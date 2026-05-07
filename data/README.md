# data/ 폴더 안내

본 폴더의 실제 데이터 파일은 `.gitignore` 에 의해 **커밋되지 않습니다**.
재현이 필요한 경우 아래 절차를 따라 로컬에서 동일한 데이터를 만들 수 있습니다.

## 폴더 구조

| 경로 | 역할 |
|---|---|
| `data/raw/` | 1차 추출본 (Open Food Facts에서 한국 제품만 필터링한 결과) |
| `data/processed/` | ETL 정제 결과 (Week 2 후반 산출물) |

## `df_raw.parquet` 가져오는 방법

### 방법 A — 1차 프로젝트(`food/`) 결과 재사용

이미 동일한 추출이 1차 프로젝트(`synthetic-data-tbt-detection`)에서 수행되어 있습니다.

```powershell
Copy-Item <1차 프로젝트 경로>\data\df_raw.parquet data\raw\df_raw.parquet
```

### 방법 B — 원본에서 다시 추출 (재현 스크립트)

원본 `food.parquet` (4 GB, Open Food Facts dump) 가 있을 때만 가능합니다.

```bash
python etl/extract_korean_products.py \
    --input  /path/to/food.parquet \
    --output data/raw/df_raw.parquet
```

추출 기준: `countries_tags` 가 `korea | kr | south-korea | en:kr | en:korea` 를 포함하는 행. (1차 프로젝트와 동일)

## 데이터 출처

- **Open Food Facts** — https://world.openfoodfacts.org/data
- 라이선스: **Open Database License (ODbL) v1.0** — 본 프로젝트는 학술 비영리 목적으로 사용하며, 데이터 자체는 본 레포에 재배포하지 않습니다.
