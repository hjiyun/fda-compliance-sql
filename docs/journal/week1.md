# Week 1: DB 설계 및 환경 구축

> **기간**: 2026.04.30 (1일 완료)
> **상태**: ✅ 완료

---

## 목표

- PostgreSQL 18 + Docker 환경 구축
- 프로젝트 폴더 구조 셋업
- Claude Code 연결
- 테이블 6개 + 인덱스 2개 생성
- 시드 데이터 입력 (카테고리 6개, FDA 영양소 4종)
- VS Code PostgreSQL 확장으로 DB 시각화

---

## 주요 의사결정

### 1. Windows 네이티브 PostgreSQL → Docker로 전환

이력서에 Docker 경험 추가, 환경 재현성 확보, 데이터 엔지니어 표준 도구라는 세 가지 이유로 결정. `docker run` 한 줄로 PG 18 클린 환경을 확보할 수 있어 다른 머신·서버로의 이식이 단순해진다.

### 2. `nutrient_name_ko` → `nutrient_name_kr` 컬럼명 통일

학술적으로는 `_ko` (ISO 639 언어 코드)가 정확하지만, ERD·연구 제안서·보고서가 모두 `_kr` (ISO 3166 국가 코드) 표기로 작성되어 있어 **문서 간 일관성**을 학술 정확성보다 우선했다. 이 결정은 본 프로젝트에 한정.

---

## 트러블슈팅

### 1. Docker Desktop 권한 에러

- **증상**: `For security reasons C:\ProgramData\DockerDesktop must be owned...`
- **원인**: 이전 Docker 설치 잔여 폴더의 소유권 불일치
- **해결**: 해당 폴더 삭제 후 Docker Desktop 관리자 권한으로 재실행
- **배운 점**: Windows에서 시스템 디렉토리는 단순 재설치로 정리되지 않음. 잔여물을 직접 제거해야 한다.

### 2. PostgreSQL 18 컨테이너 즉시 종료 (Exited 1)

- **증상**: `docker logs`에 `PostgreSQL data in /var/lib/postgresql/data (unused mount/volume)` 출력 후 컨테이너 종료
- **원인**: PostgreSQL 18부터 데이터 디렉토리가 버전별로 분리됨 (`/var/lib/postgresql/<ver>/`)
- **해결**: 볼륨 마운트를 `-v fda_data:/var/lib/postgresql/data` → `-v fda_data:/var/lib/postgresql` 로 변경
- **배운 점**: 메이저 버전 업이 디렉토리 레이아웃을 바꿀 수 있다. 공식 이미지의 변경 사항을 사전 확인.

### 3. 시드 작성 단계에서 컬럼명 불일치 발견

- **증상**: `03_seed_nutrient_limits.sql` INSERT 컬럼명이 `01_schema.sql`의 정의와 불일치 (`_ko` vs `_kr`, `threshold_per_100g` vs `high_threshold_100g`, `is_public_concern` 누락)
- **원인**: ERD/보고서가 정한 컬럼명이 초기 DDL에 반영되지 않음
- **해결**: `01_schema.sql` 수정 후 `nutrient_limits` 테이블만 DROP/CREATE 부분 재적용 (`product_nutrients` FK 복구 포함)
- **배운 점**: **ERD → DDL → 시드** 라인의 컬럼명 일관성 점검은 시드 작성 전에 수행.

### 4. GitHub push가 이메일 프라이버시 정책에 차단

- **증상**: `remote: error: GH007: Your push would publish a private email address`
- **원인**: 글로벌 git config의 commit author email이 GitHub 계정에서 비공개 처리된 주소
- **해결**: 이 레포 한정으로 `git config --local user.email` 을 공개용 이메일로 변경 후 amend + push (글로벌 config 보존)
- **배운 점**: 공개 레포와 사적 레포에서 author email을 분리하려면 repo-local config가 안전한 도구.

### 5. README/CLAUDE.md 비밀번호 평문 노출

- **증상**: 공개 push 직전 점검에서 DB 비밀번호 평문(`fda1234`) 2곳 발견
- **원인**: 로컬 개발 편의를 위해 문서에 그대로 기록
- **해결**: 해당 위치를 `<your-password>` / `<local-dev-password>` 로 마스킹, README에 사용자 변경 안내 추가
- **배운 점**: 공개 직전 자격증명 평문 검색(`grep -ri 'password\|token\|key'`)을 체크리스트화한다.

### 6. GitHub commit author 매핑 충돌

- **증상**: push 후 commit 페이지의 author 아바타가 의도한 계정과 다른 계정으로 표시
- **원인**: 사용한 author email이 다른 GitHub 계정에 verified 상태로 등록되어 있어 GitHub UI가 그 계정으로 매핑
- **해결**: 충돌 계정 정리 + 의도한 계정의 verified email 목록에 해당 주소 추가
- **배운 점**: GitHub은 commit metadata가 아닌 **verified email** 기준으로 commit-계정 매핑을 한다.

---

## 학습 노트

### Docker

- 자주 쓰는 명령: `docker run`, `ps`, `exec`, `logs`, `volume ls / inspect`
- 컨테이너 내부 작업: `docker exec -it <container> bash` 또는 `docker exec <container> psql ...`
- 파일 전달: `docker cp <local> <container>:/path` 로 SQL/스크립트 주입

### PostgreSQL psql 메타 명령

- `\dt` — 테이블 목록
- `\d <table>` — 테이블 상세 구조 (컬럼·인덱스·FK)
- `\di` — 인덱스 목록
- `\l` — 데이터베이스 목록
- `\q` — 종료

### 데이터 모델링 원칙

- **롱 포맷 vs 와이드 포맷**: 영양소를 컬럼이 아닌 행(`product_nutrients`)으로 저장 → 영양소 추가/삭제 시 스키마 변경 불필요
- **규정과 데이터의 분리**: `nutrient_limits` (FDA 규정 메타데이터) vs `product_nutrients` (실측치) — 규정 개정이 데이터 마이그레이션을 유발하지 않음
- **VIEW 활용 예정**: 적합성 진단 로직은 `v_compliance_results` / `v_risk_score` 로 캡슐화하여 룰 변경의 영향 최소화
- **`DROP TABLE IF EXISTS ... CASCADE`**: 스키마 재실행 안전성 확보. 단, FK 종속 객체가 함께 사라지므로 부분 재적용 시 FK 복구 단계 필요.

---

## 다음 주차 계획 (Week 2)

- Open Food Facts 한국 식품 2,493건 ETL 파이프라인 구축
- 실제 카테고리 분포 확인 후 `categories` 시드 보강
- Python `pandas` + `psycopg2` 로 `products` / `product_nutrients` 적재
- 적재 후 데이터 품질 검증 (NULL 비율, 영양소 단위 정규화)
