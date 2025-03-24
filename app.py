from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import random
import requests

app = Flask(__name__)

KST = pytz.timezone("Asia/Seoul")
MAX_POINTS = 60  # 최근 30분 (30초 단위)
btc_data = []
hbar_data = []

btc_trades = []
hbar_trades = []

# 💡 고래 주소 목록 (mock)
whale_addresses = ["0xABC123", "0xDEAD99", "0xFAFA01", "0xBEEF22"]

# 📆 현재 KST 시간
def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

# 🎲 거래량/거래수 mock 생성 함수
def generate_mock_data(coin="btc"):
    if coin == "btc":
        keys = {
            "0-1": (0.01, 1),
            "1-10": (1, 10),
            "10-100": (10, 100),
            "100+": (100, 300)
        }
    else:
        keys = {
            "0-1k": (10, 1000),
            "1k-10k": (1000, 10000),
            "10k-100k": (10000, 100000),
            "100k+": (100000, 300000)
        }

    result = {}
    for key, (low, high) in keys.items():
        count = random.randint(1, 8)
        avg_volume = random.uniform(low, high)
        volume = round(count * avg_volume, 2)
        result[key] = {"count": count, "volume": volume}
    return result

# 🧾 고래 거래 mock 데이터 생성
def generate_mock_trades(coin="btc"):
    types = {
        "btc": ["0-1", "1-10", "10-100", "100+"],
        "hbar": ["0-1k", "1k-10k", "10k-100k", "100k+"]
    }
    trades = []
    for _ in range(random.randint(2, 4)):
        from_addr = random.choice(whale_addresses)
        to_addr = random.choice(whale_addresses)
        while to_addr == from_addr:
            to_addr = random.choice(whale_addresses)
        amount = round(random.uniform(0.5, 150), 2)
        type_range = random.choice(types[coin])
        direction = "매수" if "exchange" in to_addr.lower() else "매도"
        trades.append({
            "time": get_kst_time(),
            "from": from_addr,
            "to": to_addr,
            "amount": amount,
            "type": type_range,
            "direction": direction
        })
    return trades

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/btc")
def api_btc():
    entry = {"time": get_kst_time(), "data": generate_mock_data("btc")}
    btc_data.append(entry)
    if len(btc_data) > MAX_POINTS:
        btc_data.pop(0)
    return jsonify(btc_data)

@app.route("/api/hbar")
def api_hbar():
    entry = {"time": get_kst_time(), "data": generate_mock_data("hbar")}
    hbar_data.append(entry)
    if len(hbar_data) > MAX_POINTS:
        hbar_data.pop(0)
    return jsonify(hbar_data)

@app.route("/api/price")
def api_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,hedera-hashgraph",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        res = requests.get(url, params=params, timeout=5)
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
    except Exception as e:
        print("가격 API 에러:", e)
        return jsonify({"BTC": {"price": 0, "change": 0}, "HBAR": {"price": 0, "change": 0}})

@app.route("/api/btc_trades")
def api_btc_trades():
    trades = generate_mock_trades("btc")
    btc_trades.extend(trades)
    btc_trades[:] = btc_trades[-20:]
    return jsonify(btc_trades)

@app.route("/api/hbar_trades")
def api_hbar_trades():
    trades = generate_mock_trades("hbar")
    hbar_trades.extend(trades)
    hbar_trades[:] = hbar_trades[-20:]
    return jsonify(hbar_trades)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

