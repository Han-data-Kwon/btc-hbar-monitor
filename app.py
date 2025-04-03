import os
import requests
import feedparser
from flask import Flask, render_template, jsonify
from datetime import datetime
from dotenv import load_dotenv
import random

load_dotenv()
app = Flask(__name__)

# ===== 코인 시세 API =====
@app.route("/api/price")
def api_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    coins = "bitcoin,ethereum,hedera,ripple"
    params = {"ids": coins, "vs_currencies": "usd", "include_24hr_change": "true"}
    try:
        res = requests.get(url, params=params, timeout=10).json()
        return jsonify({
            "BTC": {
                "price": round(res.get("bitcoin", {}).get("usd", 0), 2),
                "change": round(res.get("bitcoin", {}).get("usd_24h_change", 0), 2),
            },
            "ETH": {
                "price": round(res.get("ethereum", {}).get("usd", 0), 2),
                "change": round(res.get("ethereum", {}).get("usd_24h_change", 0), 2),
            },
            "HBAR": {
                "price": round(res.get("hedera", {}).get("usd", 0), 2),
                "change": round(res.get("hedera", {}).get("usd_24h_change", 0), 2),
            },
            "XRP": {
                "price": round(res.get("ripple", {}).get("usd", 0), 2),
                "change": round(res.get("ripple", {}).get("usd_24h_change", 0), 2),
            },
        })
    except Exception as e:
        print("[ERROR /api/price]", e)
        return jsonify({})

# ===== 뉴스 API (Cointelegraph RSS) =====
@app.route("/api/news")
def api_news():
    feed_url = "https://cointelegraph.com/rss"
    feed = feedparser.parse(feed_url)
    news = []
    for entry in feed.entries[:5]:
        news.append({
            "title": entry.title,
            "link": entry.link,
            "date": entry.published,
            "image": entry.get("media_content", [{}])[0].get("url", "")
        })
    return jsonify(news)

# ===== 경제지표 API (TradingEconomics) =====
@app.route("/api/economics")
def api_economics():
    api_key = os.getenv("TRADING_API_KEY")
    url = f"https://api.tradingeconomics.com/calendar?c={api_key}"
    try:
        res = requests.get(url, timeout=10).json()
        keywords = ["FOMC", "GDP", "Inflation", "Interest", "Unemployment", "CPI", "PPI", "Retail", "PMI"]
        data = []
        for e in res:
            if any(k in e["Event"] for k in keywords):
                effect = "시장 영향 낮음"
                if e.get("Actual") and e.get("Forecast"):
                    try:
                        delta = abs(float(e["Actual"]) - float(e["Forecast"]))
                        if delta > 1:
                            effect = "시장 영향 큼"
                        elif delta > 0.3:
                            effect = "시장 영향 중간"
                    except:
                        pass
                data.append({
                    "date": e.get("Date", "")[:10],
                    "event": e.get("Event", ""),
                    "country": e.get("Country", ""),
                    "actual": e.get("Actual", "-"),
                    "forecast": e.get("Forecast", "-"),
                    "previous": e.get("Previous", "-"),
                    "effect": effect,
                })
        return jsonify(data)
    except Exception as e:
        print("[ERROR /api/economics]", e)
        return jsonify([])

# ===== 고래 거래 Mock 데이터 =====
@app.route("/api/btc_trades")
def api_btc_trades():
    trades = generate_mock_trades("btc")
    return jsonify(trades)

@app.route("/api/hbar_trades")
def api_hbar_trades():
    trades = generate_mock_trades("hbar")
    return jsonify(trades)

def generate_mock_trades(coin="btc"):
    trades = []
    for _ in range(12):
        amount = round(random.uniform(0.1, 300000), 2) if coin == "hbar" else round(random.uniform(0.1, 300), 2)
        direction = random.choice(["매수", "매도"])
        from_addr = random.choice(["binance_wallet", "user_wallet", "coinbase_wallet"])
        to_addr = random.choice(["user_wallet", "upbit_wallet", "binance_wallet"])
        if coin == "btc":
            if amount > 100:
                size = "100+"
            elif amount > 10:
                size = "10–100"
            elif amount > 1:
                size = "1–10"
            else:
                size = "0–1"
        else:
            if amount > 100000:
                size = "100K+"
            elif amount > 10000:
                size = "10K–100K"
            elif amount > 1000:
                size = "1K–10K"
            else:
                size = "0–1K"
        trades.append({
            "time": datetime.utcnow().strftime("%H:%M:%S"),
            "from": from_addr,
            "to": to_addr,
            "amount": amount,
            "type": size,
            "direction": direction
        })
    return trades

# ===== 메인 페이지 렌더링 =====
@app.route("/")
def home():
    return render_template("index.html")

# ===== 실행 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)