# app.py 전체 수정본 디버깅 로그 포함 버전 재로드

import os
import requests
from flask import Flask, render_template, jsonify
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
app = Flask(__name__)

BINANCE_API = "https://api.binance.com/api/v3/ticker/24hr"
TE_API_KEY = os.getenv("TRADING_API_KEY")

COINS = {
    "BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT", "XRP": "XRPUSDT", "ADA": "ADAUSDT",
    "SOL": "SOLUSDT", "DOGE": "DOGEUSDT", "AVAX": "AVAXUSDT", "HBAR": "HBARUSDT", "LINK": "LINKUSDT"
}

@app.route("/api/price")
def get_price():
    try:
        res = requests.get(BINANCE_API)
        res.raise_for_status()
        json_data = res.json()
        print("Binance 응답 샘플:", json_data[:3])

        data = {}
        for coin, symbol in COINS.items():
            match = next((item for item in json_data if item["symbol"] == symbol), None)
            if match:
                data[coin] = {
                    "price": round(float(match["lastPrice"]), 4),
                    "change": round(float(match["priceChangePercent"]), 2)
                }
        print("시세 수:", len(data))
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
            headers = {"User-Agent": "Mozilla/5.0"}
            html = requests.get(url, headers=headers).text
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("article")[:3]
            for item in items:
                title = item.select_one("h3, h4")
                link = item.find("a")
                time_tag = item.find("time")
                if title and link and time_tag:
                    articles.append({
                        "title": title.text.strip(),
                        "link": f"https://news.google.com{link['href'][1:]}",
                        "date": time_tag.get("datetime", "")[:10],
                        "summary": f"{kw} 관련 뉴스",
                        "keyword": kw
                    })
        print("뉴스 건수:", len(articles))
        return jsonify(articles)
    except Exception as e:
        print("뉴스 오류:", e)
        return jsonify([])

@app.route("/api/economics")
def get_economics():
    try:
        url = f"https://api.tradingeconomics.com/calendar?importance=high&c={TE_API_KEY}"
        res = requests.get(url)
        res.raise_for_status()
        json_data = res.json()
        print("TE 응답 수:", len(json_data))

        filtered = [dict(
            date=d.get("date", "")[:10],
            event=d.get("event"),
            country=d.get("country"),
            actual=d.get("actual"),
            forecast=d.get("forecast"),
            previous=d.get("previous"),
            importance=d.get("importance")
        ) for d in json_data if d.get("date")]

        sorted_data = sorted(filtered, key=lambda x: x["date"], reverse=True)[:10]
        print("경제지표 수:", len(sorted_data))
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