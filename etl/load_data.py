"""
Week 2 ETL — 1차 프로젝트의 TBT 큐레이션 2,493건을 기준으로,
df_raw.nutriments 에서 4개 영양소를 직접 재추출하여
PostgreSQL 의 products / product_nutrients 에 적재.

확정 정책 (Week 2 후반):
    - 행 선별:  tbt_analysis_result.code  ∩  df_raw.code  → 2,493건
    - 영양소:   df_raw.nutriments[*]['100g']  (1차의 0-대치된 컬럼은 사용하지 않음)
    - 결측:     NULL 유지 (4개 모두 결측이어도 product 자체는 적재)
    - 이상치:   음수 → NULL,  g/100g > 100 → NULL,  energy > 4000 kcal → NULL
    - 단위:     sodium 만 g → mg (×1000) — unit 필드 검증 결과 OFF는 g 단위로 정규화
    - product_name: ndarray of {lang, text} 구조 → main → ko → en → 첫 dict 우선
    - 카테고리: 4-tier
        1) categories_tags 자체 매핑          → category_source = 'tags'
        2) category_top 정규화 매핑           → 'top'
        3) categories 자유텍스트 키워드 매칭   → 'free'
        4) product_name 모든 dict text 매칭   → 'name'
        5) fallback                           → 'other'
"""

import os
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DF_RAW_PATH       = PROJECT_ROOT / "data" / "raw" / "df_raw.parquet"
TBT_PATH          = Path(r"C:\Users\julie\Desktop\2026-1\표준학개론\food\Fact\tbt_analysis_result.parquet")
FINAL_MERGED_PATH = Path(r"C:\Users\julie\Desktop\2026-1\표준학개론\food\data\final_merged_data.parquet")

# ──────────────────────── 영양소 정책 ────────────────────────
NUTRIENT_KEYS = {
    "energy":        ["energy-kcal", "energy"],
    "sugars":        ["sugars"],
    "saturated_fat": ["saturated-fat"],
    "sodium":        ["sodium"],
}
ENERGY_HIGH_KCAL = 4000
GRAM_HIGH        = 100

# ──────────────────────── 카테고리 정책 ────────────────────────
# Tier 1 — categories_tags 키워드 (OFF 태그 도메인)
TAG_RULES = [
    ("Dairy",     ["dairies", "fermented-milk", "cheeses", "yogurt", "yoghurt",
                   "milk", "creams"]),
    ("Beverages", ["beverages", "drinks", "plant-based-beverages", "juice",
                   "tea", "coffee", "water", "soda"]),
    ("Sweets",    ["sweet-snacks", "desserts", "confectioneries", "chocolates",
                   "candies", "ice-cream", "biscuits-and-cakes", "cocoa"]),
    ("Meals",     ["meals", "prepared-foods", "noodles", "pizza", "soups",
                   "appetizers", "frozen-foods", "sandwiches"]),
    ("Snacks",    ["snacks", "salty-snacks", "biscuits", "chips", "crisps",
                   "cereals-and-potatoes", "cereals-and-their-products",
                   "rice-cakes"]),
]

# Tier 2 — category_top 정규화 매핑
TOP_MAP = {
    "Beverages":              "Beverages",
    "Snacks":                 "Snacks",
    "Dairies":                "Dairy",
    "Meals":                  "Meals",
    "Desserts":               "Sweets",
    "Sweeteners":             "Sweets",
    "Cocoa-And-Its-Products": "Sweets",
    "Sandwiches":             "Meals",
    "Breakfast Foods":        "Snacks",
    "Instant Noodles":        "Meals",
    "Ko:과자":               "Snacks",
    "Ko:과자류":             "Snacks",
    "Ko:스낵":               "Snacks",
    "Ko:한과":               "Sweets",
    "Ko:면류":               "Meals",
    "Ko:만두":               "Meals",
    "Ko:파스타면":           "Meals",
    "Ko:Noodle-In-Spicy-Soup": "Meals",
    "Fr:Tteokbokki":         "Meals",
    "Ko:빵류":               "Snacks",
    "Ko:초코빵":             "Sweets",
    "Ko:씨리얼":             "Snacks",
    "Sliced-Brioche":        "Snacks",
    "Premium-Cereal":        "Snacks",
    "Rice-Cake":             "Snacks",
    "Fr:Barre-De-Riz-Souffle": "Snacks",
    "Fr:Cereales-Poudre":    "Snacks",
    "Almon":                 "Snacks",
    "Ko:탄산음료":           "Beverages",
    "Ko:Soymilk":            "Beverages",
    "Juice":                 "Beverages",
    "De:Ice-Kaffee":         "Beverages",
    "Non-Alcoholic-Soft-Drink": "Beverages",
    "Ko:유산균-발효유":      "Dairy",
    "Ugert":                 "Dairy",
    "Ice-Bar":               "Sweets",
    "Syrups":                "Sweets",
    "Fr:Miel-De-Rawganic":   "Sweets",
    "Ko:샌드위치":           "Meals",
}

