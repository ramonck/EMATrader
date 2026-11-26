"use strict";

const translations = {
  pt: { locale: "pt-BR", title: "EMA Trader · Perpétuos na Lighter", resume: "Retomar animação" },
  en: {
    locale: "en", title: "EMA Trader · Lighter perpetuals", skip: "Skip to content", navLabel: "Sections", languageLabel: "Language",
    navStrategy: "Strategy", navResults: "Backtest", navCode: "Source code", eyebrow: "OPEN SOURCE · LIGHTER",
    heroFirst: "Read the trend.", heroSecond: "Trade on Lighter.",
    intro: "Monitor perpetuals with the 15-minute EMA band. Follow the signals or enable automatic orders in your Lighter account.",
    download: "Download EMA Trader", learn: "Explore the strategy", platforms: "Windows and macOS desktop · Linux command line",
    chartTime: "15-minute candles", chartLabel: "Illustrative candlesticks with an EMA band", chartBand: "EMA band", chartCaption: "Illustrative data",
    pause: "Pause animation", resume: "Resume animation", signalLabel: "STRATEGY", strategyHeading: "How the bot decides",
    ruleA: "Identifies direction", ruleAText: "Calculates an EMA band from Heikin Ashi highs and lows. A neutral band preserves the previous direction.",
    ruleB: "Confirms the short exit", ruleBText: "A turn to long requires a bullish trend on the last closed hourly candle and a real 15-minute close above its open and the upper band.",
    ruleC: "Executes on Lighter", ruleCText: "Long-to-short follows the 15-minute band. With automation enabled, the bot confirms the close before opening the opposite side.",
    resultLabel: "BACKTEST · LIGHTER MAINNET", resultHeading: "Six months of BTC perpetuals",
    resultText: "May 24 to November 24, 2026. $100 initial equity, 10× leverage, reinvestment and a 0.05% simulated cost per side. The account loss limit was disabled.",
    method: "See the assumptions and replay", roi: "Simulated ROI", roiNumber: "+454.91%", drawdown: "Maximum drawdown", drawdownNumber: "82.04%", trades: "Closed trades",
    modelNote: "The simulation uses only Lighter data and candle opening prices. Funding, slippage and liquidation are outside the model.",
    startHeading: "From charts to execution", startText: "Install the app, set up Lighter and explore the bot’s rules.", docs: "Open the documentation",
    footer: "Open-source project for educational use.", risk: "Risk notice",
  },
  es: {
    locale: "es", title: "EMA Trader · Perpetuos en Lighter", skip: "Ir al contenido", navLabel: "Secciones", languageLabel: "Idioma",
    navStrategy: "Estrategia", navResults: "Backtest", navCode: "Código", eyebrow: "CÓDIGO ABIERTO · LIGHTER",
    heroFirst: "Lee la tendencia.", heroSecond: "Opera en Lighter.",
    intro: "Sigue contratos perpetuos con la banda EMA de 15 minutos. Consulta las señales o activa órdenes automáticas en tu cuenta de Lighter.",
    download: "Descargar EMA Trader", learn: "Conocer la estrategia", platforms: "Interfaz en Windows y macOS · Linux por terminal",
    chartTime: "Velas de 15 min", chartLabel: "Velas ilustrativas con banda EMA", chartBand: "Banda EMA", chartCaption: "Datos ilustrativos",
    pause: "Pausar animación", resume: "Reanudar animación", signalLabel: "ESTRATEGIA", strategyHeading: "Cómo decide el robot",
    ruleA: "Identifica la dirección", ruleAText: "Calcula la banda EMA de máximos y mínimos Heikin Ashi. La banda neutral conserva la dirección anterior.",
    ruleB: "Confirma la salida del short", ruleBText: "El giro a long exige tendencia alcista en la última hora cerrada y cierre real de 15 min por encima de la apertura y de la banda superior.",
    ruleC: "Ejecuta en Lighter", ruleCText: "El giro de long a short sigue la banda de 15 min. Con la automatización activa, el robot confirma el cierre antes de abrir el lado contrario.",
    resultLabel: "BACKTEST · LIGHTER MAINNET", resultHeading: "Seis meses de BTC perpetuo",
    resultText: "Del 24 de mayo al 24 de noviembre de 2026. Saldo inicial de US$ 100, apalancamiento de 10×, reinversión y coste simulado del 0,05% por lado. El límite de pérdida estuvo desactivado.",
    method: "Ver supuestos y reproducción", roi: "ROI simulado", roiNumber: "+454,91%", drawdown: "Caída máxima", drawdownNumber: "82,04%", trades: "Operaciones cerradas",
    modelNote: "La simulación usa solo datos de Lighter y precios de apertura de velas. El funding, el deslizamiento y la liquidación quedan fuera del modelo.",
    startHeading: "Del gráfico a la ejecución", startText: "Instala la aplicación, configura Lighter y consulta las reglas del robot.", docs: "Abrir la documentación",
    footer: "Proyecto de código abierto para uso educativo.", risk: "Aviso de riesgos",
  },
};

