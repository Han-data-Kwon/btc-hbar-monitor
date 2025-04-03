<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>🐋 고래 모니터링 대시보드</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {
      font-family: 'Segoe UI', sans-serif;
      background-color: white;
      color: black;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #1e1e1e;
      color: white;
    }
    button { margin: 6px; padding: 8px 12px; font-weight: bold; }
    .tab { display: none; }
    .tab.active { display: block; }
    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
    th, td { border: 1px solid #ccc; padding: 6px; text-align: center; font-size: 14px; }
    th { background-color: #f0f0f0; }
    .dark-mode th { background-color: #444; }
    .buy { color: red; font-weight: bold; }
    .sell { color: blue; font-weight: bold; }
    .highlight { background-color: yellow; font-weight: bold; }
    .sparkline { height: 40px; }
  </style>
</head>
<body>
  <h1>🐋 고래 모니터링 대시보드</h1>

  <!-- 📌 탭 -->
  <div>
    <button onclick="showTab('price')">💰 시세</button>
    <button onclick="showTab('news')">📰 뉴스</button>
    <button onclick="showTab('econ')">📅 경제지표</button>
    <button onclick="showTab('whales')">🐋 고래 거래</button>
    <button onclick="toggleDarkMode()">🌙 다크모드</button>
  </div>

  <!-- 💰 시세 -->
  <div id="price" class="tab active">
    <h2>💰 실시간 시세</h2>
    <div id="priceCards"></div>
  </div>

  <!-- 📰 뉴스 -->
  <div id="news" class="tab">
    <h2>📰 Cointelegraph 뉴스</h2>
    <div id="newsList"></div>
  </div>

  <!-- 📅 경제지표 -->
  <div id="econ" class="tab">
    <h2>📅 주요 경제지표</h2>
    <table>
      <thead>
        <tr><th>날짜</th><th>지표명</th><th>국가</th><th>해석</th></tr>
      </thead>
      <tbody id="econBody"></tbody>
    </table>
  </div>

  <!-- 🐋 고래 거래 -->
  <div id="whales" class="tab">
    <h2>🐳 BTC 고래 거래</h2>
    <table>
      <thead>
        <tr><th>시간</th><th>From</th><th>To</th><th>수량</th><th>구간</th><th>방향</th></tr>
      </thead>
      <tbody id="btcTable"></tbody>
    </table>

    <h2>🧊 HBAR 고래 거래</h2>
    <table>
      <thead>
        <tr><th>시간</th><th>From</th><th>To</th><th>수량</th><th>구간</th><th>방향</th></tr>
      </thead>
      <tbody id="hbarTable"></tbody>
    </table>
  </div>

  <script>
    function showTab(id) {
      document.querySelectorAll(".tab").forEach(el => el.classList.remove("active"));
      document.getElementById(id).classList.add("active");
    }

    function toggleDarkMode() {
      document.body.classList.toggle("dark-mode");
    }

    async function loadPrices() {
      try {
        const res = await fetch('/api/price');
        const data = await res.json();
        const el = document.getElementById("priceCards");
        el.innerHTML = Object.keys(data).map(key => `
          <div>
            <h3>${key}</h3>
            <p>💲 ${data[key].price.toLocaleString()} USD</p>
            <p>📉 변화율: ${data[key].change}%</p>
          </div>
        `).join('');
      } catch (e) {
        console.error("가격 로딩 실패", e);
      }
    }

    async function loadNews() {
      const res = await fetch("/api/news");
      const news = await res.json();
      const el = document.getElementById("newsList");
      el.innerHTML = news.map(n => `
        <div style="margin-bottom:10px;">
          <a href="${n.link}" target="_blank"><strong>${n.title}</strong></a><br/>
          발행일: ${n.date}<br/>
          <em>${n.summary}</em>
        </div>
      `).join('');
    }

    async function loadEconomics() {
      const res = await fetch("/api/economics");
      const econ = await res.json();
      const el = document.getElementById("econBody");
      el.innerHTML = econ.map(e => `
        <tr>
          <td>${e.date}</td>
          <td>${e.event}</td>
          <td>${e.country}</td>
          <td>${e.effect}</td>
        </tr>
      `).join('');
    }

    async function loadWhales() {
      const btcRes = await fetch("/api/btc_trades");
      const hbarRes = await fetch("/api/hbar_trades");
      const btc = await btcRes.json();
      const hbar = await hbarRes.json();

      document.getElementById("btcTable").innerHTML = btc.map(d => `
        <tr>
          <td>${d.time}</td>
          <td class="${isExchange(d.from) ? 'highlight' : ''}">${d.from}</td>
          <td class="${isExchange(d.to) ? 'highlight' : ''}">${d.to}</td>
          <td>${d.amount}</td>
          <td>${d.type}</td>
          <td class="${d.direction === '매수' ? 'buy' : 'sell'}">${d.direction}</td>
        </tr>
      `).join('');

      document.getElementById("hbarTable").innerHTML = hbar.map(d => `
        <tr>
          <td>${d.time}</td>
          <td class="${isExchange(d.from) ? 'highlight' : ''}">${d.from}</td>
          <td class="${isExchange(d.to) ? 'highlight' : ''}">${d.to}</td>
          <td>${d.amount}</td>
          <td>${d.type}</td>
          <td class="${d.direction === '매수' ? 'buy' : 'sell'}">${d.direction}</td>
        </tr>
      `).join('');
    }

    function isExchange(addr) {
      return ['binance_wallet', 'upbit_wallet', 'coinbase_wallet'].includes(addr);
    }

    async function loadAll() {
      await loadPrices();
      await loadNews();
      await loadEconomics();
      await loadWhales();
    }

    loadAll();
    setInterval(loadAll, 30000);
  </script>
</body>
</html>