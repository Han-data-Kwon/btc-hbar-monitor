from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import random
import requests
import os
import feedparser
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

KST = pytz.timezone("Asia/Seoul")
MAX_POINTS = 60
btc_trades, hbar_trades = [], []
btc_data, hbar_data = [], []
exchange_addresses = {"binance_wallet", "upbit_wallet", "coinbase_wallet"}

def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

# 시세 API
@app.route("/api/price")
def api_price():
    try:
        res = requests.get("https://api.coingecko.com/api/v3/simple/price", params={
            "ids": "bitcoin,ethereum,ripple,hedera-hashgraph",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }).json()

        def format_price(symbol):
            return {
                "price": round(res[symbol]["usd"], 4 if symbol == "hedera-hashgraph" else 2),
                "change": round(res[symbol]["usd_24h_change"], 2)
            }

        return jsonify({
            "BTC": format_price("bitcoin"),
            "ETH": format_price("ethereum"),
            "XRP": format_price("ripple"),
            "HBAR": format_price("hedera-hashgraph")
        })

    except Exception as e:
        print("시세 API 오류:", e)
        return jsonify({})

# 뉴스
@app.route("/api/news")
def api_news():
    url = "https://cointelegraph.com/rss"
    feed = feedparser.parse(url)
    result = []

    for entry in feed.entries[:10]:
        summary = entry.summary if hasattr(entry, "summary") else ""
        result.append({
            "title": entry.title,
            "link": entry.link,
            "date": entry.published,
            "summary": summary[:100] + "..." if len(summary) > 100 else summary
        })

    return jsonify(result)

# 경제지표
@app.route("/api/economics")
def api_economics():
    try:
        key = os.getenv("TRADING_API_KEY")
        res = requests.get(f"https://api.tradingeconomics.com/calendar/country/all?c={key}")
        data = res.json()

        filtered = []
        for d in data:
            if d.get("importance") == 3 and d.get("actual") and d.get("event"):
                effect = "예상보다 높으면 시장에 긍정적" if "PMI" in d["event"] or "GDP" in d["event"] else "높으면 물가 상승 → 부정적"
                filtered.append({
                    "date": d["date"].split("T")[0],
                    "event": d["event"],
                    "country": d.get("country", "N/A"),
                    "effect": effect
                })

        return jsonify(filtered[:10])
    except Exception as e:
        print("경제지표 오류:", e)
        return jsonify([])

# 거래량 mock
def generate_mock_summary_data(coin="btc"):
    if coin == "hbar":
        ranges = {
            "0-1K": {"count": random.randint(30, 60), "volume": 0.0},
            "1K-10K": {"count": random.randint(10, 20), "volume": 0.0},
            "10K-100K": {"count": random.randint(2, 8), "volume": 0.0},
            "100K+": {"count": random.randint(0, 3), "volume": 0.0}
        }
    else:
        ranges = {
            "0-1": {"count": random.randint(50, 100), "volume": 0.0},
            "1-10": {"count": random.randint(5, 15), "volume": 0.0},
            "10-100": {"count": random.randint(1, 5), "volume": 0.0},
            "100+": {"count": random.randint(0, 2), "volume": 0.0}
        }

    for k in ranges:
        low, high = (1, 10) if "1-10" in k or "1K-10K" in k else (
            10, 100) if "10-100" in k or "10K-100K" in k else (
            100, 300) if "100+" in k or "100K+" in k else (0.01, 1)
        ranges[k]["volume"] = round(ranges[k]["count"] * random.uniform(low, high), 2)
    return ranges

# 고래 거래 mock
def generate_mock_trades(coin="btc"):
    trades = []
    now = get_kst_time()
    for _ in range(random.randint(5, 10)):
        amount = round(random.uniform(0.1, 300000), 2) if coin == "hbar" else round(random.uniform(0.1, 300), 2)

        if coin == "hbar":
            type_label = "0-1K" if amount < 1000 else "1K-10K" if amount < 10000 else "10K-100K" if amount < 100000 else "100K+"
        else:
            type_label = "0-1" if amount < 1 else "1-10" if amount < 10 else "10-100" if amount < 100 else "100+"

        from_addr = random.choice(["user_wallet", "whale_wallet", "binance_wallet"])
        to_addr = random.choice(["upbit_wallet", "coinbase_wallet", "user_wallet"])
        direction = "매도" if to_addr in exchange_addresses else "매수"

        trades.append({
            "time": now,
            "from": from_addr,
            "to": to_addr,
            "amount": amount,
            "type": type_label,
            "direction": direction
        })
    return trades

# 라우팅
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/btc_trades")
def api_btc_trades():
    trades = generate_mock_trades("btc")
    btc_trades.extend(trades)
    if len(btc_trades) > MAX_POINTS * 10:
        btc_trades[:] = btc_trades[-MAX_POINTS * 10:]
    return jsonify(btc_trades[-30:])

@app.route("/api/hbar_trades")
def api_hbar_trades():
    trades = generate_mock_trades("hbar")
    hbar_trades.extend(trades)
    if len(hbar_trades) > MAX_POINTS * 10:
        hbar_trades[:] = hbar_trades[-MAX_POINTS * 10:]
    return jsonify(hbar_trades[-30:])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)