# Tier 3·4 — 자유텍스트·product_name 키워드 매칭 (사용자 지정 우선순위)
# Latin 키워드는 \b 워드바운더리, 한국어는 substring.
PRIORITY_KEYWORDS = [
    ("Dairy",     ["milk", "yogurt", "yoghurt", "cheese", "butter", "cream",
                   "우유", "치즈", "요거트", "요구르트", "버터"]),
    ("Beverages", ["drink", "beverage", "juice", "coffee", "tea", "water",
                   "soda", "ade", "latte", "cappuccino", "americano",
                   "음료", "주스", "차", "커피", "에이드"]),
    ("Sweets",    ["chocolate", "candy", "cake", "dessert",
                   "ice-cream", "icecream", "honey", "syrup", "jelly", "pie", "tart",
                   "초콜릿", "초콜렛", "사탕", "케이크", "디저트", "아이스크림",
                   "꿀", "시럽", "젤리"]),
    ("Meals",     ["ramen", "ramyun", "noodle", "rice", "soup",
                   "dumpling", "pasta", "pizza", "lasagna", "sandwich",
                   "라면", "면", "밥", "국", "만두", "찌개", "죽"]),
    ("Snacks",    ["snack", "chip", "cookie", "biscuit", "cracker",
                   "popcorn", "cereal", "crisp",
                   "과자", "스낵", "쿠키", "크래커", "팝콘"]),
]

LATIN_RE = re.compile(r"^[a-z\-\.\s]+$")


def banner(t):
    print("\n" + "=" * 72 + "\n " + t + "\n" + "=" * 72)


def keyword_match(text):
    """우선순위 순으로 첫 매칭. 매칭 없으면 None."""
    if not isinstance(text, str) or not text.strip():
        return None
    low = text.lower()
    for cat, kws in PRIORITY_KEYWORDS:
        for kw in kws:
            if LATIN_RE.match(kw):
                if re.search(rf"\b{re.escape(kw)}\b", low):
                    return cat
            else:
                if kw in low:
                    return cat
    return None


def map_by_tags(tags):
    """Tier 1 — categories_tags 키워드. None 가능."""
    if tags is None:
        return None
    if isinstance(tags, (list, tuple, np.ndarray)):
        if len(tags) == 0:
            return None
        joined = " ".join(str(t).lower() for t in tags)
    else:
        joined = str(tags).lower()
    if not joined.strip() or joined.strip() == "missing":
        return None
    for cat, kws in TAG_RULES:
        if any(kw in joined for kw in kws):
            return cat
    return None


# ──────────────────────── product_name 처리 ────────────────────────
def extract_name(arr):
    """ndarray of {lang, text} → 단일 문자열 (main → ko → en → 첫 항목)."""
    if arr is None:
        return None
    if not isinstance(arr, (list, np.ndarray)):
        s = str(arr).strip()
        return s if s else None
    if len(arr) == 0:
        return None
    by_lang = {}
    for item in arr:
        if not isinstance(item, dict):
            continue
        lang = item.get("lang")
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            by_lang.setdefault(lang, text.strip())
    for k in ("main", "ko", "en"):
        if k in by_lang:
            return by_lang[k]
    if by_lang:
        return next(iter(by_lang.values()))
    return None


def name_blob(arr):
    """모든 dict text 를 합친 문자열 (다국어 키워드 매칭용)."""
    if not isinstance(arr, (list, np.ndarray)) or len(arr) == 0:
        return ""
    parts = []
    for item in arr:
        if isinstance(item, dict):
            t = item.get("text")
            if isinstance(t, str):
                parts.append(t)
    return " ".join(parts)


