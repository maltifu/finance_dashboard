# 자산 장부

휴대폰에서 보기 좋은 개인 자산 대시보드입니다. 계좌와 종목을 직접 입력해 분류별로 보고, 과거 시세로 "그때 이렇게 투자했다면"을 계산하고, 그 기간의 연평균 수익률로 미래 자산을 예측합니다.

빌드가 끝난 `index.html` 하나로 동작하고, 서버나 API 키가 필요 없습니다.

## 화면 구성

| 탭 | 내용 |
|---|---|
| 요약 | 총자산, 지난 기록 대비 변화(상승 빨강 ▲ / 하락 파랑 ▼), 총자산 추이, 기관별 합계, 큰 자산 5개 |
| 분류 | 현금·예금, 국내주식, 해외주식, 채권, 금·원자재, 가상자산 등 분류별 금액과 비중 |
| 자산 입력 | 직접 입력, 수정·삭제, 예금 금리 가정, 백업 파일 저장·복원 |
| 수익 예측 | ① 분류별로 지수·종목 담기 → ② 비율 정하기 → ③ 과거에 투자했다면(백테스트) → ④ 목돈 투자 미래 예측 → ⑤ 적립식 투자(과거·미래) |

수익 예측에서 고를 수 있는 것:
- 분류 지수: KOSPI, S&P 500(배당 포함), NASDAQ-100, 미국 종합채권, 금, 비트코인, 예금 금리
- 종목 약 150개: 국내·미국 대형주, 국내·해외 ETF, 채권 ETF, 원자재 선물(브렌트유, WTI, 은, 구리, 옥수수, 밀, 대두 등)과 원자재 ETF

## GitHub Pages로 휴대폰에서 보기

1. GitHub에서 새 저장소를 만들고 이 폴더의 파일을 모두 올립니다.
   - git이 없으면 저장소 화면의 **Add file → Upload files**에 폴더 안 파일을 끌어다 놓으면 됩니다. `.github` 폴더도 함께 올려야 자동 갱신이 동작해요.
   - git이 있으면:
     ```bash
     git init
     git add .
     git commit -m "자산 장부"
     git branch -M main
     git remote add origin https://github.com/<내 아이디>/asset-ledger.git
     git push -u origin main
     ```
2. 저장소 **Settings → Pages**에서 Source를 **Deploy from a branch**, Branch를 `main` / `(root)`로 정하고 저장합니다.
3. 1~2분 뒤 `https://<내 아이디>.github.io/asset-ledger/` 주소가 생깁니다. 휴대폰 브라우저에서 열고 **홈 화면에 추가**하면 앱처럼 쓸 수 있어요.

## 내 자산 데이터는 어디에 저장되나요

- GitHub Pages에서 열면 입력한 자산은 **그 브라우저의 저장소(localStorage)에만** 저장됩니다. GitHub 저장소나 다른 서버로는 전송되지 않아요.
- 그래서 휴대폰과 PC의 데이터가 따로입니다. 옮기려면 **자산 입력 → 백업 파일 저장**으로 받은 파일을 다른 기기에서 **백업에서 복원**하세요.
- 브라우저 사이트 데이터를 지우면 입력한 자산도 지워집니다. 가끔 백업 파일을 받아 두세요.
- **스크린샷으로 가져오기**(Claude가 캡처 화면을 읽는 기능)는 claude.ai 안에서 열었을 때만 동작합니다. GitHub Pages에서는 직접 입력을 이용하세요.

## 시세 갱신

페이지에 들어 있는 시세는 빌드한 시점의 값입니다.

- **자동:** `.github/workflows/update-data.yml`이 매월 2일에 시세를 받아 `index.html`을 다시 만들고 커밋합니다. 저장소 **Actions** 탭에서 **시세 갱신 → Run workflow**로 바로 실행할 수도 있어요.
- **직접 (Python 3.10 이상, 추가 패키지 없음):**
  ```bash
  python scripts/fetch_data.py   # Yahoo Finance 월간 시세 → data/raw/
  python scripts/build.py        # data/stats.json, data/sec.json, index.html 생성
  ```
  화면만 고쳤다면 `python scripts/build.py --page`로 페이지만 다시 만들 수 있어요.

## 종목 추가

`data/tickers.json`에 한 줄을 추가하고 시세 갱신을 실행하면 됩니다.

```json
["005930.KS", "삼성전자", "stock", "kr_stock"]
```

- 첫 번째 값: Yahoo Finance 티커 (국내 코스피 `.KS`, 코스닥 `.KQ`, 미국은 그대로, 선물은 `=F`)
- 두 번째 값: 화면에 보일 이름
- 세 번째 값: `stock`(주식), `etf`, `fut`(선물)
- 네 번째 값: 분류 `kr_stock`, `us_stock`, `us_tech`, `bond`, `gold`(원자재 전체), `crypto`, `other`

## 폴더 구조

```
index.html              빌드된 페이지 (GitHub Pages가 보여주는 파일)
src/ledger.html         페이지 원본 (/*__STATS__*/, /*__SEC__*/ 자리에 데이터가 들어감)
data/tickers.json       종목 목록
data/stats.json         분류 지수의 월간 수익률 (빌드 결과)
data/sec.json           종목별 월말 시세와 원/달러 환율 (빌드 결과)
scripts/fetch_data.py   시세 받기
scripts/build.py        데이터 계산과 페이지 빌드
.github/workflows/      매월 자동 갱신
```

## 계산 방식

- 모든 수익률은 원화 기준입니다. 해외 자산은 매월 원/달러 환율을 곱해 계산합니다.
- 종목은 배당·분할을 반영한 월말 종가를 씁니다. KOSPI 지수는 배당이 빠진 가격 지수예요.
- 원자재 선물은 가장 가까운 만기 선물 가격을 이어 붙인 시세라, 실제 선물 ETF보다 수익률이 높게 나올 수 있어요(만기 교체 비용 미반영).
- 미래 예측은 ③에서 고른 기간의 연평균 수익률이 매년 똑같이 이어진다고 가정합니다. 적립식의 과거 수익률은 넣은 시점별로 계산한 내부수익률(IRR)입니다.
- 세금과 수수료는 반영하지 않았습니다.

## 주의

- 시세 출처는 Yahoo Finance입니다. 개인적인 참고용으로 만든 도구이며, 데이터의 정확성을 보장하지 않습니다.
- 공개 저장소에 올리면 `data/` 안의 시세 파일도 함께 공개됩니다. 신경 쓰인다면 저장소를 비공개로 만드세요. 비공개 저장소의 GitHub Pages는 유료 요금제에서만 쓸 수 있어요.
- 과거 수익률은 미래 수익률을 보장하지 않습니다. 투자 판단의 책임은 본인에게 있습니다.
