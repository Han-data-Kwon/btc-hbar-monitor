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
            "ids": "bitcoin,ethereum,binancecoin,xrp,cardano,solana,dogecoin,avalanche-2,hedera,chainlink",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        res = requests.get(url, params=params).json()
        return jsonify({
            key.upper(): {
                "price": round(res[key]["usd"], 4),
                "change": round(res[key]["usd_24h_change"], 2)
            }
            for key in res
        })
    except Exception as e:
        print("시세 오류:", e)
        return jsonify({})

# --- CoinGecko 시가총액 트리맵용 데이터 ---
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
        return jsonify([
            {"name": coin["symbol"].upper(), "value": coin["market_cap"]}
            for coin in res
        ])
    except Exception as e:
        print("트리맵 오류:", e)
        return jsonify([])

# --- NewsData.io 뉴스 (영어/한글, 특정 키워드 기반) ---
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

# --- FRED 경제지표 (미국 전일~당일 기준) ---
@app.route("/api/economics")
def get_economics():
    try:
        key = os.getenv("FRED_API_KEY")
        now = datetime.utcnow()
        start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")
        url = f"https://api.stlouisfed.org/fred/releases/dates?api_key={key}&file_type=json"
        release_dates = requests.get(url).json()
        releases = []

        for release in release_dates.get("release_dates", []):
            date = release.get("date")
            if start_date <= date <= end_date:
                releases.append({
                    "date": date,
                    "name": release.get("release_name", "N/A")
                })

        return jsonify(sorted(releases, key=lambda x: x["date"], reverse=True))
    except Exception as e:
        print("경제지표 오류:", e)
        return jsonify([])

# --- ClankApp 고래 추적 (공개 API 사용) ---
@app.route("/api/whales")
def get_whales():
    try:
        url = "https://public.clankapp.com/api/v1/alerts"
        res = requests.get(url).json()
        whales = []
        for tx in res.get("alerts", [])[:15]:
            whales.append({
                "time": tx.get("timestamp", "")[:19].replace("T", " "),
                "coin": tx.get("symbol", ""),
                "amount": tx.get("amount", 0),
                "from": tx.get("from", ""),
                "to": tx.get("to", "")
            })
        return jsonify(whales)
    except Exception as e:
        print("고래 데이터 오류:", e)
        return jsonify([])

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)