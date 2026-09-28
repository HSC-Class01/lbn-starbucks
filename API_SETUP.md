# OpenDART API 설정

## 1. 인증키 발급

OpenDART에서 API 인증키를 신청합니다.

- https://opendart.fss.or.kr/
- 발급받은 40자리 키를 GitHub Actions secret으로 저장합니다.

## 2. GitHub Secret

Repository → Settings → Secrets and variables → Actions → New repository secret

- Name: `DART_API_KEY`
- Secret: 발급받은 OpenDART API key

코드 파일에는 실제 키를 넣지 않습니다.

## 3. 사용 API

### 기업 고유번호
`GET /api/corpCode.xml`

### 공시검색
`GET /api/list.json`

사업보고서/반기보고서/분기보고서의 접수번호를 찾는 데 사용합니다.

### 구조화 재무제표
`GET /api/fnlttSinglAcntAll.json`

보고서 코드:

- 사업보고서: `11011`
- 반기보고서: `11012`
- 1분기보고서: `11013`
- 3분기보고서: `11014`

OpenDART 공식 개발가이드상 이 API의 사업연도는 2015년 이후부터 제공됩니다. 따라서 2010~2014는 공시검색 → `document.xml` 원문 다운로드 경로를 사용합니다.

### 공시서류 원본
`GET /api/document.xml`

접수번호(`rcept_no`)를 기준으로 원문 ZIP을 저장합니다.

## 4. 주의

- DART API key를 공개 repository에 commit하지 않습니다.
- 정정보고서가 존재할 수 있으므로 최신 접수본을 기준으로 다시 수집하도록 구성합니다.
- OpenDART 제공자료는 제출인의 책임으로 작성되며 정정 시 값이 변경될 수 있으므로 원문 확인이 필요합니다.
