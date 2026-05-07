"""
Open Food Facts 원본에서 한국 제품을 추출하는 일회성 재현 스크립트.

본 스크립트는 4GB 원본 food.parquet 파일이 필요하며, 일회성 추출용입니다.
1차 프로젝트(synthetic-data-tbt-detection)에서 이미 같은 추출을 수행했으므로
보통은 그 결과(df_raw.parquet)를 그대로 가져오면 됩니다.

추출 기준 (1차 프로젝트와 동일):
    countries_tags 가 'korea | kr | south-korea | en:kr | en:korea' 를 포함

Usage:
    python etl/extract_korean_products.py \
        --input  /path/to/food.parquet \
        --output data/raw/df_raw.parquet
"""

import argparse
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

BASIC_COLUMNS = [
    "code",              # 바코드 (PK 후보)
    "product_name",      # 제품명
    "brands",            # 브랜드
    "brands_tags",
    "categories",
    "categories_tags",
    "countries_tags",
    "allergens_tags",
    "labels_tags",
    "nutriscore_grade",
    "nutriments",        # 영양정보 (struct/dict)
]


def load_and_filter_korean_products(input_path: str, output_path: str) -> pd.DataFrame:
    print("=" * 60)
    print("한국 제품 필터링 (Open Food Facts)")
    print("=" * 60)

    print(f"\n[1] 로딩: {input_path}")
    df = pd.read_parquet(input_path, engine="pyarrow")
    print(f"    전체 데이터: {len(df):,} 행, {len(df.columns)} 컬럼")

    print("\n[2] countries_tags 기준 한국 제품 필터링")
    korean_mask = df["countries_tags"].astype(str).str.contains(
        "korea|kr|south-korea|en:kr|en:korea",
        case=False,
        na=False,
    )
    df_korean = df[korean_mask].copy()
    print(f"    한국 제품: {len(df_korean):,} 행 ({len(df_korean) / len(df) * 100:.2f}%)")

    print("\n[3] 기본 컬럼 선택")
    available = [c for c in BASIC_COLUMNS if c in df_korean.columns]
    missing = [c for c in BASIC_COLUMNS if c not in df_korean.columns]
    if missing:
        print(f"    경고: 다음 컬럼이 원본에 없습니다 → {missing}")
    df_raw = df_korean[available].copy()
    print(f"    선택된 컬럼: {len(available)}개 / 최종 {len(df_raw):,} 행")

    print("\n[4] 저장")
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df_raw.to_parquet(out, engine="pyarrow", index=False)
    print(f"    -> {out}")

    return df_raw


def main():
    parser = argparse.ArgumentParser(
        description="Extract Korean products from Open Food Facts food.parquet (one-shot)."
    )
    parser.add_argument("--input",  required=True, help="원본 food.parquet 경로 (4GB)")
    parser.add_argument("--output", required=True, help="추출 결과 저장 경로 (.parquet)")
    args = parser.parse_args()

    load_and_filter_korean_products(args.input, args.output)
    print("\n완료.")


if __name__ == "__main__":
    main()
