const metricsUrl = "../data/processed/dashboard_metrics.json";
const colors = ["#e50914", "#18b6d9", "#f7b955", "#39c980"];

const formatNumber = new Intl.NumberFormat("en", {
  maximumFractionDigits: 1,
});

function kpi(label, value) {
  return `<div class="kpi"><span>${label}</span><strong>${value}</strong></div>`;
}

function renderKpis(data) {
  const k = data.kpis;
  document.querySelector("#kpis").innerHTML = [
    kpi("Total titles", k.totalTitles),
    kpi("Movies", k.movies),
    kpi("TV shows", k.tvShows),
    kpi("Views", `${formatNumber.format(k.totalViewsMillions)}M`),
    kpi("Countries", k.countries),
    kpi("Genres", k.genres),
    kpi("Avg completion", `${Math.round(k.avgCompletionRate * 100)}%`),
    kpi("Avg movie length", `${k.avgMovieDurationMinutes}m`),
  ].join("");
}

function renderTrend(items) {
  const maxTotal = Math.max(...items.map((item) => item.total));
  document.querySelector("#releaseTrend").innerHTML = items
    .map((item) => {
      const movieHeight = (item.movies / maxTotal) * 210;
      const showHeight = (item.tvShows / maxTotal) * 210;
      return `
        <div class="trend-column" title="${item.year}: ${item.total} titles">
          <div class="stack">
            <div class="movie-bar" style="height: ${movieHeight}px"></div>
            <div class="show-bar" style="height: ${showHeight}px"></div>
          </div>
          <div class="trend-label">${item.year}</div>
        </div>
      `;
    })
    .join("");
}

function renderContentMix(items) {
  const total = items.reduce((sum, item) => sum + item.count, 0);
  let cursor = 0;
  const stops = items.map((item, index) => {
    const start = cursor;
    cursor += (item.count / total) * 360;
    return `${colors[index]} ${start}deg ${cursor}deg`;
  });
  document.querySelector("#contentDonut").style.background = `conic-gradient(${stops.join(", ")})`;
  document.querySelector("#contentLegend").innerHTML = items
    .map(
      (item, index) => `
        <div class="legend-row">
          <span><i class="swatch" style="background:${colors[index]}"></i>${item.name}</span>
          <strong>${item.count}</strong>
        </div>
      `,
    )
    .join("");
}

function renderBars(selector, items) {
  const max = Math.max(...items.map((item) => item.count));
  document.querySelector(selector).innerHTML = items
    .map(
      (item) => `
        <div class="bar-row">
          <div class="bar-meta"><span>${item.name}</span><strong>${item.count}</strong></div>
          <div class="bar-track"><div class="bar-fill" style="width:${(item.count / max) * 100}%"></div></div>
        </div>
      `,
    )
    .join("");
}

function renderRatings(items) {
  document.querySelector("#ratings").innerHTML = items
    .map((item) => `<div class="rating-chip"><span>${item.rating}</span><strong>${item.count}</strong></div>`)
    .join("");
}

function renderTopTitles(items) {
  document.querySelector("#topTitles").innerHTML = items
    .map(
      (item) => `
        <tr>
          <td>${item.title}</td>
          <td>${item.type}</td>
          <td>${item.country}</td>
          <td>${item.releaseYear}</td>
          <td>${formatNumber.format(item.viewsMillions)}M</td>
          <td>${Math.round(item.completionRate * 100)}%</td>
        </tr>
      `,
    )
    .join("");
}

async function boot() {
  const response = await fetch(metricsUrl);
  if (!response.ok) {
    throw new Error(`Could not load ${metricsUrl}`);
  }
  const data = await response.json();
  document.querySelector("#generatedAt").textContent = `Updated ${new Date(data.generatedAt).toLocaleString()}`;
  renderKpis(data);
  renderTrend(data.releaseTrend);
  renderContentMix(data.contentType);
  renderBars("#genres", data.genres);
  renderBars("#countries", data.countries);
  renderRatings(data.ratings);
  renderTopTitles(data.topTitles);
}

boot().catch((error) => {
  document.body.innerHTML = `<main><section class="panel"><h1>Dashboard data unavailable</h1><p>${error.message}</p></section></main>`;
});
