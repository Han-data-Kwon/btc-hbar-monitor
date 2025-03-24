from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import random
import requests
import os

app = Flask(__name__)

MAX_POINTS = 60
KST = pytz.timezone('Asia/Seoul')

btc_data = []
hbar_data = []
btc_trades = []
hbar_trades = []

# 거래소 지갑 주소 모음 (간단 예시)
exchange_addresses = {"binance_wallet", "upbit_wallet", "coinbase_wallet"}

def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

def generate_mock_summary_data():
    data = {
        "0-1": {"count": random.randint(50, 100), "volume": 0.0},
        "1-10": {"count": random.randint(5, 15), "volume": 0.0},
        "10-100": {"count": random.randint(1, 5), "volume": 0.0},
        "100+": {"count": random.randint(0, 2), "volume": 0.0}
    }
    for k in data:
        low, high = (1, 10) if k == "1-10" else (
            10, 100) if k == "10-100" else (
            100, 300) if k == "100+" else (0.01, 1)
        data[k]["volume"] = round(data[k]["count"] * random.uniform(low, high), 2)
    return data

def generate_mock_trades():
    trades = []
    now = get_kst_time()
    for _ in range(random.randint(5, 10)):
        amount = round(random.uniform(0.05, 300), 2)
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
    summary = generate_mock_summary_data()
    btc_data.append({"time": now, "data": summary})
    if len(btc_data) > MAX_POINTS:
        btc_data.pop(0)
    return jsonify(btc_data)

@app.route("/api/hbar")
def api_hbar():
    now = get_kst_time()
    summary = generate_mock_summary_data()
    hbar_data.append({"time": now, "data": summary})
    if len(hbar_data) > MAX_POINTS:
        hbar_data.pop(0)
    return jsonify(hbar_data)

@app.route("/api/btc_trades")
def api_btc_trades():
    trades = generate_mock_trades()
    btc_trades.extend(trades)
    if len(btc_trades) > MAX_POINTS * 10:
        del btc_trades[:len(btc_trades) - MAX_POINTS * 10]
    return jsonify(btc_trades[-30:])  # 최근 30개만 반환

@app.route("/api/hbar_trades")
def api_hbar_trades():
    trades = generate_mock_trades()
    hbar_trades.extend(trades)
    if len(hbar_trades) > MAX_POINTS * 10:
        del hbar_trades[:len(hbar_trades) - MAX_POINTS * 10]
    return jsonify(hbar_trades[-30:])

@app.route("/api/price")
def api_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,hedera-hashgraph",
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
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


