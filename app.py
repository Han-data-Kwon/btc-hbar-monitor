from flask import Flask, jsonify, render_template
import requests
import feedparser
import random
import os
from datetime import datetime

app = Flask(__name__)

# ------------------------- API KEY -------------------------
TRADING_API_KEY = os.environ.get("TRADING_API_KEY")  # Render 환경변수에서 불러옴

# ------------------------- ROUTES -------------------------
@app.route('/')
def home():
    return render_template('index.html')

# ------------------------- 실시간 시세 -------------------------
@app.route('/api/price')
def api_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum,ripple,hedera-hashgraph',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        res = requests.get(url).json()
        data = {
            "BTC": {
                "price": round(res.get("bitcoin", {}).get("usd", 0), 2),
                "change": round(res.get("bitcoin", {}).get("usd_24h_change", 0), 2)
            },
            "ETH": {
                "price": round(res.get("ethereum", {}).get("usd", 0), 2),
                "change": round(res.get("ethereum", {}).get("usd_24h_change", 0), 2)
            },
            "XRP": {
                "price": round(res.get("ripple", {}).get("usd", 0), 2),
                "change": round(res.get("ripple", {}).get("usd_24h_change", 0), 2)
            },
            "HBAR": {
                "price": round(res.get("hedera-hashgraph", {}).get("usd", 0), 5),
                "change": round(res.get("hedera-hashgraph", {}).get("usd_24h_change", 0), 2)
            }
        }
        return jsonify(data)
    except Exception as e:
        print("[ERROR] /api/price:", e)
        return jsonify({})

# ------------------------- 뉴스 요약 -------------------------
@app.route('/api/news')
def api_news():
    feed_url = "https://cointelegraph.com/rss"
    feed = feedparser.parse(feed_url)
    items = []
    for entry in feed.entries[:5]:
        items.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary,
            "date": entry.published
        })
    return jsonify(items)

# ------------------------- 경제지표 -------------------------
@app.route('/api/economics')
def api_economics():
    try:
        url = f"https://api.tradingeconomics.com/calendar?c={TRADING_API_KEY}"
        res = requests.get(url)
        data = res.json()
        latest = []
        for item in data[:10]:
            event = item.get("Event", "")
            country = item.get("Country", "")
            date = item.get("Date", "")
            impact = item.get("Impact", "")
            # 간단한 해석 생성
            if impact == "High":
                effect = "시장에 강한 영향 예상"
            elif impact == "Medium":
                effect = "일정 수준의 영향 예상"
            else:
                effect = "시장 영향 낮음"
            latest.append({
                "date": date[:10],
                "event": event,
                "country": country,
                "effect": effect
            })
        return jsonify(latest)
    except Exception as e:
        print("[ERROR] /api/economics:", e)
        return jsonify([])

# ------------------------- 고래 거래 -------------------------
def generate_mock_trades(coin="btc"):
    trades = []
    for _ in range(20):
        amount = round(random.uniform(0.1, 300000), 2) if coin == "hbar" else round(random.uniform(0.1, 300), 2)
        ttype = "0-1K" if amount < 1000 else "1K-10K" if amount < 10000 else "10K-100K" if amount < 100000 else "100K+"
        if coin == "btc":
            ttype = "0-1" if amount < 1 else "1-10" if amount < 10 else "10-100" if amount < 100 else "100+"
        direction = random.choice(["매수", "매도"])
        trades.append({
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "from": random.choice(["binance_wallet", "unknown_wallet", "upbit_wallet", "coinbase_wallet"]),
            "to": random.choice(["cold_wallet", "unknown_wallet", "binance_wallet"]),
            "amount": amount,
            "type": ttype,
            "direction": direction
        })
    return trades

@app.route('/api/btc_trades')
def api_btc_trades():
    try:
        trades = generate_mock_trades("btc")
        return jsonify(trades)
    except Exception as e:
        print("[ERROR] /api/btc_trades:", e)
        return jsonify([])

@app.route('/api/hbar_trades')
def api_hbar_trades():
    try:
        trades = generate_mock_trades("hbar")
        return jsonify(trades)
    except Exception as e:
        print("[ERROR] /api/hbar_trades:", e)
        return jsonify([])

# ------------------------- 실행 -------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)