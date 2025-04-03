from flask import Flask, render_template, jsonify
from datetime import datetime
import pytz
import random
import requests
import os
import feedparser

app = Flask(__name__)

KST = pytz.timezone('Asia/Seoul')

def get_kst_time():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/indicators")
def api_indicators():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,ripple,hedera-hashgraph",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    res = requests.get(url, params=params)
    data = res.json()

    mock_rsi = lambda: round(random.uniform(40, 70), 1)
    generate_sparkline = lambda: [round(random.uniform(0.9, 1.1), 4) for _ in range(20)]

    return jsonify({
        "BTC": {
            "price": round(data["bitcoin"]["usd"], 2),
            "change": round(data["bitcoin"]["usd_24h_change"], 2),
            "rsi": mock_rsi(),
            "spark": generate_sparkline()
        },
        "ETH": {
            "price": round(data["ethereum"]["usd"], 2),
            "change": round(data["ethereum"]["usd_24h_change"], 2),
            "rsi": mock_rsi(),
            "spark": generate_sparkline()
        },
        "XRP": {
            "price": round(data["ripple"]["usd"], 2),
            "change": round(data["ripple"]["usd_24h_change"], 2),
            "rsi": mock_rsi(),
            "spark": generate_sparkline()
        },
        "HBAR": {
            "price": round(data["hedera-hashgraph"]["usd"], 4),
            "change": round(data["hedera-hashgraph"]["usd_24h_change"], 2),
            "rsi": mock_rsi(),
            "spark": generate_sparkline()
        }
    })

@app.route("/api/news")
def api_news():
    feed = feedparser.parse("https://cointelegraph.com/rss")
    return jsonify([
        {
            "title": entry.title,
            "link": entry.link,
            "published": entry.published
        } for entry in feed.entries[:5]
    ])

@app.route("/api/econ")
def api_econ():
    return jsonify([
        {
            "name": "미국 ISM 비제조업 PMI (3월)",
            "country": "미국",
            "actual": "53.0",
            "forecast": "53.5",
            "previous": "53.5",
            "date": "2025-04-03"
        },
        {
            "name": "미국 ADP 민간고용 (3월)",
            "country": "미국",
            "actual": "155K",
            "forecast": "118K",
            "previous": "84K",
            "date": "2025-04-02"
        },
        {
            "name": "호주 기준금리 (4월)",
            "country": "호주",
            "actual": "4.10%",
            "forecast": "4.10%",
            "previous": "4.10%",
            "date": "2025-04-01"
        },
        {
            "name": "미국 ISM 제조업 PMI (3월)",
            "country": "미국",
            "actual": "49.0",
            "forecast": "49.5",
            "previous": "50.3",
            "date": "2025-04-01"
        },
        {
            "name": "일본 단칸 대형제조업지수 (Q1)",
            "country": "일본",
            "actual": "+12",
            "forecast": "+12",
            "previous": "+14",
            "date": "2025-04-01"
        }
    ])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
