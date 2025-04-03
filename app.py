from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import random
import requests
import feedparser
import os

app = Flask(__name__)

MAX_POINTS = 60
KST = pytz.timezone('Asia/Seoul')

btc_data = []
hbar_data = []
btc_trades = []
hbar_trades = []

exchange_addresses = {"binance_wallet", "upbit_wallet", "coinbase_wallet"}

def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

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

def generate_mock_trades(coin="btc"):
    trades = []
    now = get_kst_time()
    for _ in range(random.randint(5, 10)):
        amount = round(random.uniform(0.05, 300000), 2) if coin == "hbar" else round(random.uniform(0.05, 300), 2)

        if coin == "hbar":
            if amount < 1000:
                type_label = "0-1K"
            elif amount < 10000:
                type_label = "1K-10K"
            elif amount < 100000:
                type_label = "10K-100K"
            else:
                type_label = "100K+"
        else:
            if amount < 1:
                type_label = "0-1"
            elif amount < 10:
                type_label = "1-10"
            elif amount < 100:
                type_label = "10-100"
            else:
                type_label = "100+"

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

@app.route("/api/btc")
def api_btc():
    now = get_kst_time()
    summary = generate_mock_summary_data("btc")
    btc_data.append({"time": now, "data": summary})
    if len(btc_data) > MAX_POINTS:
        btc_data.pop(0)
    return jsonify(btc_data)

@app.route("/api/hbar")
def api_hbar():
    now = get_kst_time()
    summary = generate_mock_summary_data("hbar")
    hbar_data.append({"time": now, "data": summary})
    if len(hbar_data) > MAX_POINTS:
        hbar_data.pop(0)
    return jsonify(hbar_data)

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
        "ids": "bitcoin,hedera-hashgraph,ethereum,ripple",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    res = requests.get(url, params=params)
    data = res.json()
    return jsonify({
        "BTC": {
            "price": round(data["bitcoin"]["usd"], 2),
            "change": round(data["bitcoin"]["usd_24h_change"], 2)
        },
        "HBAR": {
            "price": round(data["hedera-hashgraph"]["usd"], 4),
            "change": round(data["hedera-hashgraph"]["usd_24h_change"], 2)
        },
        "ETH": {
            "price": round(data["ethereum"]["usd"], 2),
            "change": round(data["ethereum"]["usd_24h_change"], 2)
        },
        "XRP": {
            "price": round(data["ripple"]["usd"], 2),
            "change": round(data["ripple"]["usd_24h_change"], 2)
        }
    })

@app.route("/api/news")
def api_news():
    url = "https://cointelegraph.com/rss"
    feed = feedparser.parse(url)
    items = feed.entries[:5]
    result = []
    for item in items:
        result.append({
            "title": item.title,
            "link": item.link,
            "published": item.published,
            "summary": item.summary[:150] + "..."
        })
    return jsonify(result)

@app.route("/api/economic")
def api_economic():
    return jsonify([
        {"event": "미국 FOMC 금리 결정", "date": "2025-04-11", "impact": "매우 높음", "interpret": "금리가 예상보다 높으면 코인 하락 가능"},
        {"event": "미국 고용 지표 발표", "date": "2025-04-05", "impact": "매우 높음", "interpret": "실업률 상승 시 위험자산에 악영향"},
        {"event": "CPI 소비자물가지수", "date": "2025-04-08", "impact": "매우 높음", "interpret": "인플레이션 지표 상승 시 긴축 가능성 높아짐"}
    ])