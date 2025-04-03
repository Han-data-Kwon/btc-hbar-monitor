# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify
from datetime import datetime
import requests
import pytz
import os
import feedparser

# 환경 설정 (dotenv or fallback)
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

app = Flask(__name__)
KST = pytz.timezone('Asia/Seoul')

# 고정 데이터 (가상 거래소 주소 포함)
exchange_addresses = {"binance_wallet", "upbit_wallet", "coinbase_wallet"}
MAX_POINTS = 60

# 실시간 저장소
btc_trades, hbar_trades = [], []

# 🕒 현재 시간
def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

# 📈 주요 코인 시세 + RSI
@app.route("/api/price")
def api_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,ripple,hedera-hashgraph",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    res = requests.get(url, params=params).json()
    def fake_rsi(price): return round(30 + (price % 70), 2)  # 모의 RSI
    return jsonify({
        "BTC": {
            "price": round(res["bitcoin"]["usd"], 2),
            "change": round(res["bitcoin"]["usd_24h_change"], 2),
            "rsi": fake_rsi(res["bitcoin"]["usd"])
        },
        "ETH": {
            "price": round(res["ethereum"]["usd"], 2),
            "change": round(res["ethereum"]["usd_24h_change"], 2),
            "rsi": fake_rsi(res["ethereum"]["usd"])
        },
        "XRP": {
            "price": round(res["ripple"]["usd"], 2),
            "change": round(res["ripple"]["usd_24h_change"], 2),
            "rsi": fake_rsi(res["ripple"]["usd"])
        },
        "HBAR": {
            "price": round(res["hedera-hashgraph"]["usd"], 4),
            "change": round(res["hedera-hashgraph"]["usd_24h_change"], 2),
            "rsi": fake_rsi(res["hedera-hashgraph"]["usd"])
        }
    })

# 📰 뉴스 요약
@app.route("/api/news")
def api_news():
    feed_url = "https://cointelegraph.com/rss"
    parsed = feedparser.parse(feed_url)
    news = []
    for entry in parsed.entries[:5]:
        title = entry.title
        link = entry.link
        date = entry.published
        summary = entry.summary[:180].replace('<p>', '').replace('</p>', '') + "..."
        image = entry.media_content[0]['url'] if 'media_content' in entry else ""
        hbar_related = "hbar" in title.lower() or "hedera" in summary.lower()
        news.append({
            "title": title,
            "link": link,
            "date": date,
            "summary": summary,
            "image": image,
            "highlight": hbar_related
        })
    return jsonify(news)

# 📅 경제지표 (TradingEconomics API)
@app.route("/api/economics")
def api_economics():
    api_key = os.getenv("TRADING_API_KEY", "YOUR_FALLBACK_KEY")
    url = f"https://api.tradingeconomics.com/calendar/country/united states?importance=3&c={api_key}"
    res = requests.get(url)
    try:
        data = res.json()
    except:
        return jsonify([])

    result = []
    for item in data[:5]:
        date = item.get("Date", "")[:10]
        event = item.get("Event", "")
        country = item.get("Country", "")
        actual = item.get("Actual", "")
        forecast = item.get("Forecast", "")
        effect = interpret_impact(event, actual, forecast)
        result.append({
            "date": date,
            "event": event,
            "country": country,
            "effect": effect
        })
    return jsonify(result)

# 📌 간단한 해석 생성기
def interpret_impact(event, actual, forecast):
    if actual == "" or forecast == "":
        return "정보 부족"
    try:
        actual_val = float(str(actual).replace('%', '').replace(',', ''))
        forecast_val = float(str(forecast).replace('%', '').replace(',', ''))
        diff = actual_val - forecast_val
        if diff > 0:
            return "예상보다 높음 → 강세 가능"
        elif diff < 0:
            return "예상보다 낮음 → 약세 가능"
        else:
            return "예상과 동일 → 영향 제한적"
    except:
        return "정량 비교 불가"

# 🐳 고래 거래 데이터 생성
def generate_mock_trades(coin="btc"):
    trades = []
    now = get_kst_time()
    for _ in range(10):
        amount = round(random.uniform(0.1, 300000), 2) if coin == "hbar" else round(random.uniform(0.1, 300), 2)
        type_label = ("0-1" if amount < 1 else "1-10" if amount < 10 else "10-100" if amount < 100 else "100+") if coin == "btc" else \
                     ("0-1K" if amount < 1_000 else "1K-10K" if amount < 10_000 else "10K-100K" if amount < 100_000 else "100K+")
        from_addr = random.choice(["user_wallet", "binance_wallet", "whale_wallet"])
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

@app.route("/api/btc_trades")
def api_btc_trades():
    global btc_trades
    trades = generate_mock_trades("btc")
    btc_trades.extend(trades)
    btc_trades = btc_trades[-MAX_POINTS:]
    return jsonify(btc_trades)

@app.route("/api/hbar_trades")
def api_hbar_trades():
    global hbar_trades
    trades = generate_mock_trades("hbar")
    hbar_trades.extend(trades)
    hbar_trades = hbar_trades[-MAX_POINTS:]
    return jsonify(hbar_trades)

@app.route("/")
def index():
    return render_template("index.html")

# 🔁 포트 설정 (Render 호환)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)