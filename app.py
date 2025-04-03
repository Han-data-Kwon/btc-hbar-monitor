import os
from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 설정
KST = pytz.timezone('Asia/Seoul')
MAX_POINTS = 60
exchange_addresses = {"binance_wallet", "upbit_wallet", "coinbase_wallet"}
TRADING_API_KEY = os.getenv("TRADING_API_KEY")

btc_trades, hbar_trades = [], []

def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

def generate_mock_trades(coin="btc"):
    import random
    trades = []
    now = get_kst_time()
    for _ in range(random.randint(5, 10)):
        amount = round(random.uniform(0.05, 300000 if coin == "hbar" else 300), 2)
        if coin == "hbar":
            if amount < 1000: type_label = "0-1K"
            elif amount < 10000: type_label = "1K-10K"
            elif amount < 100000: type_label = "10K-100K"
            else: type_label = "100K+"
        else:
            if amount < 1: type_label = "0-1"
            elif amount < 10: type_label = "1-10"
            elif amount < 100: type_label = "10-100"
            else: type_label = "100+"

        from_addr = random.choice(["user_wallet", "whale_wallet", "random_wallet", "binance_wallet"])
        to_addr = random.choice(["upbit_wallet", "user_wallet", "coinbase_wallet"])
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/btc_trades")
def api_btc_trades():
    trades = generate_mock_trades("btc")
    btc_trades.extend(trades)
    if len(btc_trades) > MAX_POINTS * 10:
        del btc_trades[:len(btc_trades) - MAX_POINTS * 10]
    return jsonify(btc_trades[-30:])

@app.route("/api/hbar_trades")
def api_hbar_trades():
    trades = generate_mock_trades("hbar")
    hbar_trades.extend(trades)
    if len(hbar_trades) > MAX_POINTS * 10:
        del hbar_trades[:len(hbar_trades) - MAX_POINTS * 10]
    return jsonify(hbar_trades[-30:])

@app.route("/api/price")
def api_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,ripple,hedera-hashgraph",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        return jsonify({
            "BTC": {"price": data["bitcoin"]["usd"], "change": round(data["bitcoin"]["usd_24h_change"], 2)},
            "ETH": {"price": data["ethereum"]["usd"], "change": round(data["ethereum"]["usd_24h_change"], 2)},
            "XRP": {"price": data["ripple"]["usd"], "change": round(data["ripple"]["usd_24h_change"], 2)},
            "HBAR": {"price": data["hedera-hashgraph"]["usd"], "change": round(data["hedera-hashgraph"]["usd_24h_change"], 2)}
        })
    except Exception as e:
        print("[Error] Coingecko API:", e)
        return jsonify({})

@app.route("/api/news")
def api_news():
    import feedparser
    url = "https://cointelegraph.com/rss"
    feed = feedparser.parse(url)
    entries = feed.entries[:5]
    result = []
    for e in entries:
        result.append({
            "title": e.title,
            "link": e.link,
            "date": e.published,
            "summary": e.summary[:200] + "..."
        })
    return jsonify(result)

@app.route("/api/economics")
def api_economics():
    try:
        url = "https://api.tradingeconomics.com/calendar/country/united states"
        res = requests.get(url, params={"c": TRADING_API_KEY})
        data = res.json()[:5]
        result = []
        for d in data:
            result.append({
                "date": d.get("Date", "N/A"),
                "event": d.get("Event", "N/A"),
                "country": d.get("Country", "N/A"),
                "effect": interpret_event(d.get("Event", ""))
            })
        return jsonify(result)
    except Exception as e:
        print("[Error] TradingEconomics API:", e)
        return jsonify([])

def interpret_event(event):
    if "GDP" in event or "Growth" in event: return "성장률이 높으면 코인에 긍정적"
    if "Unemployment" in event: return "실업률 상승은 위험회피 심리 → 코인 약세"
    if "CPI" in event or "Inflation" in event: return "물가 상승은 긴축 우려 → 코인에 부정적"
    if "Rate" in event or "FOMC" in event: return "금리 결정은 시장 변동성 확대 요인"
    return "시장에 미치는 영향은 중립"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render용 포트 설정
    app.run(host="0.0.0.0", port=port)