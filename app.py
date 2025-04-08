import os
import requests
from flask import Flask, render_template, jsonify
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# CoinGecko API (대안 시세 API)
COINS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "cardano": "ADA",
    "solana": "SOL",
    "dogecoin": "DOGE",
    "avalanche-2": "AVAX",
    "hedera-hashgraph": "HBAR",
    "chainlink": "LINK"
}

@app.route("/api/price")
def get_price():
    try:
        ids = ",".join(COINS.keys())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        res = requests.get(url)
        data = res.json()
        result = {}
        for cid, symbol in COINS.items():
            if cid in data:
                result[symbol] = {
                    "price": data[cid]["usd"],
                    "change": round(data[cid]["usd_24h_change"], 2)
                }
        return jsonify(result)
    except Exception as e:
        print("가격 오류:", e)
        return jsonify({})

@app.route("/api/news")
def get_news():
    try:
        rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"
        rss = requests.get(rss_url).text
        soup = BeautifulSoup(rss, "xml")
        items = soup.find_all("item")[:10]
        results = []
        for item in items:
            results.append({
                "title": item.title.text,
                "link": item.link.text,
                "date": item.pubDate.text,
                "summary": item.description.text
            })
        return jsonify(results)
    except Exception as e:
        print("뉴스 오류:", e)
        return jsonify([])

@app.route("/api/economics")
def get_economics():
    try:
        # Fallback mock economic data
        return jsonify([
            {
                "date": "2025-04-07",
                "event": "미국 기준금리 결정",
                "country": "US",
                "actual": "5.25%",
                "forecast": "5.25%",
                "previous": "5.25%",
                "importance": "High"
            },
            {
                "date": "2025-04-07",
                "event": "실업률",
                "country": "US",
                "actual": "3.8%",
                "forecast": "3.9%",
                "previous": "3.8%",
                "importance": "Medium"
            }
        ])
    except Exception as e:
        print("경제지표 오류:", e)
        return jsonify([])

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)