const textElements = [...document.querySelectorAll("[data-i]")];
const ariaElements = [...document.querySelectorAll("[data-aria]")];
const originals = new Map(textElements.map(element => [element.dataset.i, element.textContent]));
const originalAria = new Map(ariaElements.map(element => [element.dataset.aria, element.getAttribute("aria-label")]));
const languageButtons = [...document.querySelectorAll("[data-language]")];
const canvas = document.querySelector("#chart");
const context = canvas.getContext("2d");
const motionButton = document.querySelector("#motion");
const prefersReduced = matchMedia("(prefers-reduced-motion: reduce)");
const docsRoot = "https://github.com/ramonck/EMATrader/blob/main/knowledge";
let language = "pt";
let paused = prefersReduced.matches;
let frame = null;
let lastFrame = 0;
let elapsed = 0;

function setLanguage(next) {
  if (!Object.hasOwn(translations, next)) return;
  language = next;
  const strings = translations[next];
  document.documentElement.lang = strings.locale;
  document.title = strings.title;
  for (const element of textElements) element.textContent = strings[element.dataset.i] ?? originals.get(element.dataset.i);
  for (const element of ariaElements) element.setAttribute("aria-label", strings[element.dataset.aria] ?? originalAria.get(element.dataset.aria));
  for (const button of languageButtons) button.setAttribute("aria-pressed", String(button.dataset.language === next));
  for (const link of document.querySelectorAll("[data-doc]")) link.href = `${docsRoot}/${next}/${link.dataset.doc}.md`;
  const url = new URL(location.href);
  url.searchParams.set("lang", next);
  history.replaceState(null, "", url);
  updateMotion();
  draw();
}

for (const button of languageButtons) button.addEventListener("click", () => setLanguage(button.dataset.language));

const candles = [];
let rolling = 60500;
for (let i = 0; i < 43; i++) {
  const trend = i < 14 ? -6 * i : i < 25 ? -84 + (i - 14) * 8 : 4 + (i - 25) * 12;
  const close = 60530 + trend + Math.sin(i * .61) * 28 + Math.cos(i * 1.83) * 14;
  const open = candles.at(-1)?.close ?? 60545;
  rolling += (close - rolling) * .16;
  candles.push({ open, close, low: Math.min(open, close) - 8 - (i * 7) % 16,
    high: Math.max(open, close) + 6 + (i * 11) % 17, band: rolling });
}

