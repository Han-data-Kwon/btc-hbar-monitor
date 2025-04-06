import os
import random
import requests
import feedparser
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- KST 기준 시간 함수 ---
def get_kst_time():
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")

# --- 시세 API ---
@app.route("/api/price")
def api_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,hedera-hashgraph,ripple",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        res = requests.get(url, params=params).json()
        return jsonify({
            "BTC": {
                "price": round(res["bitcoin"]["usd"], 2),
                "change": round(res["bitcoin"]["usd_24h_change"], 2)
            },
            "ETH": {
                "price": round(res["ethereum"]["usd"], 2),
                "change": round(res["ethereum"]["usd_24h_change"], 2)
            },
            "HBAR": {
                "price": round(res["hedera-hashgraph"]["usd"], 4),
                "change": round(res["hedera-hashgraph"]["usd_24h_change"], 2)
            },
            "XRP": {
                "price": round(res["ripple"]["usd"], 4),
                "change": round(res["ripple"]["usd_24h_change"], 2)
            }
        })
    except Exception as e:
        print("시세 API 오류:", e)
        return jsonify({})

# --- RSI + 외부 시세 차트용 API ---
@app.route("/api/indicators")
def api_indicators():
    try:
        # RSI 값은 mock으로 제공 중
        now = datetime.utcnow()
        labels = [(now - timedelta(minutes=5 * i)).strftime("%H:%M") for i in reversed(range(12))]
        mock_rsi = [round(random.uniform(30, 70), 2) for _ in range(12)]
        return jsonify({
            "labels": labels,
            "rsi": mock_rsi
        })
    except Exception as e:
        print("지표 API 오류:", e)
        return jsonify({})

# --- 뉴스 API ---
@app.route("/api/news")
def api_news():
    feed = feedparser.parse("https://cointelegraph.com/rss")
    articles = []
    for entry in feed.entries[:10]:
        title = entry.title
        is_hbar = "HBAR" in title.upper() or "HEDERA" in title.upper()
        is_whale = "WHALE" in title.upper()
        articles.append({
            "title": title,
            "link": entry.link,
            "date": entry.published,
            "summary": entry.summary,
            "image": entry.get("media_content", [{}])[0].get("url", ""),
            "highlight": is_hbar or is_whale
        })
    return jsonify(articles)

# --- 경제지표 API ---
@app.route("/api/economics")
def api_economics():
    try:
        key = os.environ.get("TRADING_API_KEY")
        res = requests.get(f"https://api.tradingeconomics.com/calendar?c={key}").json()

        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

        filtered = []
        for d in res:
            date_str = d.get("date", "")[:10]
            if date_str == yesterday:
                importance = d.get("importance", "")
                effect = "시장 영향 높음" if importance == "High" else "보통"
                filtered.append({
                    "date": date_str,
                    "event": d.get("event", ""),
                    "country": d.get("country", ""),
                    "actual": d.get("actual"),
                    "forecast": d.get("forecast"),
                    "previous": d.get("previous"),
                    "importance": importance,
                    "effect": effect
                })

        sorted_data = sorted(filtered, key=lambda x: x["date"], reverse=True)
        return jsonify(sorted_data[:15])

    except Exception as e:
        print("경제지표 API 오류:", e)
        return jsonify([])

# --- 고래 거래 MOCK ---
def classify_trade_type(amount, coin):
    if coin == "btc":
        if amount < 1: return "0–1"
        elif amount < 10: return "1–10"
        elif amount < 100: return "10–100"
        else: return "100+"
    else:
        if amount < 1000: return "0–1K"
        elif amount < 10000: return "1K–10K"
        elif amount < 100000: return "10K–100K"
        else: return "100K+"

def generate_mock_trades(coin):
    trades = []
    for _ in range(10):
        amount = round(random.uniform(0.1, 300000), 2) if coin == "hbar" else round(random.uniform(0.1, 300), 2)
        trades.append({
            "time": get_kst_time(),
            "from": random.choice(["binance_wallet", "upbit_wallet", "user_wallet"]),
            "to": random.choice(["coinbase_wallet", "user_wallet", "kraken_wallet"]),
            "amount": amount,
            "type": classify_trade_type(amount, coin),
            "direction": "매수" if random.choice([True, False]) else "매도"
        })
    return trades

@app.route("/api/btc_trades")
def api_btc_trades():
    return jsonify(generate_mock_trades("btc"))

@app.route("/api/hbar_trades")
def api_hbar_trades():
    return jsonify(generate_mock_trades("hbar"))

# --- 기본 라우트 ---
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)