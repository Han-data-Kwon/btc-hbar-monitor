from flask import Flask, render_template, jsonify
import requests
import threading
import time
from datetime import datetime

app = Flask(__name__)

# BTC 설정
BTC_API = "https://blockchain.info/unconfirmed-transactions?format=json"
BTC_LABELS = ["0-1 BTC", "1-10 BTC", "10-100 BTC", "100+ BTC"]
BTC_BINS = [0, 1, 10, 100, 1000]
btc_data = {"timestamps": [], "values": {label: [] for label in BTC_LABELS}}

# HBAR 설정
HBAR_API = "https://mainnet-public.mirrornode.hedera.com/api/v1/transactions"
HBAR_LABELS = ["100K-1M HBAR", "1M-10M HBAR", "10M-100M HBAR", "100M+ HBAR"]
HBAR_BINS = [100_000, 1_000_000, 10_000_000, 100_000_000]
hbar_data = {"timestamps": [], "values": {label: [] for label in HBAR_LABELS}}

def fetch_btc():
    try:
        r = requests.get(BTC_API, timeout=10)
        txs = r.json()["txs"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        btc_data["timestamps"].append(now)
        counts = {label: 0 for label in BTC_LABELS}
        for tx in txs:
            value = sum(out["value"] for out in tx["out"]) / 1e8
            if value >= BTC_BINS[3]:
                counts["100+ BTC"] += value
            elif value >= BTC_BINS[2]:
                counts["10-100 BTC"] += value
            elif value >= BTC_BINS[1]:
                counts["1-10 BTC"] += value
            else:
                counts["0-1 BTC"] += value
        for label in BTC_LABELS:
            prev = btc_data["values"][label][-1] if btc_data["values"][label] else 0
            btc_data["values"][label].append(round(prev + counts[label], 2))
    except Exception as e:
        print("BTC 오류:", e)

def fetch_hbar():
    try:
        r = requests.get(HBAR_API, params={"limit": 10, "order": "desc"}, timeout=10)
        txs = r.json()["transactions"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        hbar_data["timestamps"].append(now)
        counts = {label: 0 for label in HBAR_LABELS}
        for tx in txs:
            if "transfers" in tx:
                value = sum(abs(float(t["amount"])) for t in tx["transfers"]) / 1e8
                if value >= HBAR_BINS[3]:
                    counts["100M+ HBAR"] += value
                elif value >= HBAR_BINS[2]:
                    counts["10M-100M HBAR"] += value
                elif value >= HBAR_BINS[1]:
                    counts["1M-10M HBAR"] += value
                elif value >= HBAR_BINS[0]:
                    counts["100K-1M HBAR"] += value
        for label in HBAR_LABELS:
            prev = hbar_data["values"][label][-1] if hbar_data["values"][label] else 0
            hbar_data["values"][label].append(round(prev + counts[label], 2))
    except Exception as e:
        print("HBAR 오류:", e)

def updater():
    while True:
        fetch_btc()
        fetch_hbar()
        print("⏱ 데이터 업데이트 완료")
        time.sleep(60)

# 백그라운드 스레드 실행
threading.Thread(target=updater, daemon=True).start()

# 라우터 설정
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/btc")
def api_btc():
    return jsonify(btc_data)

@app.route("/api/hbar")
def api_hbar():
    return jsonify(hbar_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
