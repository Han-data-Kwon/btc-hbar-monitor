from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import random  # 실제 API 대신 예시용

app = Flask(__name__)

btc_data = []
hbar_data = []

MAX_POINTS = 60  # 30초 단위로 30분 = 60개 포인트
KST = pytz.timezone('Asia/Seoul')

def get_mock_data():
    return {
        "0-1": random.randint(0, 100),
        "1-10": random.randint(0, 10),
        "10-100": random.randint(0, 5),
        "100+": random.randint(0, 2)
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/btc")
def api_btc():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    data = get_mock_data()
    btc_data.append({"time": now, "data": data})
    if len(btc_data) > MAX_POINTS:
        btc_data.pop(0)
    return jsonify(btc_data)

@app.route("/api/hbar")
def api_hbar():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    data = get_mock_data()
    hbar_data.append({"time": now, "data": data})
    if len(hbar_data) > MAX_POINTS:
        hbar_data.pop(0)
    return jsonify(hbar_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

