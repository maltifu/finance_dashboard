"""data/raw/ 시세로 data/stats.json, data/sec.json 을 만들고 index.html 을 빌드합니다.

사용법:
  python scripts/build.py            # data/raw 가 있으면 데이터부터 다시 계산, 없으면 기존 data/*.json 으로 페이지만 빌드
  python scripts/build.py --page     # 페이지만 빌드
"""
import datetime, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
UTC = datetime.timezone.utc
START = "2006-01"


def idx(m):
    y, mo = map(int, m.split("-")); return y * 12 + mo - 1


def mon(i):
    return "%04d-%02d" % (i // 12, i % 12 + 1)


def fname(t):
    return re.sub(r"[^A-Za-z0-9]", "_", t) + ".json"


def load(t, now, adj=True, fx=False):
    """월말 시세(배당·분할 조정) {YYYY-MM: 값}. 빠진 달은 로그 선형 보간."""
    d = json.load(open(os.path.join(RAW, fname(t)), encoding="utf-8-sig"))
    r = d["chart"]["result"][0]
    q = r["indicators"]
    vals = q["adjclose"][0]["adjclose"] if adj and "adjclose" in q else q["quote"][0]["close"]
    out = {}
    for ts, v in zip(r["timestamp"], vals):
        if v is None or v <= 0 or (fx and v < 500):
            continue
        m = datetime.datetime.fromtimestamp(ts + 86400 * 3, UTC).strftime("%Y-%m")
        if m < now:
            out[m] = v
    ks = sorted(out)
    for a, b in zip(ks, ks[1:]):
        ia, ib = idx(a), idx(b)
        for i in range(ia + 1, ib):
            w = (i - ia) / (ib - ia)
            out[mon(i)] = math.exp(math.log(out[a]) * (1 - w) + math.log(out[b]) * w)
    return {k: v for k, v in out.items() if k >= START}, r["meta"]


def sig(v, n=5):
    return 0 if v == 0 else float("%.*g" % (n, v))


def build_stats(now):
    fx, _ = load("KRW=X", now, adj=False, fx=True)
    series = {"kr_stock": ("^KS11", False), "us_stock": ("^SP500TR", True), "us_tech": ("^NDX", True),
              "bond": ("AGG", True), "gold": ("GC=F", True), "crypto": ("BTC-USD", True)}
    classes = {}
    for k, (t, usd) in series.items():
        s, _ = load(t, now, adj=(t == "AGG"))
        months = sorted(m for m in s if (not usd or m in fx))
        lv = {m: s[m] * (fx[m] if usd else 1) for m in months}
        rets, first = [], None
        for a, b in zip(months, months[1:]):
            if idx(b) - idx(a) != 1:
                rets, first = [], None; continue
            first = first or b
            rets.append(round(lv[b] / lv[a] - 1, 5))
        n = len(rets); mean = sum(rets) / n
        sd = math.sqrt(sum((x - mean) ** 2 for x in rets) / (n - 1))
        cagr = math.exp(sum(math.log(1 + x) for x in rets) / n * 12) - 1
        classes[k] = {"start": first, "returns": rets, "cagr": round(cagr, 4), "vol": round(sd * math.sqrt(12), 4), "n": n}
    return {"asOf": sorted(fx)[-1], "classes": classes}


def build_sec(now):
    fx, fxmeta = load("KRW=X", now, adj=False, fx=True)
    fks = sorted(fx)
    res = {"asOf": fks[-1], "fx": {"s": fks[0], "p": [round(fx[k], 2) for k in fks]}, "fxNow": round(fxmeta["regularMarketPrice"], 2), "sec": []}
    times = []
    for t, name, kind, cat in json.load(open(os.path.join(ROOT, "data", "tickers.json"), encoding="utf-8")):
        if not os.path.exists(os.path.join(RAW, fname(t))):
            print("건너뜀(시세 없음):", t); continue
        s, meta = load(t, now)
        ks = sorted(s)
        if len(ks) < 3:
            print("건너뜀(자료 부족):", t); continue
        last = meta.get("regularMarketPrice")
        cur = meta.get("currency")
        if cur == "USX":  # 미국 센트 단위 → 달러
            s = {k: v / 100 for k, v in s.items()}; last /= 100; cur = "USD"
        lt = datetime.datetime.fromtimestamp(meta.get("regularMarketTime"), UTC).strftime("%Y-%m-%d")
        times.append(lt)
        res["sec"].append({"t": t, "n": name, "k": kind, "c": cat, "cur": cur, "s": ks[0], "p": [sig(s[k]) for k in ks], "last": sig(last, 6), "lt": lt})
    res["now"] = max(times)
    return res


def build_page():
    src = open(os.path.join(ROOT, "src", "ledger.html"), encoding="utf-8").read()
    stats = json.load(open(os.path.join(ROOT, "data", "stats.json"), encoding="utf-8"))
    sec = json.load(open(os.path.join(ROOT, "data", "sec.json"), encoding="utf-8"))
    stats["fx"] = sec["fxNow"]
    body = src.replace("/*__STATS__*/", json.dumps(stats, separators=(",", ":"))) \
              .replace("/*__SEC__*/", json.dumps(sec, ensure_ascii=False, separators=(",", ":")))
    assert "/*__" not in body
    head = ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
            'body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(head + body + "</body></html>\n")
    print("index.html", round(len(body.encode()) / 1024), "KB")


def main():
    now = datetime.datetime.now(UTC).strftime("%Y-%m")
    if "--page" not in sys.argv and os.path.isdir(RAW):
        json.dump(build_stats(now), open(os.path.join(ROOT, "data", "stats.json"), "w", encoding="utf-8"), separators=(",", ":"))
        json.dump(build_sec(now), open(os.path.join(ROOT, "data", "sec.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print("data/stats.json, data/sec.json 갱신")
    build_page()


if __name__ == "__main__":
    main()
