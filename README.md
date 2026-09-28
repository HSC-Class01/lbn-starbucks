# ☕ Starbucks Korea DART Financial Agent

[![Dashboard](https://img.shields.io/badge/%F0%9F%94%97%20%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C-%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-111111?style=for-the-badge)](https://HSC-Class01.github.io/lbn-starbucks/)

> DART(OpenDART) 기반 스타벅스 코리아(주식회사 에스씨케이컴퍼니) 재무 데이터 수집·분석 Agent

## Dashboard

**🔗 대시보드 바로가기:** https://HSC-Class01.github.io/lbn-starbucks/

GitHub Pages에서 정적 Dashboard를 제공합니다. 상단에는 매출·영업이익·영업이익률·ROE/ROA 등 추세 Figure를, 하단에는 Annual / Half-year / Quarterly 3개 테이블을 배치합니다.

## Data scope

- Company: 주식회사 에스씨케이컴퍼니 (Starbucks Korea)
- Reports: 사업보고서(11011), 반기보고서(11012), 1분기보고서(11013), 3분기보고서(11014)
- Target period: 2010 onward
- 2010–2014: DART filing search + original disclosure document XML fallback
- 2015 onward: OpenDART `fnlttSinglAcntAll` structured financial statements
- Update: every month on the 1st, Asia/Seoul 09:10 via GitHub Actions

OpenDART's structured financial-statement API documents 2015 onward as its available period, so the older-period fallback is intentional. See `docs/API_SETUP.md`.

## Key metrics

The extraction/analysis follows the supplied financial-ratio guide: revenue, gross profit, operating profit, pretax income, net income, EBITDA, assets, liabilities, equity, CFO, CFI, CFF, CAPEX, FCF, interest-bearing debt/cash where available, and ratios including revenue growth, gross/operating/net margins, current/quick ratio, debt ratio, interest coverage, net debt/EBITDA, asset turnover, DSO/DIO/DPO/CCC, CFO/net income, ROA, ROE, ROIC and valuation fields when market data exists. Missing/non-applicable metrics remain blank rather than being fabricated.

## Domestic peer firms

| Peer | Company / operator | Notes |
|---|---|---|
| 투썸플레이스 | 투썸플레이스(주) | 프리미엄 디저트·커피 카페 |
| 메가MGC커피 | (주)앤하우스 | 저가 커피 프랜차이즈 |
| 컴포즈커피 | 컴포즈커피 운영사 | 저가 커피 프랜차이즈 |
| 공차 | 공차코리아(주) | 티·음료 중심 카페 |
| 커피빈 | (주)커피빈코리아 | 커피 전문점 |

Peers are presented as a reference set, not as an investment ranking.

## API setup

1. OpenDART에서 인증키를 발급합니다.
2. GitHub repository `HSC-Class01/lbn-starbucks` → **Settings → Secrets and variables → Actions → New repository secret**
3. Name: `DART_API_KEY`
4. Value: 발급받은 40자리 OpenDART 인증키
5. Workflow를 실행하면 `DART_API_KEY`를 GitHub Actions secret으로 읽습니다. API key는 코드나 README에 직접 넣지 마세요.

## Local run

```bash
pip install -r requirements.txt
export DART_API_KEY="YOUR_KEY"
python src/agent.py --start-year 2010 --end-year auto
```

생성 파일:

- `data/raw/` — DART 원문 ZIP/XML 및 filing metadata
- `data/financials.csv` — 표준화 재무 데이터
- `data/ratios.csv` — 계산 재무비율
- `public/data.json` — Dashboard용 데이터

## GitHub Pages deployment

Repository Settings → Pages → **Build and deployment: GitHub Actions**로 설정합니다. 저장소의 `github/workflows/pages.yml`을 `.github/workflows/pages.yml`로 이동/복사하면 Pages 배포가 활성화됩니다. `github/workflows/update.yml`은 매월 1일 수집·분석 후 결과를 commit/push합니다.

> 이 ZIP은 업로드 방해가 되는 `.DS_Store`, `Thumbs.db`, `__MACOSX` 등 불필요한 숨김 파일을 포함하지 않습니다. GitHub Actions가 실제로 인식하려면 최종 GitHub 저장소에서는 workflow 파일이 반드시 `.github/workflows/` 아래에 있어야 합니다.

## About 링크

GitHub repository의 **About → Website**에 다음 주소를 넣어주세요:

`https://HSC-Class01.github.io/lbn-starbucks/`

GitHub repository Settings/About UI는 저장소 소유자 권한으로 설정해야 하므로 ZIP만으로는 About 영역을 자동 변경할 수 없습니다.

## Data source

Financial data source: Financial Supervisory Service OpenDART / DART. Always cross-check important figures against the original filing because the regulator notes that submitted disclosure data are the responsibility of the filer and can change after corrections.
