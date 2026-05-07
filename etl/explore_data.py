"""
Week 2 데이터 탐색 스크립트.

대상: data/raw/df_raw.parquet
목적: ETL 정책 결정에 필요한 데이터 형태·결측·이상치 파악.
가장 핵심: nutriments 컬럼 구조 (어떻게 영양소를 추출할지).
"""

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# Windows 기본 cp949 콘솔에서 한글·기호 출력 깨짐 방지
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "df_raw.parquet"

# 본 프로젝트의 4개 영양소에 대해, 후보 키 (우선순위 순)
TARGET_KEYS = {
    "energy":        ["energy-kcal_100g", "energy_100g", "energy-kcal", "energy"],
    "sugars":        ["sugars_100g", "sugars"],
    "saturated_fat": ["saturated-fat_100g", "saturated-fat"],
    "sodium":        ["sodium_100g", "sodium"],
}

# 시드 카테고리 6개 (Snacks/Beverages/Dairy/Meals/Sweets/Other) 후보 키워드
SEED_CATEGORY_KEYWORDS = {
    "Beverages": ["beverages", "drinks", "water", "juice", "soda", "tea", "coffee"],
    "Dairy":     ["dairy", "milk", "yogurt", "cheese", "cream"],
    "Sweets":    ["sweets", "chocolate", "candy", "confectionery", "desserts", "ice-cream"],
    "Snacks":    ["snacks", "chips", "crackers", "biscuits", "cookies", "cereals"],
    "Meals":     ["meals", "prepared", "ready", "noodles", "pizza", "soup"],
}


def banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(f" {title}")
    print("=" * 72)


def get_from_nutriments(value, key):
    """
    nutriments 에서 영양소 100g 당 값 추출.
    실제 구조: ndarray([{name, '100g', serving, unit, value, prepared_*}, ...])
    'name' 매칭 후 '100g' 필드를 반환 (FDA 임계값이 100g 기준이므로).
    """
    if value is None:
        return None
    if isinstance(value, dict):
        # 일부 행이 dict 한 개로 들어올 가능성에 대비
        if value.get("name") == key:
            return value.get("100g")
        return value.get(key)
    if isinstance(value, (list, tuple, np.ndarray)):
        try:
            for item in value:
                if isinstance(item, (list, tuple)) and len(item) == 2 and item[0] == key:
                    return item[1]
                if isinstance(item, dict) and item.get("name") == key:
                    return item.get("100g")
        except Exception:
            return None
    return None


def collect_keys(series: pd.Series) -> Counter:
    keys = Counter()
    for v in series:
        if isinstance(v, dict):
            keys.update(v.keys())
        elif isinstance(v, (list, tuple, np.ndarray)):
            try:
                for item in v:
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        keys.update([item[0]])
                    elif isinstance(item, dict) and "name" in item:
                        keys.update([item["name"]])
            except Exception:
                pass
    return keys


