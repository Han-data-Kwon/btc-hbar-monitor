# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import requests
import os
import feedparser
import random

app = Flask(__name__)
KST = pytz.timezone("Asia/Seoul")
MAX_POINTS = 60

btc_trades, hbar_trades = [], []
exchange_addresses = {"binance_wallet", "upbit_wallet", "coinbase_wallet"}

# 주요 코인 지표용
coin_list = ["bitcoin", "ethereum", "ripple", "hedera-hashgraph"]

def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

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

        from_addr = random.choice(list(exchange_addresses) + ["user_wallet"])
        to_addr = random.choice(list(exchange_addresses) + ["user_wallet"])
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

@app.route("/api/price")
def api_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(coin_list),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        result = {}
        for coin in coin_list:
            if coin in data:
                result[coin.upper()] = {
                    "price": round(data[coin]["usd"], 4),
                    "change": round(data[coin]["usd_24h_change"], 2)
                }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            "summary": entry.summary[:120] + "..." if entry.get("summary") else ""
        })
    return jsonify(news)

@app.route("/api/economics")
def api_economics():
    key = os.getenv("TRADING_API_KEY", "")
    url = f"https://api.tradingeconomics.com/calendar?importance=3&c={key}"
    try:
        res = requests.get(url)
        data = res.json()
        latest = []
        for d in data[:5]:
            effect = f"{d['country']}의 {d['event']} 발표는 시장 변동 가능성이 높습니다."
            latest.append({
                "date": d.get("date", ""),
                "event": d.get("event", ""),
                "country": d.get("country", ""),
                "effect": effect
            })
        return jsonify(latest)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)