# ──────────────────────── nutriments 처리 ────────────────────────
def get_100g(nutriments, name):
    if nutriments is None:
        return None
    if isinstance(nutriments, (list, tuple, np.ndarray)):
        for item in nutriments:
            if isinstance(item, dict) and item.get("name") == name:
                return item.get("100g")
    return None


def extract_nutrient(nutriments, candidates):
    for k in candidates:
        v = get_100g(nutriments, k)
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if np.isnan(f):
            continue
        return f, k
    return None, None


def normalize(code, raw):
    if raw is None:
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    if np.isnan(v) or v < 0:
        return None
    if code == "energy":
        return None if v > ENERGY_HIGH_KCAL else v
    if v > GRAM_HIGH:
        return None
    if code == "sodium":
        return v * 1000.0
    return v


# ──────────────────────── 4-tier 카테고리 ────────────────────────
def map_4tier(row, code_to_top):
    """반환: (category, source)."""
    # 1) tags
    cat = map_by_tags(row.get("categories_tags"))
    if cat is not None:
        return cat, "tags"
    # 2) category_top
    raw_top = code_to_top.get(row["code"])
    if raw_top and raw_top != "Unknown":
        mapped = TOP_MAP.get(raw_top)
        if mapped is not None:
            return mapped, "top"
    # 3) categories 자유텍스트
    free = row.get("categories")
    cat = keyword_match(free) if isinstance(free, str) else None
    if cat is not None:
        return cat, "free"
    # 4) product_name (모든 dict text 합친 문자열)
    cat = keyword_match(name_blob(row.get("product_name")))
    if cat is not None:
        return cat, "name"
    return "Other", "other"