def main():
    banner("1. 기본 정보")
    df = pd.read_parquet(DATA_PATH, engine="pyarrow")
    print(f"  shape           : {df.shape}")
    print(f"  메모리 (deep)   : {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    print("\n  dtypes:")
    for col, dt in df.dtypes.items():
        print(f"    {col:20s} {dt}")

    banner("2. nutriments 컬럼 구조")
    if "nutriments" not in df.columns:
        print("[!] nutriments 컬럼 없음 → ETL 불가")
        return

    nutri = df["nutriments"]
    sample = nutri.iloc[0]
    print(f"  자료형 (샘플 1행)  : {type(sample).__name__}")
    if isinstance(sample, dict):
        keys = list(sample.keys())
        print(f"  샘플 키 개수       : {len(keys)}")
        print(f"  샘플 처음 15개 키  : {keys[:15]}")
    elif isinstance(sample, (list, tuple, np.ndarray)):
        print(f"  샘플 원소 개수     : {len(sample)}")
        if len(sample):
            print(f"  샘플 첫 원소       : {sample[0]} (type={type(sample[0]).__name__})")
    else:
        print(f"  str(sample)[:200]  : {str(sample)[:200]}")

    banner("2-1. 전체 행에서 등장하는 nutriments 키 (Top 30)")
    all_keys = collect_keys(nutri)
    print(f"  unique 키 수: {len(all_keys)}")
    for k, c in all_keys.most_common(30):
        print(f"    {c:5d}  {k}")

    banner("2-2. 본 프로젝트 4개 영양소 키 매칭")
    chosen = {}
    for canonical, candidates in TARGET_KEYS.items():
        chosen[canonical] = (None, 0)
        for cand in candidates:
            cnt = all_keys.get(cand, 0)
            if cnt > 0:
                chosen[canonical] = (cand, cnt)
                break
        key, cnt = chosen[canonical]
        if key is None:
            print(f"  {canonical:14s}  [--] 매칭 키 없음 (후보: {candidates})")
        else:
            print(f"  {canonical:14s}  [OK] key='{key}'  등장 {cnt:,}회")

    banner("2-3. 4개 영양소 결측·통계")
    rows = []
    extracted = {}
    for canonical, (key, _) in chosen.items():
        if key is None:
            rows.append({"nutrient": canonical, "key": "-", "have": 0, "missing_pct": 100.0,
                         "min": "-", "median": "-", "p95": "-", "max": "-"})
            extracted[canonical] = (key, [])
            continue
        vals = []
        for v in nutri:
            x = get_from_nutriments(v, key)
            if x is None:
                continue
            try:
                xf = float(x)
            except (TypeError, ValueError):
                continue
            if np.isnan(xf):
                continue
            vals.append(xf)
        n_total = len(df)
        n_have = len(vals)
        rows.append({
            "nutrient":    canonical,
            "key":         key,
            "have":        n_have,
            "missing_pct": round((n_total - n_have) / n_total * 100, 1),
            "min":         f"{min(vals):.4g}"           if vals else "-",
            "median":      f"{float(np.median(vals)):.4g}" if vals else "-",
            "p95":         f"{float(np.percentile(vals, 95)):.4g}" if vals else "-",
            "max":         f"{max(vals):.4g}"           if vals else "-",
        })
        extracted[canonical] = (key, vals)
    print(pd.DataFrame(rows).to_string(index=False))

    banner("2-4. 단위 진단 (관측 분포 → 단위 추론)")
    print("  FDA 100g 임계값  :  sodium=460 mg | sugars=10 g | saturated_fat=4 g | energy=400 kcal")
    print("  → median이 임계값과 자릿수가 맞으면 그 단위, 아니면 변환 필요\n")
    inferences = {
        "sodium":        "값이 0~수 범위면 g 단위(=g of sodium per 100g) → ×1000하여 mg로 변환 필요",
        "sugars":        "g 단위가 일반적 (0~100)",
        "saturated_fat": "g 단위가 일반적 (0~100)",
        "energy":        "energy-kcal_100g면 kcal, energy_100g면 kJ (×0.239 → kcal)",
    }
    for canonical, msg in inferences.items():
        key, vals = extracted[canonical]
        med = float(np.median(vals)) if vals else float("nan")
        print(f"  {canonical:14s} key={key!s:25s} median={med:.4g}    {msg}")

    banner("3. 카테고리 분석")
    if "categories_tags" in df.columns:
        ctags = Counter()
        for v in df["categories_tags"]:
            if v is None:
                continue
            if isinstance(v, (list, tuple, np.ndarray)):
                ctags.update(str(t) for t in v)
            elif isinstance(v, str):
                # 콤마 구분 문자열인 경우
                ctags.update(t.strip() for t in v.split(",") if t.strip())
        print(f"  unique tag 수: {len(ctags)}")
        print("  Top 30:")
        for t, c in ctags.most_common(30):
            print(f"    {c:5d}  {t}")

        banner("3-1. 시드 카테고리 6개와의 매핑 가능성")
        # 각 행을 시드 카테고리로 첫 번째로 매핑되는 것 기준 1회만 카운트
        rows = df["categories_tags"]
        mapped = Counter()
        for v in rows:
            if v is None:
                mapped["<no_tags>"] += 1
                continue
            if isinstance(v, (list, tuple, np.ndarray)):
                tags = [str(t).lower() for t in v]
            elif isinstance(v, str):
                tags = [t.strip().lower() for t in v.split(",") if t.strip()]
            else:
                tags = []
            joined = " ".join(tags)
            assigned = None
            for cat, kws in SEED_CATEGORY_KEYWORDS.items():
                if any(kw in joined for kw in kws):
                    assigned = cat
                    break
            mapped[assigned or "Other"] += 1
        print("  키워드 기반 1차 매핑 결과 (보강 전 추정치):")
        for cat in ["Snacks", "Beverages", "Dairy", "Meals", "Sweets", "Other", "<no_tags>"]:
            print(f"    {cat:12s}  {mapped.get(cat, 0):5d}")

    banner("4. 기타 결측·분포")
    for col in ["product_name", "brands", "code", "nutriscore_grade"]:
        if col not in df.columns:
            continue
        miss = df[col].isna().sum()
        print(f"  {col:18s} 결측 {miss:5d} ({miss / len(df) * 100:5.1f}%)")
    if "nutriscore_grade" in df.columns:
        print("\n  nutriscore_grade 분포:")
        for k, c in df["nutriscore_grade"].value_counts(dropna=False).items():
            print(f"    {str(k):8s}  {c}")
    if "allergens_tags" in df.columns:
        atags = Counter()
        for v in df["allergens_tags"]:
            if v is None:
                continue
            if isinstance(v, (list, tuple, np.ndarray)):
                atags.update(str(t) for t in v)
        print("\n  allergens_tags Top 15:")
        for t, c in atags.most_common(15):
            print(f"    {c:5d}  {t}")

    banner("5. 이상치 탐지 (4개 영양소)")
    sanity_high = {
        "sodium":        100,    # g 단위면 매우 큼
        "sugars":        100,
        "saturated_fat": 100,
        "energy":        4000,
    }
    for canonical, (key, vals) in extracted.items():
        if key is None or not vals:
            continue
        arr = np.asarray(vals)
        neg = int((arr < 0).sum())
        too_high = int((arr > sanity_high[canonical]).sum())
        print(f"  {canonical:14s} (n={len(arr):,})  음수: {neg}건  / >{sanity_high[canonical]}: {too_high}건")

    banner("끝")
    print("  전체 행수:", len(df))
    print("  최대 product_nutrients 적재 행수 (2,493 × 4 = 9,972 가정):", len(df) * 4)


if __name__ == "__main__":
    main()
