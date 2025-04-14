import os
import requests
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- CoinGecko 시세 데이터 ---
@app.route("/api/price")
def get_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,binancecoin,xrp,cardano,solana,dogecoin,avalanche-2,hedera-hashgraph,chainlink",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        res = requests.get(url, params=params).json()
        return jsonify({
            coin_id.upper(): {
                "price": round(data["usd"], 4),
                "change": round(data["usd_24h_change"], 2)
            }
            for coin_id, data in res.items()
        })
    except Exception as e:
        print("시세 오류:", e)
        return jsonify({})

# --- CoinGecko 시가총액 트리맵 데이터 (비중 % 포함) ---
@app.route("/api/treemap")
def get_treemap():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1
        }
        res = requests.get(url, params=params).json()
        total_market_cap = sum(coin["market_cap"] for coin in res if coin["market_cap"])

        return jsonify([
            {
                "name": f"{coin['symbol'].upper()} ({coin['name']})\n{round(coin['market_cap'] / total_market_cap * 100, 2)}%",
                "value": coin["market_cap"]
            }
            for coin in res
        ])
    except Exception as e:
        print("트리맵 오류:", e)
        return jsonify([])

# --- 뉴스 API (NewsData.io) ---
@app.route("/api/news")
def get_news():
    try:
        key = os.getenv("NEWSDATA_API_KEY")
        keywords = ["Trump", "HBAR", "Bitcoin"]
        articles = []
        for kw in keywords:
            url = f"https://newsdata.io/api/1/news?apikey={key}&q={kw}&language=en,ko"
            res = requests.get(url).json()
            if res.get("results"):
                for item in res["results"][:3]:
                    articles.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "date": item.get("pubDate", "")[:10],
                        "summary": item.get("description", ""),
                        "keyword": kw
                    })
        return jsonify(articles)
    except Exception as e:
        print("뉴스 오류:", e)
        return jsonify([])

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)