function draw() {
  if (!context) return;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (!width || !height) return;
  const ratio = Math.min(devicePixelRatio || 1, 2);
  if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
  }
  const ctx = context;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const left = 13, right = width - 67, top = 16, bottom = height - 26;
  const y = value => top + (60785 - value) * (bottom - top) / 415;
  const step = (right - left) / candles.length;
  const x = i => left + (i + .5) * step;
  const number = new Intl.NumberFormat(translations[language].locale);
  ctx.font = "12px 'IBM Plex Mono', monospace";
  ctx.textBaseline = "middle";
  ctx.lineWidth = 1;
  for (let row = 0; row < 5; row++) {
    const value = 60750 - row * 85;
    ctx.strokeStyle = "#263b50";
    ctx.beginPath(); ctx.moveTo(left, y(value)); ctx.lineTo(right, y(value)); ctx.stroke();
    ctx.fillStyle = "#9cb3cd"; ctx.fillText(number.format(value), right + 5, y(value));
  }
  const times = width > 430 ? [0, 1, 2, 3, 4] : [0, 2, 4];
  for (const column of times) {
    const at = left + (right - left) * column / 4;
    ctx.strokeStyle = "#22364a";
    ctx.beginPath(); ctx.moveTo(at, top); ctx.lineTo(at, bottom); ctx.stroke();
    ctx.fillStyle = "#9cb3cd"; ctx.fillText(`${String(8 + 2 * column).padStart(2, "0")}:00`, at - Math.min(column, 1) * 17, height - 12);
  }

  const gradient = ctx.createLinearGradient(left, 0, right, 0);
  gradient.addColorStop(0, "#ad507b66"); gradient.addColorStop(.43, "#3973a681"); gradient.addColorStop(1, "#2d9d7780");
  ctx.fillStyle = gradient;
  ctx.beginPath();
  candles.forEach((candle, i) => i ? ctx.lineTo(x(i), y(candle.band + 13)) : ctx.moveTo(x(i), y(candle.band + 13)));
  for (let i = candles.length - 1; i >= 0; --i) ctx.lineTo(x(i), y(candles[i].band - 20));
  ctx.closePath(); ctx.fill();
  const last = candles.length - 1;
  candles.forEach((candle, i) => {
    const drift = i === last ? Math.sin(elapsed / 750) * 8 : 0;
    const close = candle.close + drift;
    ctx.fillStyle = ctx.strokeStyle = close >= candle.open ? "#62f3c1" : "#ff819c";
    ctx.beginPath(); ctx.moveTo(x(i), y(candle.low)); ctx.lineTo(x(i), y(candle.high + Math.max(0, drift))); ctx.stroke();
    ctx.fillRect(x(i) - step * .28, y(Math.max(candle.open, close)), step * .56, Math.max(1.5, Math.abs(y(candle.open) - y(close))));
  });
  const priceY = y(candles[last].close + Math.sin(elapsed / 750) * 8);
  ctx.strokeStyle = "#63efc28c";
  ctx.setLineDash([4, 4]); ctx.beginPath(); ctx.moveTo(left, priceY); ctx.lineTo(right, priceY); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = "#62f3c1";
  ctx.beginPath(); ctx.arc(x(last), priceY, 3 + .7 * Math.sin(elapsed / 400), 0, Math.PI * 2); ctx.fill();
}

function animate(now) {
  if (lastFrame && now - lastFrame < 30) { frame = requestAnimationFrame(animate); return; }
  if (lastFrame) elapsed += Math.min(now - lastFrame, 80);
  lastFrame = now;
  draw();
  frame = requestAnimationFrame(animate);
}

function updateMotion() {
  motionButton.textContent = paused ? translations[language].resume : translations[language].pause ?? originals.get("pause");
  motionButton.disabled = !context;
  if (paused || document.hidden || !context) {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
    lastFrame = 0;
    return;
  }
  if (frame === null) frame = requestAnimationFrame(animate);
}

motionButton.addEventListener("click", () => { paused = !paused; updateMotion(); });
prefersReduced.addEventListener("change", event => { paused = event.matches; updateMotion(); });
document.addEventListener("visibilitychange", updateMotion);
new ResizeObserver(draw).observe(canvas.parentElement);
const requestedLanguage = new URLSearchParams(location.search).get("lang");
if (requestedLanguage && Object.hasOwn(translations, requestedLanguage)) setLanguage(requestedLanguage);
else { updateMotion(); draw(); }
