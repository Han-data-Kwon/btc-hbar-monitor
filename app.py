# app.py
import os
import requests
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)

BINANCE_API = "https://api.binance.com/api/v3/ticker/24hr"
TE_API_KEY = os.getenv("TRADING_API_KEY")

# 주요 10대 코인 리스트
COINS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "XRP": "XRPUSDT",
    "ADA": "ADAUSDT",
    "SOL": "SOLUSDT",
    "DOGE": "DOGEUSDT",
    "AVAX": "AVAXUSDT",
    "HBAR": "HBARUSDT",
    "LINK": "LINKUSDT"
}

@app.route("/api/price")
def get_price():
    try:
        res = requests.get(BINANCE_API, timeout=5).json()
        data = {}
        for coin, symbol in COINS.items():
            match = next((item for item in res if item["symbol"] == symbol), None)
            if match:
                data[coin] = {
                    "price": round(float(match["lastPrice"]), 4),
                    "change": round(float(match["priceChangePercent"]), 2)
                }
        return jsonify(data)
    except Exception as e:
        print("시세 오류:", e)
        return jsonify({})

@app.route("/api/news")
def get_news():
    try:
        keywords = ["헤데라", "비트코인", "암호화폐", "트럼프"]
        articles = []
        for kw in keywords:
            url = f"https://news.google.com/search?q={kw}&hl=ko&gl=KR&ceid=KR:ko"
            html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).text
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("article")[:3]
            for item in items:
                title = item.select_one("h3, h4")
                link = item.find("a")
                time_tag = item.find("time")
                if title and link and time_tag:
                    articles.append({
                        "title": title.text.strip(),
                        "link": f'https://news.google.com{link["href"][1:]}',
                        "date": time_tag.get("datetime", "")[:10],
                        "summary": f"{kw} 관련 뉴스",
                        "keyword": kw
                    })
        return jsonify(articles)
    except Exception as e:
        print("뉴스 오류:", e)
        return jsonify([])

@app.route("/api/economics")
def get_economics():
    try:
        url = f"https://api.tradingeconomics.com/calendar?importance=high&c={TE_API_KEY}"
        res = requests.get(url, timeout=5).json()
        filtered = [
            {
                "date": d.get("date", "")[:10],
                "event": d.get("event"),
                "country": d.get("country"),
                "actual": d.get("actual"),
                "forecast": d.get("forecast"),
                "previous": d.get("previous"),
                "importance": d.get("importance")
            }
            for d in res if d.get("date")
        ]
        sorted_data = sorted(filtered, key=lambda x: x["date"], reverse=True)[:10]
        return jsonify(sorted_data)
    except Exception as e:
        print("경제지표 오류:", e)
        return jsonify([])

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)