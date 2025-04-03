from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import random
import requests
import os  # ✅ 이 줄이 꼭 필요

app = Flask(__name__)

KST = pytz.timezone('Asia/Seoul')

btc_trades = []
hbar_trades = []

def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

exchange_addresses = {"binance_wallet", "upbit_wallet", "coinbase_wallet"}

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

@app.route("/api/btc_trades")
def api_btc_trades():
    trades = generate_mock_trades("btc")
    btc_trades.extend(trades)
    if len(btc_trades) > 600:
        del btc_trades[:-600]
    return jsonify(btc_trades[-30:])

@app.route("/api/hbar_trades")
def api_hbar_trades():
    trades = generate_mock_trades("hbar")
    hbar_trades.extend(trades)
    if len(hbar_trades) > 600:
        del hbar_trades[:-600]
    return jsonify(hbar_trades[-30:])

@app.route("/api/price")
def api_price():
    try:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # 기본값은 10000으로 설정
    app.run(host="0.0.0.0", port=port, debug=False)