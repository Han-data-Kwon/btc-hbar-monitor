import os
import random
import requests
from flask import Flask, render_template, jsonify
from datetime import datetime
from dotenv import load_dotenv
import feedparser

load_dotenv()
app = Flask(__name__)

# 주요 코인 시세
@app.route("/api/price")
def api_price():
    try:
        res = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,hedera-hashgraph,ripple&vs_currencies=usd&include_24hr_change=true"
        ).json()
        return jsonify({
            "BTC": {
                "price": round(res.get("bitcoin", {}).get("usd", 0)),
                "change": round(res.get("bitcoin", {}).get("usd_24h_change", 0), 2),
            },
            "ETH": {
                "price": round(res.get("ethereum", {}).get("usd", 0)),
                "change": round(res.get("ethereum", {}).get("usd_24h_change", 0), 2),
            },
            "HBAR": {
                "price": round(res.get("hedera-hashgraph", {}).get("usd", 0)),
                "change": round(res.get("hedera-hashgraph", {}).get("usd_24h_change", 0), 2),
            },
            "XRP": {
                "price": round(res.get("ripple", {}).get("usd", 0)),
                "change": round(res.get("ripple", {}).get("usd_24h_change", 0), 2),
            }
        })
    except Exception as e:
        print("시세 API 오류:", e)
        return jsonify({
            "BTC": {"price": 0, "change": 0},
            "ETH": {"price": 0, "change": 0},
            "HBAR": {"price": 0, "change": 0},
            "XRP": {"price": 0, "change": 0}
        })

# 뉴스
@app.route("/api/news")
def api_news():
    feed = feedparser.parse("https://cointelegraph.com/rss")
    articles = []
    for entry in feed.entries[:5]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "date": entry.published,
            "summary": entry.summary,
            "image": entry.get("media_content", [{}])[0].get("url", "")
        })
    return jsonify(articles)

# 경제지표
@app.route("/api/economics")
def api_economics():
    try:
        key = os.environ.get("TRADING_API_KEY", "")
        res = requests.get(f"https://api.tradingeconomics.com/calendar?c={key}").json()
        filtered = [
            {
                "date": d.get("date", "")[:10],
                "event": d.get("event", ""),
                "country": d.get("country", ""),
                "actual": d.get("actual"),
                "forecast": d.get("forecast"),
                "previous": d.get("previous"),
                "importance": d.get("importance"),
            }
            for d in res if d.get("importance") == "High"
        ]
        sorted_data = sorted(filtered, key=lambda x: x["date"], reverse=True)
        return jsonify(sorted_data[:15])
    except Exception as e:
        print("경제지표 API 오류:", e)
        return jsonify([])

# 고래 매집 데이터 (모의)
def generate_mock_trades(coin):
    trades = []
    for _ in range(10):
        amount = round(random.uniform(0.1, 300000), 2) if coin == "hbar" else round(random.uniform(0.1, 300), 2)
        trade = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from": random.choice(["binance_wallet", "cold_wallet", "upbit_wallet", "user_wallet"]),
            "to": random.choice(["binance_wallet", "coinbase_wallet", "user_wallet", "kraken_wallet"]),
            "amount": amount,
            "type": classify_trade_type(amount, coin),
            "direction": "매수" if random.choice([True, False]) else "매도"
        }
        trades.append(trade)
    return trades

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

@app.route("/api/btc_trades")
def api_btc_trades():
    return jsonify(generate_mock_trades("btc"))

@app.route("/api/hbar_trades")
def api_hbar_trades():
    return jsonify(generate_mock_trades("hbar"))

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)