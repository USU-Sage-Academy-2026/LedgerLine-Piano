// Draws the 2 teacher dashboard charts from the JSON APIs in app/api.py.
async function getJSON(url) {
  const res = await fetch(url);                 // the login cookie is sent automatically (same site)
  if (!res.ok) throw new Error(`${url} returned ${res.status}`);
  return res.json();
}

function baseLayout(el) {
  return {
    height: 260,
    margin: { t: 10, r: 10, b: 40, l: 90 },
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",   // let the card color show through
    font: { family: "Atkinson Hyperlegible Next, sans-serif",
            color: getComputedStyle(document.body).color },
    // .chart has border-color: var(--border) in app.css (no border is drawn); read it for the grid lines
    xaxis: { gridcolor: getComputedStyle(el).borderTopColor },
    yaxis: { gridcolor: getComputedStyle(el).borderTopColor },
  };
}
const CONFIG = { responsive: true, displayModeBar: false };

async function drawStudents() {
  const el = document.getElementById("chart-students");
  const sum = document.getElementById("c1-sum");
  try {
    const rows = await getJSON("/api/teacher/minutes-this-week");
    if (rows.length === 0) { sum.textContent = "No students yet."; return; }
    const top = rows.reduce((a, b) => (b.minutes_this_week > a.minutes_this_week ? b : a));
    sum.textContent = `${top.display_name} practiced most this week (${top.minutes_this_week} min).`;
    Plotly.newPlot(el, [{
      type: "bar", orientation: "h",
      y: rows.map(r => r.display_name),
      x: rows.map(r => r.minutes_this_week),
      marker: { color: getComputedStyle(el).color },
      hovertemplate: "%{y}: %{x} min<extra></extra>",
    }], { ...baseLayout(el), yaxis: { autorange: "reversed", automargin: true } }, CONFIG);
  } catch (err) {
    console.error(err);
    sum.textContent = "Couldn’t load this chart. Refresh the page to try again.";
  }
}

async function drawDaily() {
  const el = document.getElementById("chart-daily");
  const sum = document.getElementById("c2-sum");
  try {
    const rows = await getJSON("/api/teacher/studio-minutes-daily");
    if (rows.length === 0) { sum.textContent = "No minutes logged"; return; }
    const avg = Math.round(rows.reduce((acc, r) => acc + r.total_minutes, 0) / rows.length * 10) / 10;
    sum.textContent = `Studio averaged ${avg} min/day over the past 8 weeks.`;
    Plotly.newPlot(el, [{
      type: "scatter", mode: "lines",
      x: rows.map(r => r.day),
      y: rows.map(r => r.total_minutes),
      fill: "tozeroy",
      line: { color: getComputedStyle(el).color },
      hovertemplate: "%{x|%b %-d}: %{y} min<extra></extra>",
    }], { ...baseLayout(el), margin: { t: 10, r: 10, b: 40, l: 40 } }, CONFIG);
  } catch (err) {
    console.error(err);
    sum.textContent = "Couldn’t load this chart. Refresh the page to try again.";
  }
}

drawStudents();
drawDaily();
// The Light/Dark button (app.js) fires "themechange": redraw so the chart colors follow.
window.addEventListener("themechange", () => { drawStudents(); drawDaily(); });
