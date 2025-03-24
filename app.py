from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import random

app = Flask(__name__)

MAX_POINTS = 60  # 30초 단위, 최대 30분
KST = pytz.timezone('Asia/Seoul')

btc_data = []
hbar_data = []

def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

def generate_mock_data():
    # 예시로 랜덤 거래 생성 (구간별 거래 건수 및 거래량)
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
        # 각 거래량은 평균값 근처로 랜덤 생성
        data[k]["volume"] = round(data[k]["count"] * random.uniform(low, high), 2)
    return data

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/btc")
def api_btc():
    now = get_kst_time()
    entry = {"time": now, "data": generate_mock_data()}
    btc_data.append(entry)
    if len(btc_data) > MAX_POINTS:
        btc_data.pop(0)
    return jsonify(btc_data)

@app.route("/api/hbar")
def api_hbar():
    now = get_kst_time()
    entry = {"time": now, "data": generate_mock_data()}
    hbar_data.append(entry)
    if len(hbar_data) > MAX_POINTS:
        hbar_data.pop(0)
    return jsonify(hbar_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import requests

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


