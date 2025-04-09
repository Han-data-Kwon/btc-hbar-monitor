import os
import requests
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

COINGECKO_PRICE_API = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_MARKET_API = "https://api.coingecko.com/api/v3/coins/markets"
TE_API_KEY = os.getenv("TRADING_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

TOP_COINS = [
    "bitcoin", "ethereum", "binancecoin", "ripple", "cardano",
    "solana", "dogecoin", "avalanche-2", "hedera-hashgraph", "chainlink"
]

@app.route("/api/price")
def get_price():
    try:
        ids = ",".join(TOP_COINS)
        res = requests.get(f"{COINGECKO_PRICE_API}?ids={ids}&vs_currencies=usd&include_24hr_change=true").json()
        data = {}
        for coin in TOP_COINS:
            coin_key = coin.upper() if coin != "hedera-hashgraph" else "HBAR"
            data[coin_key] = {
                "price": round(res[coin]["usd"], 4),
                "change": round(res[coin]["usd_24h_change"], 2)
            }
        return jsonify(data)
    except Exception as e:
        print("시세 오류:", e)
        return jsonify({})

@app.route("/api/treemap")
def get_treemap():
    try:
        res = requests.get(f"{COINGECKO_MARKET_API}?vs_currency=usd&order=market_cap_desc&per_page=50&page=1").json()
        data = [{"name": coin["symbol"].upper(), "value": coin["market_cap"]} for coin in res]
        return jsonify(data)
    except Exception as e:
        print("트리맵 오류:", e)
        return jsonify([])

@app.route("/api/news")
def get_news():
    try:
        keywords = ["Trump", "HBAR", "Bitcoin"]
        articles = []
        for kw in keywords:
            url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={kw}&language=en,ko"
            res = requests.get(url).json()
            for item in res.get("results", [])[:3]:
                articles.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "date": item.get("pubDate", "")[:10],
                    "source": item.get("source_id", ""),
                    "keyword": kw
                })
        return jsonify(articles)
    except Exception as e:
        print("뉴스 오류:", e)
        return jsonify([])

@app.route("/api/economics")
def get_economics():
    try:
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)
        start_date = yesterday.strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        url = f"https://api.tradingeconomics.com/calendar/country/united states?c={TE_API_KEY}&d1={start_date}&d2={end_date}"
        res = requests.get(url).json()
        data = [
            {
                "date": d.get("date", "")[:10],
                "event": d.get("event", ""),
                "country": d.get("country", ""),
                "actual": d.get("actual"),
                "forecast": d.get("forecast"),
                "previous": d.get("previous")
            }
            for d in res if d.get("event")
        ]
        sorted_data = sorted(data, key=lambda x: x["date"], reverse=True)
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