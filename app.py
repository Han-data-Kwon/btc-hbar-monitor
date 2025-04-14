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

# --- CoinGecko 시가총액 트리맵 데이터 ---
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
            {
                "name": f"{coin['symbol'].upper()} ({coin['name']})",
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

# --- FRED 경제지표 (전일~당일 발표된 지표 + 실제값/설명 포함) ---
@app.route("/api/economics")
def get_economics():
    try:
        key = os.getenv("FRED_API_KEY")
        now = datetime.utcnow()
        start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        # Step 1: release 목록 조회
        releases_url = f"https://api.stlouisfed.org/fred/releases/dates?api_key={key}&file_type=json"
        release_dates = requests.get(releases_url).json()

        result = []
        for r in release_dates.get("release_dates", []):
            date = r.get("date")
            if start_date <= date <= end_date:
                release_name = r.get("release_name", "N/A")

                # Step 2: observations 가져오기 (예시로 CPI 사용)
                if "CPI" in release_name.upper():
                    obs_url = f"https://api.stlouisfed.org/fred/series/observations"
                    obs_params = {
                        "api_key": key,
                        "series_id": "CPIAUCNS",
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": 1
                    }
                    obs_data = requests.get(obs_url, params=obs_params).json()
                    value = obs_data.get("observations", [{}])[0].get("value", "N/A")
                else:
                    value = "N/A"

                result.append({
                    "date": date,
                    "name": release_name,
                    "value": value,
                    "desc": f"{release_name}에 대한 간단 설명입니다."
                })

        return jsonify(sorted(result, key=lambda x: x["date"], reverse=True))
    except Exception as e:
        print("경제지표 오류:", e)
        return jsonify([])

# --- ClankApp 고래 추적 (데이터 없을 시 예외처리) ---
@app.route("/api/whales")
def get_whales():
    try:
        url = "https://public.clankapp.com/api/v1/alerts"
        res = requests.get(url).json()
        whales = []
        alerts = res.get("alerts", [])
        if not alerts:
            print("ClankApp API에 데이터 없음")
        for tx in alerts[:15]:
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