# ──────────────────────── 메인 ────────────────────────
def main():
    banner("1. 데이터 로딩 + inner join")
    tbt = pd.read_parquet(TBT_PATH, engine="pyarrow")
    df_raw = pd.read_parquet(DF_RAW_PATH, engine="pyarrow")
    print(f"  tbt rows={len(tbt):,} / df_raw rows={len(df_raw):,}")

    tbt["code"] = tbt["code"].astype(str).str.strip()
    df_raw["code"] = df_raw["code"].astype(str).str.strip()
    code_to_top = dict(zip(tbt["code"], tbt["category_top"]))
    codes = set(tbt["code"])

    df = df_raw[df_raw["code"].isin(codes)].drop_duplicates("code").copy().reset_index(drop=True)
    print(f"  inner join: {len(df):,} 행")

    banner("2. product_name 추출 검증 (사전 점검)")
    arrs = df["product_name"]
    n_total = len(df)
    n_arr = sum(1 for a in arrs if isinstance(a, (list, np.ndarray)))
    n_empty = sum(1 for a in arrs if isinstance(a, (list, np.ndarray)) and len(a) == 0)
    has_main = has_ko = has_en = 0
    for a in arrs:
        if not isinstance(a, (list, np.ndarray)):
            continue
        langs = {it.get("lang") for it in a if isinstance(it, dict)}
        if "main" in langs: has_main += 1
        if "ko"   in langs: has_ko   += 1
        if "en"   in langs: has_en   += 1
    print(f"  ndarray 형태  : {n_arr}/{n_total}")
    print(f"  빈 array     : {n_empty}")
    print(f"  main 키 존재 : {has_main} ({has_main/n_total*100:.1f}%)")
    print(f"  ko 키 존재   : {has_ko}")
    print(f"  en 키 존재   : {has_en}")

    df["__name"] = df["product_name"].apply(extract_name)
    n_extracted = df["__name"].notna().sum()
    n_no_name = n_total - n_extracted
    print(f"  추출 성공    : {n_extracted} ({n_extracted/n_total*100:.1f}%)")
    print(f"  (no name)    : {n_no_name} ({n_no_name/n_total*100:.1f}%)")

    # 언어 분포
    HANGUL = re.compile(r"[가-힣]")
    LATIN  = re.compile(r"[A-Za-z]")
    def lang_class(s):
        if not isinstance(s, str): return "none"
        h = bool(HANGUL.search(s)); e = bool(LATIN.search(s))
        if h and e: return "mixed"
        if h: return "korean"
        if e: return "english"
        return "other"
    lang_dist = df["__name"].apply(lang_class).value_counts()
    print("  추출 이름 언어 분포:")
    for k, c in lang_dist.items():
        print(f"    {k:8s} {c:5d} ({c/n_total*100:5.1f}%)")

    banner("3. 영양소 추출 + 단위변환 + 이상치")
    counters = {n: {"extracted": 0, "outlier_null": 0, "final": 0} for n in NUTRIENT_KEYS}
    long_rows = []
    for code, nutriments in zip(df["code"], df["nutriments"]):
        for canonical, candidates in NUTRIENT_KEYS.items():
            raw, _ = extract_nutrient(nutriments, candidates)
            if raw is None:
                continue
            counters[canonical]["extracted"] += 1
            final = normalize(canonical, raw)
            if final is None:
                counters[canonical]["outlier_null"] += 1
            else:
                counters[canonical]["final"] += 1
                long_rows.append((code, canonical, final))
    for n, c in counters.items():
        null_pct = (n_total - c["final"]) / n_total * 100
        print(f"  {n:14s} extracted={c['extracted']:5d}  outlier→NULL={c['outlier_null']:3d}  적재={c['final']:5d}  ({null_pct:5.1f}% NULL)")

    banner("4. 4-tier 카테고리 매핑")
    df[["__cat", "__cat_src"]] = df.apply(
        lambda r: pd.Series(map_4tier(r, code_to_top)), axis=1
    )
    cat_counter = Counter(df["__cat"])
    src_counter = Counter(df["__cat_src"])
    print("  카테고리 분포:")
    for k in ["Snacks", "Beverages", "Dairy", "Meals", "Sweets", "Other"]:
        print(f"    {k:12s} {cat_counter.get(k, 0):5d}")
    print("  category_source 분포:")
    for k in ["tags", "top", "free", "name", "other"]:
        n = src_counter.get(k, 0)
        print(f"    {k:6s} {n:5d}  ({n/n_total*100:5.1f}%)")

    # tier별 누적 (현재 tier 까지 사용했을 때 매핑된 행 수)
    cum_tags  = (df["__cat_src"] == "tags").sum()
    cum_top   = cum_tags + (df["__cat_src"] == "top").sum()
    cum_free  = cum_top + (df["__cat_src"] == "free").sum()
    cum_name  = cum_free + (df["__cat_src"] == "name").sum()
    print("  tier 누적 매핑 효과:")
    print(f"    tags 만               : {cum_tags:5d}  ({cum_tags/n_total*100:5.1f}%)")
    print(f"    + category_top        : {cum_top:5d}  ({cum_top/n_total*100:5.1f}%)")
    print(f"    + categories 자유텍스트: {cum_free:5d}  ({cum_free/n_total*100:5.1f}%)")
    print(f"    + product_name        : {cum_name:5d}  ({cum_name/n_total*100:5.1f}%)")

    banner("5. PostgreSQL 적재")
    conn = psycopg2.connect(
        host=os.environ["PG_HOST"],
        port=int(os.environ.get("PG_PORT", 5432)),
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
    )
    conn.autocommit = False
    cur = conn.cursor()

    # 5-0) schema migration: category_source 컬럼 보장
    cur.execute("""
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS category_source VARCHAR(10) NOT NULL DEFAULT 'other'
    """)
    cur.execute("""
        COMMENT ON COLUMN products.category_source IS
        '카테고리 매핑 출처 (tags / top / free / name / other)'
    """)

    cur.execute("SELECT category_name, category_id FROM categories")
    cat_id_map = dict(cur.fetchall())
    unknown = set(cat_counter) - set(cat_id_map)
    if unknown:
        raise RuntimeError(f"매핑된 카테고리가 categories 테이블에 없음: {unknown}")

    cur.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE")
    print("  TRUNCATE products RESTART IDENTITY CASCADE 실행")

    products_payload = []
    for _, r in df.iterrows():
        nm = r["__name"] if isinstance(r["__name"], str) and r["__name"].strip() else "(no name)"
        if len(nm) > 255: nm = nm[:255]
        # brand 처리: 빈/None은 NULL
        brand_val = r["brands"]
        if isinstance(brand_val, str) and brand_val.strip():
            brand = brand_val[:100]
        else:
            brand = None
        products_payload.append((
            r["code"],
            nm,
            brand,
            cat_id_map[r["__cat"]],
            r["__cat_src"],
        ))
    returned = execute_values(
        cur,
        "INSERT INTO products (product_code, product_name, brand, category_id, category_source) "
        "VALUES %s RETURNING product_id, product_code",
        products_payload, page_size=500, fetch=True,
    )
    code_to_id = {code: pid for pid, code in returned}
    print(f"  products 적재: {len(products_payload):,}")

    pn_payload = [(code_to_id[c], nc, v) for c, nc, v in long_rows if c in code_to_id]
    execute_values(
        cur,
        "INSERT INTO product_nutrients (product_id, nutrient_code, amount_per_100g) VALUES %s",
        pn_payload, page_size=1000,
    )
    print(f"  product_nutrients 적재: {len(pn_payload):,}")
    conn.commit()

    banner("6. DB 적재 검증")
    cur.execute("SELECT COUNT(*) FROM products")
    print(f"  products: {cur.fetchone()[0]}")
    cur.execute("SELECT category_source, COUNT(*) FROM products GROUP BY 1 ORDER BY 2 DESC")
    print("  category_source 분포 (DB 측):")
    for s, n in cur.fetchall():
        print(f"    {s:6s} {n:5d}")
    cur.execute("""
        SELECT c.category_name, COUNT(*) FROM products p
        JOIN categories c ON c.category_id = p.category_id
        GROUP BY c.category_name ORDER BY COUNT(*) DESC
    """)
    print("  category 분포 (DB 측):")
    for cat, n in cur.fetchall():
        print(f"    {cat:12s} {n:5d}")
    cur.execute("""
        SELECT nutrient_code, COUNT(*),
               ROUND(MIN(amount_per_100g)::numeric, 2),
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount_per_100g))::numeric, 2),
               ROUND(MAX(amount_per_100g)::numeric, 2)
        FROM product_nutrients GROUP BY 1 ORDER BY 1
    """)
    print("  nutrient 통계 (n / min / median / max):")
    for row in cur.fetchall():
        print(f"    {row[0]:14s} {row[1]:5d}  min={row[2]:>10}  med={row[3]:>10}  max={row[4]:>10}")

    banner("7. 분류된 그룹 vs Other 그룹 영양소 분포 (보고서 framing)")
    cur.execute("""
        SELECT c.category_name = 'Other' AS is_other,
               pn.nutrient_code,
               COUNT(*) AS n,
               ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pn.amount_per_100g))::numeric, 2) AS median,
               ROUND(AVG(pn.amount_per_100g)::numeric, 2) AS mean
        FROM products p
        JOIN categories c ON c.category_id = p.category_id
        JOIN product_nutrients pn ON pn.product_id = p.product_id
        GROUP BY 1, 2
        ORDER BY 2, 1
    """)
    rows = cur.fetchall()
    print("  is_other | nutrient | n | median | mean")
    for r in rows:
        label = "Other" if r[0] else "분류"
        print(f"    {label:5s}  {r[1]:14s}  n={r[2]:5d}  med={r[3]:>10}  mean={r[4]:>10}")

    cur.close()
    conn.close()

    banner("8. 1차 0-대치 vs 본 NULL 비교 (재계산)")
    if FINAL_MERGED_PATH.exists():
        fm = pd.read_parquet(FINAL_MERGED_PATH, engine="pyarrow")
        fm["code"] = fm["code"].astype(str).str.strip()
        fm = fm.set_index("code")
        new_vals = {}
        for code, nut, v in long_rows:
            new_vals.setdefault(code, {})[nut] = v
        col_map = {
            "energy":        "energy_100g",
            "sugars":        "sugars_100g",
            "saturated_fat": "saturated_fat_100g",  # 1차에 없음 (별도 표시)
            "sodium":        "sodium_100g",
        }
        out = []
        codes_in_fm = list(fm.index)
        for canonical, fmc in col_map.items():
            if fmc not in fm.columns:
                out.append({"nutrient": canonical, "1차_0건수": "N/A",
                            "본_NULL건수": (n_total - counters[canonical]["final"]),
                            "phantom_0": "N/A"})
                continue
            n_zero = int((fm[fmc] == 0).sum())
            n_null = sum(1 for c in codes_in_fm if new_vals.get(c, {}).get(canonical) is None)
            phantom = sum(1 for c in codes_in_fm
                          if (fm.at[c, fmc] == 0)
                          and (new_vals.get(c, {}).get(canonical) is None))
            out.append({"nutrient": canonical, "1차_0건수": n_zero,
                        "본_NULL건수": n_null, "phantom_0": phantom})
        comp = pd.DataFrame(out)
        print(comp.to_string(index=False))
    else:
        print("  final_merged_data.parquet 없음 → 비교 건너뜀")

    print("\n끝.")


if __name__ == "__main__":
    main()
