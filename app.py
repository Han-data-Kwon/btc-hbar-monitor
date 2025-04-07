import os
import requests
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from datetime import datetime, timedelta
import feedparser

load_dotenv()
app = Flask(__name__)

# CoinGecko 시세 API
@app.route("/api/price")
def api_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,hedera-hashgraph,ripple",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        res = requests.get(url, params=params).json()
        return jsonify({
            "BTC": {
                "price": round(res["bitcoin"]["usd"], 2),
                "change": round(res["bitcoin"]["usd_24h_change"], 2)
            },
            "ETH": {
                "price": round(res["ethereum"]["usd"], 2),
                "change": round(res["ethereum"]["usd_24h_change"], 2)
            },
            "HBAR": {
                "price": round(res["hedera-hashgraph"]["usd"], 2),
                "change": round(res["hedera-hashgraph"]["usd_24h_change"], 2)
            },
            "XRP": {
                "price": round(res["ripple"]["usd"], 2),
                "change": round(res["ripple"]["usd_24h_change"], 2)
            },
        })
    except Exception as e:
        print("시세 API 오류:", e)
        return jsonify({})

# CoinGecko OHLC 데이터 (1분 단위 시세 차트용)
@app.route("/api/ohlcv/<coin>")
def api_ohlcv(coin):
    try:
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "HBAR": "hedera-hashgraph",
            "XRP": "ripple"
        }
        coin_id = symbol_map.get(coin.upper(), "")
        if not coin_id:
            return jsonify([])

        now = datetime.utcnow()
        timestamps = []
        prices = []
        for i in range(60):
            t = now - timedelta(minutes=59 - i)
            timestamps.append(t.strftime("%Y-%m-%d %H:%M"))
            prices.append(round(25000 + i * 10 + (i % 5) * 50, 2))  # Mock logic

        return jsonify({"labels": timestamps, "prices": prices})
    except Exception as e:
        print("OHLCV 오류:", e)
        return jsonify({})

# RSI 계산 (14일 기준)
@app.route("/api/rsi/<coin>")
def api_rsi(coin):
    try:
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "HBAR": "hedera-hashgraph",
            "XRP": "ripple"
        }
        coin_id = symbol_map.get(coin.upper(), "")
        if not coin_id:
            return jsonify({})

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": "30", "interval": "daily"}
        res = requests.get(url, params=params).json()
        prices = [p[1] for p in res.get("prices", [])]

        def compute_rsi(prices, period=14):
            gains, losses = [], []
            for i in range(1, period + 1):
                diff = prices[i] - prices[i - 1]
                if diff >= 0:
                    gains.append(diff)
                else:
                    losses.append(abs(diff))
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period if losses else 1
            rs = avg_gain / avg_loss
            rsi = [100 - (100 / (1 + rs))]
            for i in range(period + 1, len(prices)):
                diff = prices[i] - prices[i - 1]
                gain = max(diff, 0)
                loss = abs(min(diff, 0))
                avg_gain = (avg_gain * (period - 1) + gain) / period
                avg_loss = (avg_loss * (period - 1) + loss) / period
                rs = avg_gain / avg_loss if avg_loss else 0
                rsi.append(100 - (100 / (1 + rs)) if rs else 100)
            return rsi

        rsi_values = compute_rsi(prices)
        labels = [datetime.utcfromtimestamp(res["prices"][i + 14][0] / 1000).strftime("%Y-%m-%d")
                  for i in range(len(rsi_values))]

        return jsonify({"labels": labels, "values": rsi_values})
    except Exception as e:
        print("RSI 오류:", e)
        return jsonify({})

# CoinTelegraph 뉴스
@app.route("/api/news")
def api_news():
    feed = feedparser.parse("https://cointelegraph.com/rss")
    results = []
    for entry in feed.entries[:8]:
        lower_title = entry.title.lower()
        highlight = "hbar" in lower_title or "hedera" in lower_title or "whale" in lower_title
        image = entry.get("media_content", [{}])[0].get("url", "") if "media_content" in entry else ""
        results.append({
            "title": entry.title,
            "link": entry.link,
            "date": entry.published,
            "summary": entry.summary,
            "image": image,
            "highlight": highlight
        })
    return jsonify(results)

# 경제지표
@app.route("/api/economics")
def api_economics():
    try:
        key = os.environ.get("TRADING_API_KEY", "")
        res = requests.get(f"https://api.tradingeconomics.com/calendar?c={key}").json()
        prev_day = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        filtered = [
            {
                "date": d.get("date", "")[:10],
                "event": d.get("event", ""),
                "country": d.get("country", ""),
                "actual": d.get("actual"),
                "forecast": d.get("forecast"),
                "previous": d.get("previous"),
                "importance": d.get("importance", "")
            }
            for d in res if d.get("date", "").startswith(prev_day)
        ]
        result = sorted(filtered, key=lambda x: x["importance"] == "High", reverse=True)
        return jsonify(result)
    except Exception as e:
        print("경제지표 오류:", e)
        return jsonify([])

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)