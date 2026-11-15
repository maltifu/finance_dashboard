"""Yahoo Finance에서 월간 시세를 받아 data/raw/ 에 저장합니다.

사용법:  python scripts/fetch_data.py
- data/tickers.json 의 모든 종목
- 분류 지수(KOSPI, S&P500 TR, NASDAQ-100, AGG, 금 선물, 비트코인)와 원/달러 환율
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
INDEXES = ["^KS11", "^SP500TR", "^NDX", "AGG", "GC=F", "BTC-USD", "KRW=X"]


def fname(t):
    return re.sub(r"[^A-Za-z0-9]", "_", t) + ".json"


def fetch(t):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%s?range=25y&interval=1mo" % urllib.parse.quote(t)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    os.makedirs(RAW, exist_ok=True)
    tickers = [row[0] for row in json.load(open(os.path.join(ROOT, "data", "tickers.json"), encoding="utf-8"))]
    failed = []
    for t in dict.fromkeys(INDEXES + tickers):
        try:
            body = fetch(t)
            json.loads(body)["chart"]["result"][0]
            open(os.path.join(RAW, fname(t)), "wb").write(body)
            print("ok  ", t)
        except Exception as e:  # noqa: BLE001
            failed.append(t)
            print("FAIL", t, e)
        time.sleep(0.15)
    if failed:
        print("받지 못한 종목:", ", ".join(failed), "(이번 빌드에서는 빠집니다)")
    if any(t in INDEXES for t in failed):
        print("분류 지수나 환율을 받지 못해 빌드를 멈춥니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
