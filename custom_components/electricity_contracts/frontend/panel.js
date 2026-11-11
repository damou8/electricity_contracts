// The Contracts page of Electricity Contracts: compares the contracts over a
// period, from the statistics the integration writes.

const DOMAIN = "electricity_contracts";
const SVG_NS = "http://www.w3.org/2000/svg";
const DAY_MS = 86400000;
const SERIES_SLOTS = 8;
// Series of what the contracts in force cost.
const ACTUAL = "actual";

const STRINGS = {
  en: {
    title: "Contracts",
    tabActual: "Actual cost",
    tabBill: "Phantom bill",
    currentContract: "Current contract",
    regulated: "regulated prices",
    manualPrices: "prices entered by hand",
    since: "since {date}",
    offPeakHours: "off-peak {ranges}",
    weekendOffPeak: "weekends off-peak",
    pricesSince: "Prices in force since {date}",
    noPrices: "No price is known for this contract.",
    sincePrevious: "{change} vs previous prices",
    more: "Show more",
    less: "Show less",
    noContractInForce: "Set when your contract started (in the contract's settings) to see what you paid.",
    ofWhichSubscription: "of which {amount} of subscription",
    withoutSubscription: "subscription excluded",
    rolling: "Last 12 months",
    year: "Year",
    month: "Month",
    custom: "Custom",
    previous: "Previous",
    next: "Next",
    from: "From",
    to: "To",
    window: "{start} to {end}",
    windowEnergy: "{window} · {energy}",
    noData: "No data for this period.",
    noEntry:
      "No consumption source is set up yet. Add the Electricity Contracts integration first.",
    noContract: "Add a contract to the integration to compare it here.",
    loadFailed: "Loading failed: {error}",
    actualCost: "Actual cost",
    costOverTime: "Cost over time",
    costPerMonth: "Total cost per month",
    costPerDay: "Total cost per day",
    cumulativeHint:
      "Compared with the actual cost: above zero, the contract would have cost less.",
    partialActual:
      "No contract was in force on part of the period: those days are left out.",
    tranches: "Split by tranche",
    tranchesHint: "Where the kWh and the euros go",
    chart: "Chart",
    table: "Table",
    period: "Period",
    actual: "Actual cost",
    tranche: "Tranche",
    energy: "Energy",
    cost: "Cost",
    average: "Average price",
    billIntro: "What a contract would have billed over the period, against what you actually paid.",
    contract: "Contract",
    compute: "Compute",
    computing: "Computing…",
    cumulativeOf: "Cumulative saving with {name}",
    pricesFrom: "Prices from {start} to {end}",
    item: "Item",
    quantity: "Quantity",
    unitPrice: "Unit price",
    amount: "Amount",
    subscription: "Subscription",
    subscriptionYear: "{amount}/year",
    days: "{count} days",
    consumption: "Consumption",
    total: "Total incl. taxes",
    actualPaid: "Actual cost over the period",
    difference: "Difference",
    moreExpensive: "{amount} more than the actual cost",
    cheaper: "{amount} less than the actual cost",
    same: "Same as the actual cost",
  },
  fr: {
    title: "Contrats",
    tabActual: "Coût réel",
    tabBill: "Facture fantôme",
    currentContract: "Contrat en cours",
    regulated: "tarif réglementé",
    manualPrices: "prix saisis à la main",
    since: "depuis le {date}",
    offPeakHours: "heures creuses {ranges}",
    weekendOffPeak: "week-end en heures creuses",
    pricesSince: "Prix en vigueur depuis le {date}",
    noPrices: "Aucun prix n'est connu pour ce contrat.",
    sincePrevious: "{change} vs prix précédents",
    more: "Voir plus",
    less: "Voir moins",
    noContractInForce: "Indiquez le début de votre contrat (dans les réglages du contrat) pour voir ce que vous avez payé.",
    ofWhichSubscription: "dont {amount} d'abonnement",
    withoutSubscription: "hors abonnement",
    rolling: "12 derniers mois",
    year: "Année",
    month: "Mois",
    custom: "Personnalisée",
    previous: "Précédent",
    next: "Suivant",
    from: "Du",
    to: "Au",
    window: "Du {start} au {end}",
    windowEnergy: "{window} · {energy}",
    noData: "Pas de données sur cette période.",
    noEntry:
      "Aucune source de consommation n'est configurée. Ajoutez d'abord l'intégration Electricity Contracts.",
    noContract: "Ajoutez un contrat à l'intégration pour le comparer ici.",
    loadFailed: "Le chargement a échoué : {error}",
    actualCost: "Coût réel",
    costOverTime: "Coût dans le temps",
    costPerMonth: "Coût total par mois",
    costPerDay: "Coût total par jour",
    cumulativeHint:
      "Par rapport au coût réel : au-dessus de zéro, le contrat aurait coûté moins cher.",
    partialActual:
      "Aucun contrat n'était en vigueur sur une partie de la période : ces jours sont laissés de côté.",
    tranches: "Répartition par tranche",
    tranchesHint: "Où vont les kWh et les euros",
    chart: "Graphique",
    table: "Tableau",
    period: "Période",
    actual: "Coût réel",
    tranche: "Tranche",
    energy: "Énergie",
    cost: "Coût",
    average: "Prix moyen",
    billIntro: "Ce qu'un contrat vous aurait facturé sur la période, comparé à ce que vous avez payé.",
    contract: "Contrat",
    compute: "Calculer",
    computing: "Calcul…",
    cumulativeOf: "Économie cumulée avec {name}",
    pricesFrom: "Prix du {start} au {end}",
    item: "Libellé",
    quantity: "Quantité",
    unitPrice: "Prix unitaire",
    amount: "Montant",
    subscription: "Abonnement",
    subscriptionYear: "{amount}/an",
    days: "{count} jours",
    consumption: "Consommation",
    total: "Total TTC",
    actualPaid: "Coût réel sur la période",
    difference: "Différence",
    moreExpensive: "{amount} de plus que le coût réel",
    cheaper: "{amount} de moins que le coût réel",
    same: "Identique au coût réel",
  },
};

const KINDS = {
  en: { base: "Base", hphc: "Peak / off-peak", tempo: "Tempo" },
  fr: { base: "Base", hphc: "Heures pleines / creuses", tempo: "Tempo" },
};

const TRANCHES = {
  en: {
    base: "Base",
    hc: "Off-peak",
    hp: "Peak",
    blue_hc: "Blue off-peak",
    blue_hp: "Blue peak",
    white_hc: "White off-peak",
    white_hp: "White peak",
    red_hc: "Red off-peak",
    red_hp: "Red peak",
  },
  fr: {
    base: "Base",
    hc: "Heures creuses",
    hp: "Heures pleines",
    blue_hc: "Bleu HC",
    blue_hp: "Bleu HP",
    white_hc: "Blanc HC",
    white_hp: "Blanc HP",
    red_hc: "Rouge HC",
    red_hp: "Rouge HP",
  },
};

// Tempo tranches keep their day's color; off-peak is the lighter step.
// Text inside a block takes the ink its fill needs.
const TRANCHE_FILLS = {
  base: ["#5598e7", "#0b0b0b"],
  hc: ["#6da7ec", "#0b0b0b"],
  hp: ["#1c5cab", "#ffffff"],
  blue_hc: ["#6da7ec", "#0b0b0b"],
  blue_hp: ["#1c5cab", "#ffffff"],
  white_hc: ["#b3b2aa", "#0b0b0b"],
  white_hp: ["#7a7974", "#ffffff"],
  red_hc: ["#ee7f7d", "#0b0b0b"],
  red_hp: ["#b8292a", "#ffffff"],
};

const STYLE = `
:host {
  display: block;
  min-height: 100vh;
  background: var(--primary-background-color);
  color: var(--primary-text-color);
  font-family: var(--ha-font-family-body, system-ui, -apple-system, "Segoe UI", sans-serif);
  --ec-surface: var(--card-background-color, #ffffff);
  --ec-text: var(--primary-text-color, #0b0b0b);
  --ec-text-2: var(--secondary-text-color, #52514e);
  --ec-muted: #898781;
  --ec-grid: #e1e0d9;
  --ec-axis: #c3c2b7;
  --ec-wash: rgba(11, 11, 11, 0.05);
  --ec-ring: rgba(11, 11, 11, 0.1);
  --ec-s1: #2a78d6;
  --ec-s2: #eb6834;
  --ec-s3: #1baf7a;
  --ec-s4: #eda100;
  --ec-s5: #e87ba4;
  --ec-s6: #008300;
  --ec-s7: #6250d6;
  --ec-s8: #e34948;
  --ec-other: #898781;
  --ec-good: #006300;
}
:host([dark]) {
  --ec-muted: #898781;
  --ec-grid: #2c2c2a;
  --ec-axis: #383835;
  --ec-wash: rgba(255, 255, 255, 0.06);
  --ec-ring: rgba(255, 255, 255, 0.1);
  --ec-s1: #3987e5;
  --ec-s2: #d95926;
  --ec-s3: #199e70;
  --ec-s4: #c98500;
  --ec-s5: #d55181;
  --ec-s6: #008300;
  --ec-s7: #9085e9;
  --ec-s8: #e66767;
  --ec-good: #0ca30c;
}
* { box-sizing: border-box; }
.toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  height: var(--header-height, 56px);
  padding: 0 12px 0 4px;
  background: var(--app-header-background-color, var(--primary-color));
  color: var(--app-header-text-color, #ffffff);
  border-bottom: var(--app-header-border-bottom, none);
  position: sticky;
  top: 0;
  z-index: 2;
}
.toolbar h1 {
  flex: 1;
  margin: 0 0 0 12px;
  font-size: var(--ha-font-size-xl, 20px);
  font-weight: var(--ha-font-weight-normal, 400);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.toolbar select {
  font: inherit;
  color: inherit;
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 8px;
  padding: 4px 8px;
  max-width: 50%;
}
.toolbar select option { color: var(--primary-text-color); background: var(--card-background-color); }
main {
  max-width: 1040px;
  margin: 0 auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.filters { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; }
.segmented {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px;
  border-radius: 20px;
  background: var(--ec-surface);
  box-shadow: inset 0 0 0 1px var(--divider-color, var(--ec-ring));
}
.segmented button {
  font: inherit;
  font-size: 14px;
  border: none;
  border-radius: 16px;
  padding: 6px 14px;
  min-height: 32px;
  background: transparent;
  color: var(--ec-text);
  cursor: pointer;
}
.segmented button:hover { background: var(--ec-wash); }
.segmented button[aria-pressed="true"] {
  background: var(--primary-color);
  color: var(--text-primary-color, #ffffff);
}
.nav { display: inline-flex; align-items: center; gap: 4px; }
.nav .label { min-width: 9em; text-align: center; font-weight: 500; }
.icon-button {
  font: inherit;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--ec-text);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.icon-button:hover:not(:disabled) { background: var(--ec-wash); }
.icon-button:disabled { opacity: 0.35; cursor: default; }
.icon-button svg { width: 24px; height: 24px; fill: currentColor; }
.custom { display: inline-flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.custom label { display: inline-flex; align-items: center; gap: 6px; color: var(--ec-text-2); font-size: 14px; }
.custom input {
  font: inherit;
  color: var(--ec-text);
  background: var(--ec-surface);
  border: 1px solid var(--divider-color, var(--ec-axis));
  border-radius: 8px;
  padding: 6px 8px;
  color-scheme: light;
}
:host([dark]) .custom input { color-scheme: dark; }
.window { width: 100%; color: var(--ec-text-2); font-size: 14px; }
.content { display: flex; flex-direction: column; gap: 16px; transition: opacity 0.2s; }
.content.loading { opacity: 0.5; pointer-events: none; }
.card {
  background: var(--ec-surface);
  border-radius: var(--ha-card-border-radius, 12px);
  border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  box-shadow: var(--ha-card-box-shadow, none);
  padding: 16px;
}
.card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.card h2 { margin: 0; font-size: 16px; font-weight: 500; }
.card .hint { margin: 2px 0 0; color: var(--ec-text-2); font-size: 13px; }
.toggle {
  font: inherit;
  font-size: 13px;
  border: 1px solid var(--divider-color, var(--ec-axis));
  border-radius: 14px;
  padding: 4px 10px;
  background: transparent;
  color: var(--ec-text);
  cursor: pointer;
  white-space: nowrap;
}
.toggle:hover { background: var(--ec-wash); }
.message { color: var(--ec-text-2); }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
.kpi .label { color: var(--ec-text-2); font-size: 14px; }
.kpi .value { font-size: 28px; font-weight: 600; margin: 4px 0 2px; line-height: 1.2; overflow-wrap: anywhere; }
.kpi .sub { color: var(--ec-text-2); font-size: 13px; }
.price-tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; margin-top: 8px; }
.price-tile { border: 1px solid var(--divider-color, var(--ec-grid)); border-radius: 10px; padding: 10px 12px; min-width: 0; }
.price-tile .name { display: flex; align-items: center; gap: 6px; color: var(--ec-text-2); font-size: 13px; }
.price-tile .price { font-size: 18px; font-weight: 600; margin: 2px 0; }
.price-tile .delta { color: var(--ec-text-2); font-size: 12px; }
.price-tile svg { display: block; margin-top: 8px; overflow: visible; }
.price-tile rect { fill: transparent; cursor: pointer; }
.chips { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 13px; }
.chip { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; color: var(--ec-text-2); }
.chip strong { color: var(--ec-text); font-weight: 500; font-variant-numeric: tabular-nums; }
.details { margin-top: 12px; padding-top: 8px; border-top: 1px solid var(--divider-color, var(--ec-grid)); }
.swatch { width: 10px; height: 10px; border-radius: 2px; flex: none; }
.line-key { width: 14px; height: 2px; border-radius: 1px; flex: none; }
.chart { position: relative; width: 100%; }
.chart svg { display: block; overflow: visible; }
.chart text { font-size: 12px; fill: var(--ec-muted); font-variant-numeric: tabular-nums; }
.chart .hit { fill: transparent; cursor: crosshair; outline: none; }
.chart .hit:focus-visible { stroke: var(--primary-color); stroke-width: 2px; }
.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--ec-surface);
  color: var(--ec-text);
  border: 1px solid var(--divider-color, var(--ec-axis));
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 8px 10px;
  font-size: 13px;
  min-width: 140px;
  z-index: 1;
}
.tooltip .head { color: var(--ec-text-2); margin-bottom: 4px; }
.tooltip .head::first-letter, .nav .label::first-letter { text-transform: uppercase; }
.tooltip .row { display: flex; align-items: center; gap: 8px; }
.tooltip .row strong { font-variant-numeric: tabular-nums; }
.tooltip .row span { color: var(--ec-text-2); }
.note { color: var(--ec-text-2); font-size: 13px; margin: 8px 0 0; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { padding: 6px 8px; text-align: right; border-bottom: 1px solid var(--divider-color, var(--ec-grid)); white-space: nowrap; font-variant-numeric: tabular-nums; }
th:first-child, td:first-child { text-align: left; }
th { color: var(--ec-text-2); font-weight: 500; }
td .swatch { display: inline-block; vertical-align: -1px; margin-right: 6px; }
tfoot td { font-weight: 600; border-bottom: none; }
.tranche-contract + .tranche-contract { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--divider-color, var(--ec-grid)); }
.tranche-contract h3 { margin: 0 0 8px; font-size: 14px; font-weight: 500; }
.split { display: grid; grid-template-columns: 3em 1fr; align-items: center; gap: 6px 8px; margin-bottom: 8px; }
.split .axis-label { color: var(--ec-text-2); font-size: 13px; }
.segments { display: flex; gap: 2px; height: 28px; }
.segment {
  border-radius: 4px;
  min-width: 0;
  display: flex;
  align-items: center;
  padding: 0 6px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
}
.bill h3 { font-size: 14px; font-weight: 500; margin: 16px 0 4px; color: var(--ec-text-2); }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--divider-color, var(--ec-grid)); }
.tabs button {
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  padding: 10px 16px;
  background: transparent;
  color: var(--ec-text-2);
  cursor: pointer;
}
.tabs button:hover { background: var(--ec-wash); }
.tabs button[aria-selected="true"] { color: var(--primary-color); border-bottom-color: var(--primary-color); }
.picker { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }
.picker label { display: inline-flex; align-items: center; gap: 8px; color: var(--ec-text-2); font-size: 14px; }
.picker select {
  font: inherit;
  color: var(--ec-text);
  background: var(--ec-surface);
  border: 1px solid var(--divider-color, var(--ec-axis));
  border-radius: 8px;
  padding: 6px 8px;
  min-width: 12em;
}
.primary {
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 18px;
  padding: 8px 20px;
  background: var(--primary-color);
  color: var(--text-primary-color, #ffffff);
  cursor: pointer;
}
.primary:disabled { opacity: 0.5; cursor: default; }
.totals { margin-top: 16px; display: grid; grid-template-columns: 1fr auto; gap: 6px 16px; font-size: 14px; }
.totals .strong { font-weight: 600; font-size: 16px; }
.totals .num { text-align: right; font-variant-numeric: tabular-nums; }
.totals hr { grid-column: 1 / -1; width: 100%; border: none; border-top: 1px solid var(--divider-color, var(--ec-grid)); margin: 4px 0; }
.verdict { grid-column: 1 / -1; color: var(--ec-text-2); }
@media (max-width: 600px) {
  main { padding: 12px; gap: 12px; }
  .card { padding: 14px; }
  .kpi .value { font-size: 24px; }
  .nav .label { min-width: 7em; }
  .segmented { display: grid; grid-template-columns: 1fr 1fr; width: 100%; border-radius: 16px; }
  th, td { padding: 6px 4px; }
}
`;

const ICONS = {
  left: "M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z",
  right: "M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z",
};

// DOM helpers. Strings become text nodes, so names from the configuration are
// never parsed as markup.
function setAttributes(node, attributes) {
  for (const [key, value] of Object.entries(attributes)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "style") {
      for (const [property, item] of Object.entries(value)) {
        node.style.setProperty(property, item);
      }
    } else if (key.startsWith("on")) {
      node.addEventListener(key.slice(2), value);
    } else {
      node.setAttribute(key, value === true ? "" : String(value));
    }
  }
}

function h(tag, attributes = {}, ...children) {
  const node = document.createElement(tag);
  setAttributes(node, attributes);
  node.append(...children.flat(Infinity).filter((child) => child !== null && child !== undefined && child !== false));
  return node;
}

function s(tag, attributes = {}, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  setAttributes(node, attributes);
  node.append(...children.flat(Infinity).filter((child) => child !== null && child !== undefined && child !== false));
  return node;
}

function icon(path) {
  return s("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" }, s("path", { d: path }));
}

function format(template, values) {
  return template.replace(/\{(\w+)\}/g, (_, key) => values[key] ?? "");
}

// Days are "YYYY-MM-DD" strings, computed in UTC so no time zone shifts them.
function dayTime(day) {
  const [year, month, date] = day.split("-").map(Number);
  return Date.UTC(year, month - 1, date);
}

function dayString(time) {
  return new Date(time).toISOString().slice(0, 10);
}

function addDays(day, count) {
  return dayString(dayTime(day) + count * DAY_MS);
}

function monthEnd(year, month) {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function lastDayOf(isoEnd) {
  // The end of a window is the first hour left out, in French time.
  const day = isoEnd.slice(0, 10);
  return isoEnd.slice(11, 19) === "00:00:00" ? addDays(day, -1) : day;
}

function niceTicks(min, max, count) {
  if (min === max) {
    max = min + 1;
  }
  const rough = (max - min) / count;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const ratio = rough / magnitude;
  const step = (ratio >= 7.5 ? 10 : ratio >= 3.5 ? 5 : ratio >= 1.5 ? 2 : 1) * magnitude;
  const low = Math.floor(min / step) * step;
  const high = Math.ceil(max / step) * step;
  const ticks = [];
  for (let value = low; value <= high + step / 2; value += step) {
    ticks.push(Math.round(value / step) * step);
  }
  return ticks;
}

// A column with a rounded data end and a square baseline.
function columnPath(x, width, base, top) {
  const radius = Math.min(4, width / 2, Math.abs(base - top));
  const sign = top <= base ? 1 : -1;
  return [
    `M${x},${base}`,
    `V${top + sign * radius}`,
    `Q${x},${top} ${x + radius},${top}`,
    `H${x + width - radius}`,
    `Q${x + width},${top} ${x + width},${top + sign * radius}`,
    `V${base}`,
    "Z",
  ].join("");
}

class ElectricityContractsPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._entries = null;
    this._entryId = null;
    this._mode = "rolling";
    this._year = null;
    this._month = null;
    this._custom = null;
    this._request = null;
    this._data = null;
    this._error = null;
    this._views = { time: "chart", cumulative: "chart" };
    this._tab = "compare";
    this._billContract = null;
    this._bill = null;
    this._billError = null;
    this._billBusy = false;
    this._billCount = 0;
    // Which price period each contract card shows, by contract id.
    this._pricePeriods = {};
    this._contractOpen = {};
    this._loadCount = 0;
    this._width = 0;
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    this.toggleAttribute("dark", Boolean(hass.themes && hass.themes.darkMode));
    if (this._menu) {
      this._menu.hass = hass;
    }
    if (first) {
      this._build();
      this._loadEntries();
    }
  }

  get hass() {
    return this._hass;
  }

  set narrow(narrow) {
    this._narrow = narrow;
    if (this._menu) {
      this._menu.narrow = narrow;
    }
  }

  set panel(panel) {
    this._panel = panel;
  }

  set route(route) {
    this._route = route;
  }

  connectedCallback() {
    this._observer = new ResizeObserver(() => {
      const width = this._content ? this._content.clientWidth : 0;
      if (width && width !== this._width) {
        this._width = width;
        this._renderCharts();
      }
    });
    if (this._content) {
      this._observer.observe(this._content);
    }
    if (this._entries) {
      // Back on the page: the statistics may have grown since.
      this._loadEntries();
    }
  }

  disconnectedCallback() {
    if (this._observer) {
      this._observer.disconnect();
    }
  }

  // Translations and formats ------------------------------------------------

  get _language() {
    const language = (this._hass.locale && this._hass.locale.language) || this._hass.language || "en";
    return language.toLowerCase().startsWith("fr") ? "fr" : "en";
  }

  get _locale() {
    return (this._hass.locale && this._hass.locale.language) || this._hass.language || "en";
  }

  _t(key, values) {
    const text = STRINGS[this._language][key] ?? STRINGS.en[key] ?? key;
    return values ? format(text, values) : text;
  }

  _money(value, digits = 2) {
    return new Intl.NumberFormat(this._locale, {
      style: "currency",
      currency: (this._hass.config && this._hass.config.currency) || "EUR",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  }

  _price(value) {
    return this._money(value, 4);
  }

  _kwh(value) {
    return `${new Intl.NumberFormat(this._locale, { maximumFractionDigits: 0 }).format(value)} kWh`;
  }

  _number(value, digits = 0) {
    return new Intl.NumberFormat(this._locale, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  }

  _dayLabel(day, options = { day: "numeric", month: "short", year: "numeric" }) {
    return new Intl.DateTimeFormat(this._locale, { ...options, timeZone: "UTC" }).format(dayTime(day));
  }

  _bucketLabel(day, long) {
    if (this._data.group_by === "month") {
      return this._dayLabel(day, long ? { month: "long", year: "numeric" } : { month: "short" });
    }
    return this._dayLabel(day, long ? { weekday: "short", day: "numeric", month: "long", year: "numeric" } : { day: "numeric" });
  }

  // Data ----------------------------------------------------------------------

  get _entry() {
    return (this._entries || []).find((entry) => entry.entry_id === this._entryId) || null;
  }

  _color(contractId) {
    const contracts = this._entry ? this._entry.contracts : [];
    const index = contracts.findIndex((contract) => contract.id === contractId);
    if (contractId === ACTUAL) return "var(--ec-s1)";
    return index >= 0 && index < SERIES_SLOTS ? `var(--ec-s${index + 1})` : "var(--ec-other)";
  }

  async _loadEntries() {
    try {
      this._entries = await this._hass.callWS({ type: `${DOMAIN}/entries` });
    } catch (error) {
      this._entries = [];
      this._error = error.message || String(error);
    }
    if (!this._entries.some((entry) => entry.entry_id === this._entryId)) {
      this._entryId = this._entries.length ? this._entries[0].entry_id : null;
      this._year = null;
      this._month = null;
      this._custom = null;
    }
    this._renderSources();
    await this._load();
  }

  _window() {
    const entry = this._entry;
    const last = entry.last_day;
    const [year, month, day] = last.split("-").map(Number);
    if (this._year === null) {
      this._year = year;
      this._month = month;
    }
    switch (this._mode) {
      case "year":
        return { start: `${this._year}-01-01`, end: `${this._year}-12-31` };
      case "month":
        return {
          start: `${this._year}-${pad(this._month)}-01`,
          end: `${this._year}-${pad(this._month)}-${pad(monthEnd(this._year, this._month))}`,
        };
      case "custom":
        if (this._custom) {
          return this._custom;
        }
      // Falls through: a custom window starts as the last 12 months.
      default: {
        const start = addDays(`${year - 1}-${pad(month)}-${pad(Math.min(day, monthEnd(year - 1, month)))}`, 1);
        return { start: entry.first_day && entry.first_day > start ? entry.first_day : start, end: last };
      }
    }
  }

  async _load() {
    const entry = this._entry;
    // A bill is only computed when asked for: another period starts afresh.
    this._bill = null;
    this._billError = null;
    this._billBusy = false;
    this._billCount++;
    this._renderFilters();
    if (!entry || !entry.last_day || !entry.contracts.length) {
      this._data = null;
      this._renderContent();
      return;
    }
    const window = this._window();
    if (this._mode === "custom" && !this._custom) {
      this._custom = window;
      this._renderFilters();
    }
    const count = ++this._loadCount;
    this._content.classList.add("loading");
    try {
      const data = await this._hass.callWS({
        type: `${DOMAIN}/compare`,
        entry_id: entry.entry_id,
        start: window.start,
        end: window.end,
      });
      if (count !== this._loadCount) return;
      this._request = window;
      this._data = data;
      this._error = null;
    } catch (error) {
      if (count !== this._loadCount) return;
      this._data = null;
      this._error = error.message || String(error);
    }
    this._content.classList.remove("loading");
    this._renderFilters();
    this._renderContent();
  }

  // Layout --------------------------------------------------------------------

  _build() {
    const root = this.shadowRoot;
    root.append(h("style", {}, STYLE));
    this._menu = document.createElement("ha-menu-button");
    this._menu.hass = this._hass;
    this._menu.narrow = this._narrow;
    this._sources = h("span");
    root.append(h("div", { class: "toolbar" }, this._menu, h("h1", {}, this._t("title")), this._sources));
    this._filters = h("div", { class: "filters" });
    this._content = h("div", { class: "content" });
    this._tabs = h("div", { class: "tabs", role: "tablist" });
    root.append(h("main", {}, this._tabs, this._filters, this._content));
    this._renderTabs();
    if (this._observer) {
      this._observer.observe(this._content);
    }
  }

  _renderTabs() {
    this._tabs.replaceChildren(
      ...["compare", "bill"].map((tab) =>
        h(
          "button",
          {
            role: "tab",
            "aria-selected": String(this._tab === tab),
            onclick: () => {
              if (this._tab === tab) return;
              this._tab = tab;
              this._renderTabs();
              this._renderContent();
            },
          },
          this._t(tab === "compare" ? "tabActual" : "tabBill"),
        ),
      ),
    );
  }

  _renderSources() {
    const entries = this._entries || [];
    if (entries.length < 2) {
      this._sources.replaceChildren();
      return;
    }
    const select = h(
      "select",
      {
        "aria-label": "Source",
        onchange: (event) => {
          this._entryId = event.target.value;
          this._year = null;
          this._custom = null;
          this._load();
        },
      },
      entries.map((entry) => {
        const option = h("option", { value: entry.entry_id }, entry.title);
        option.selected = entry.entry_id === this._entryId;
        return option;
      }),
    );
    this._sources.replaceChildren(select);
  }

  _renderFilters() {
    const entry = this._entry;
    if (!entry || !entry.last_day || !entry.contracts.length) {
      this._filters.replaceChildren();
      return;
    }
    const modes = ["rolling", "year", "month", "custom"].map((mode) =>
      h(
        "button",
        {
          "aria-pressed": String(this._mode === mode),
          onclick: () => {
            if (this._mode === mode) return;
            this._mode = mode;
            this._load();
          },
        },
        this._t(mode),
      ),
    );
    const children = [h("div", { class: "segmented", role: "group", "aria-label": this._t("period") }, modes)];
    const first = entry.first_day || entry.last_day;
    if (this._mode === "year" && this._year !== null) {
      children.push(
        this._nav(
          String(this._year),
          this._year > Number(first.slice(0, 4)),
          this._year < Number(entry.last_day.slice(0, 4)),
          (step) => {
            this._year += step;
            this._load();
          },
        ),
      );
    } else if (this._mode === "month" && this._year !== null) {
      const current = `${this._year}-${pad(this._month)}`;
      children.push(
        this._nav(
          this._dayLabel(`${current}-01`, { month: "long", year: "numeric" }),
          current > first.slice(0, 7),
          current < entry.last_day.slice(0, 7),
          (step) => {
            const index = this._year * 12 + this._month - 1 + step;
            this._year = Math.floor(index / 12);
            this._month = (index % 12) + 1;
            this._load();
          },
        ),
      );
    } else if (this._mode === "custom" && this._custom) {
      const input = (key) =>
        h("input", {
          type: "date",
          value: this._custom[key],
          min: first,
          max: entry.last_day,
          onchange: (event) => {
            const value = event.target.value;
            if (!value) return;
            const next = { ...this._custom, [key]: value };
            if (next.start > next.end) {
              next[key === "start" ? "end" : "start"] = value;
            }
            this._custom = next;
            this._load();
          },
        });
      children.push(
        h(
          "div",
          { class: "custom" },
          h("label", {}, this._t("from"), input("start")),
          h("label", {}, this._t("to"), input("end")),
        ),
      );
    }
    const data = this._data;
    if (data && data.start !== data.end) {
      const energy = data.contracts.length ? data.contracts[0].energy : 0;
      children.push(h("div", { class: "window" }, this._t("windowEnergy", { window: this._windowText(), energy: this._kwh(energy) })));
    }
    this._filters.replaceChildren(...children);
  }

  _windowText(data = this._data) {
    return this._t("window", {
      start: this._dayLabel(data.start.slice(0, 10)),
      end: this._dayLabel(lastDayOf(data.end)),
    });
  }

  _nav(label, hasPrevious, hasNext, move) {
    return h(
      "div",
      { class: "nav" },
      h(
        "button",
        { class: "icon-button", "aria-label": this._t("previous"), disabled: !hasPrevious, onclick: () => move(-1) },
        icon(ICONS.left),
      ),
      h("span", { class: "label", "aria-live": "polite" }, label),
      h(
        "button",
        { class: "icon-button", "aria-label": this._t("next"), disabled: !hasNext, onclick: () => move(1) },
        icon(ICONS.right),
      ),
    );
  }

  _card(title, hint, body, toggle) {
    return h(
      "section",
      { class: "card" },
      h("div", { class: "card-head" }, h("div", {}, h("h2", {}, title), hint ? h("p", { class: "hint" }, hint) : null), toggle || null),
      body,
    );
  }

  _renderContent() {
    const entry = this._entry;
    let message = null;
    if (this._error) {
      message = this._t("loadFailed", { error: this._error });
    } else if (!entry) {
      message = this._entries ? this._t("noEntry") : null;
    } else if (!entry.contracts.length) {
      message = this._t("noContract");
    } else if (!entry.last_day || !this._data || this._data.start === this._data.end) {
      message = this._data || !entry.last_day ? this._t("noData") : null;
    }
    if (message !== null) {
      this._content.replaceChildren(h("section", { class: "card message" }, message));
      return;
    }
    if (!this._data) {
      return;
    }
    this._timeChart = null;
    this._cumulativeChart = null;
    if (this._tab === "bill") {
      this._content.replaceChildren(...this._renderBillTab());
    } else if (!this._data.actual) {
      this._content.replaceChildren(h("section", { class: "card message" }, this._t("noContractInForce")));
    } else {
      this._timeChart = h("div", { class: "chart" });
      const inForce = this._contractsInForce();
      const cards = [
        ...this._renderContractCards(),
        this._renderKpis(),
        this._card(this._t("costOverTime"), this._t(this._data.group_by === "month" ? "costPerMonth" : "costPerDay"), this._timeChart, this._toggle("time")),
      ];
      // The split of a contract covers the whole period: only shown when one was in force.
      if (inForce.length === 1) {
        cards.push(this._card(this._t("tranches"), this._t("tranchesHint"), this._renderTranches(inForce)));
      }
      this._content.replaceChildren(...cards);
    }
    this._width = this._content.clientWidth;
    this._renderCharts();
  }

  _toggle(view) {
    return h(
      "button",
      {
        class: "toggle",
        onclick: () => {
          this._views[view] = this._views[view] === "chart" ? "table" : "chart";
          this._renderContent();
        },
      },
      this._t(this._views[view] === "chart" ? "table" : "chart"),
    );
  }

  // Headline figures -----------------------------------------------------------

  _renderKpis() {
    const actual = this._data.actual;
    const tile = (label, value, sub) =>
      h("section", { class: "card kpi" }, h("div", { class: "label" }, label), h("div", { class: "value" }, value), h("div", { class: "sub" }, sub));
    return h(
      "div",
      { class: "kpis" },
      tile(this._t("actualCost"), this._money(actual.total_cost), this._t("ofWhichSubscription", { amount: this._money(actual.fixed_cost) })),
      tile(this._t("consumption"), this._kwh(actual.energy), ""),
      tile(this._t("average"), actual.energy ? `${this._price(actual.variable_cost / actual.energy)}/kWh` : "—", this._t("withoutSubscription")),
    );
  }

  // The contracts in force today, with the prices they have had.
  _renderContractCards() {
    const today = dayString(Date.now());
    return this._entry.contracts
      .filter((contract) => contract.active_from && contract.active_from <= today && (!contract.active_to || contract.active_to >= today))
      .map((contract) => {
        const facts = [
          KINDS[this._language][contract.kind] || contract.kind,
          contract.kva ? `${contract.kva} kVA` : null,
          this._t(contract.official ? "regulated" : "manualPrices"),
          this._t("since", { date: this._dayLabel(contract.active_from) }),
          contract.off_peak.length ? this._t("offPeakHours", { ranges: contract.off_peak.join(", ") }) : null,
          contract.weekend_off_peak ? this._t("weekendOffPeak") : null,
        ];
        const periods = contract.prices;
        const current = periods.findIndex((period) => period.start <= today && (!period.end || period.end >= today));
        const index = Math.min(this._pricePeriods[contract.id] ?? (current >= 0 ? current : periods.length - 1), periods.length - 1);
        const title = `${this._t("currentContract")} · ${contract.name}`;
        if (!periods.length) {
          return this._card(title, facts.filter(Boolean).join(" · "), h("p", { class: "message" }, this._t("noPrices")));
        }
        const names = TRANCHES[this._language];
        const now = periods[current >= 0 ? current : periods.length - 1];
        const chips = h(
          "div",
          { class: "chips" },
          h("span", { class: "chip" }, this._t("subscription"), h("strong", {}, this._t("subscriptionYear", { amount: this._money(now.fixed_per_year) }))),
          Object.entries(now.tranches).map(([tranche, price]) =>
            h(
              "span",
              { class: "chip" },
              h("span", { class: "swatch", style: { background: (TRANCHE_FILLS[tranche] || ["#898781"])[0] } }),
              names[tranche] || tranche,
              h("strong", {}, `${this._price(price)}/kWh`),
            ),
          ),
        );
        const open = Boolean(this._contractOpen[contract.id]);
        const toggle = h(
          "button",
          {
            class: "toggle",
            "aria-expanded": String(open),
            onclick: () => {
              this._contractOpen[contract.id] = !open;
              this._renderContent();
            },
          },
          this._t(open ? "less" : "more"),
        );
        const details = open
          ? h(
              "div",
              { class: "details" },
              this._nav(this._periodLabel(periods[index]), index > 0, index < periods.length - 1, (step) => {
                this._pricePeriods[contract.id] = index + step;
                this._renderContent();
              }),
              this._priceTiles(contract, periods, index, today),
            )
          : null;
        return this._card(title, facts.filter(Boolean).join(" · "), h("div", {}, chips, details), toggle);
      });
  }

  // One tile per price of a contract: its value in the chosen price period, the
  // change since the period before, and how it moved over every period.
  _priceTiles(contract, periods, index, today) {
    const names = TRANCHES[this._language];
    const starts = periods.map((period) => dayTime(period.start));
    const last = Math.max(dayTime(today), starts[starts.length - 1] + DAY_MS);
    const x = (time) => ((time - starts[0]) / (last - starts[0])) * 100;
    const edge = (position) => (position < periods.length ? x(starts[position]) : 100);
    const select = (position) => {
      this._pricePeriods[contract.id] = position;
      this._renderContent();
    };
    const percent = new Intl.NumberFormat(this._locale, { style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" });
    const tile = (label, color, values, text) => {
      const known = values.filter((value) => value !== null);
      const min = Math.min(...known);
      const max = Math.max(...known);
      const y = (value) => (max === min ? 20 : 36 - ((value - min) / (max - min)) * 32);
      let path = "";
      values.forEach((value, position) => {
        if (value === null) return;
        path += `${path ? "L" : "M"}${edge(position)},${y(value)}H${edge(position + 1)}`;
      });
      const value = values[index];
      const before = index > 0 ? values[index - 1] : null;
      const change = value !== null && before ? value / before - 1 : null;
      return h(
        "div",
        { class: "price-tile" },
        h("div", { class: "name" }, color ? h("span", { class: "swatch", style: { background: color } }) : null, label),
        h("div", { class: "price" }, value === null ? "—" : text(value)),
        h("div", { class: "delta" }, change === null ? "\u00a0" : this._t("sincePrevious", { change: percent.format(change) })),
        s(
          "svg",
          { viewBox: "0 0 100 40", preserveAspectRatio: "none", width: "100%", height: 44, role: "img", "aria-label": label },
          s("path", { d: path, "vector-effect": "non-scaling-stroke", style: { fill: "none", stroke: "var(--ec-muted)", "stroke-width": "1.5px" } }),
          value === null
            ? null
            : s("path", {
                d: `M${edge(index)},${y(value)}H${edge(index + 1)}`,
                "vector-effect": "non-scaling-stroke",
                style: { fill: "none", stroke: color || "var(--ec-s1)", "stroke-width": "4px", "stroke-linecap": "round" },
              }),
          periods.map((period, position) =>
            s(
              "rect",
              { x: edge(position), y: 0, width: edge(position + 1) - edge(position), height: 40, onclick: () => select(position) },
              s("title", {}, `${this._periodLabel(period)} : ${values[position] === null ? "—" : text(values[position])}`),
            ),
          ),
        ),
      );
    };
    return h(
      "div",
      { class: "price-tiles" },
      tile(
        this._t("subscription"),
        null,
        periods.map((period) => period.fixed_per_year),
        (value) => this._t("subscriptionYear", { amount: this._money(value) }),
      ),
      Object.keys(periods[index].tranches).map((tranche) =>
        tile(
          names[tranche] || tranche,
          (TRANCHE_FILLS[tranche] || ["#898781"])[0],
          periods.map((period) => period.tranches[tranche] ?? null),
          (value) => `${this._price(value)}/kWh`,
        ),
      ),
    );
  }

  _periodLabel(period) {
    return period.end
      ? this._t("pricesFrom", { start: this._dayLabel(period.start), end: this._dayLabel(period.end) })
      : this._t("pricesSince", { date: this._dayLabel(period.start) });
  }

  // The compared contracts that were in force during the period.
  _contractsInForce() {
    const first = this._data.start.slice(0, 10);
    const last = lastDayOf(this._data.end);
    const ids = this._entry.contracts
      .filter((contract) => contract.active_from && contract.active_from <= last && (!contract.active_to || contract.active_to >= first))
      .map((contract) => contract.id);
    return this._data.contracts.filter((contract) => ids.includes(contract.id));
  }

  // Charts ---------------------------------------------------------------------

  _renderCharts() {
    if (!this._data) return;
    if (this._timeChart) {
      this._renderTimeChart();
    }
    if (this._cumulativeChart && this._bill) {
      this._renderCumulativeChart(this._bill.contract);
    }
  }

  _renderTimeChart() {
    const actual = { id: ACTUAL, name: this._t("actual") };
    const partial = this._data.series.some((bucket) => bucket.actual === null);
    if (this._views.time === "chart") {
      const series = [{ ...actual, values: this._data.series.map((bucket) => bucket.actual ?? 0) }];
      if (this._data.group_by === "month") {
        this._drawColumns(this._timeChart, series);
      } else {
        this._drawLines(this._timeChart, series, { zero: false });
      }
    } else {
      this._timeChart.replaceChildren(this._seriesTable((bucket) => bucket.actual, false, [actual]));
    }
    if (partial) {
      this._timeChart.append(h("p", { class: "note" }, this._t("partialActual")));
    }
  }

  _renderCumulativeChart(contract) {
    const cumulative = this._cumulative(contract.id);
    if (this._views.cumulative === "chart") {
      const series = [{ id: contract.id, name: contract.name, values: cumulative.values }];
      this._drawLines(this._cumulativeChart, series, { zero: true });
    } else {
      this._cumulativeChart.replaceChildren(this._seriesTable((bucket, item, index) => cumulative.values[index], false, [contract]));
    }
    if (cumulative.partial) {
      this._cumulativeChart.append(h("p", { class: "note" }, this._t("partialActual")));
    }
  }

  // What the contract would have saved on the actual cost, day after day.
  _cumulative(contractId) {
    let total = 0;
    let partial = false;
    const values = this._data.series.map((bucket) => {
      if (bucket.actual === null) {
        partial = true;
      } else {
        total += bucket.actual - (bucket.contracts[contractId] ?? 0);
      }
      return Math.round(total * 100) / 100;
    });
    return { values, partial };
  }

  _frame(container, values, zero) {
    const width = Math.max(container.clientWidth || 320, 240);
    const height = width < 500 ? 220 : 260;
    const margin = { top: 12, right: 12, bottom: 28, left: 0 };
    let min = Math.min(0, ...values);
    let max = Math.max(0, ...values);
    if (!zero) {
      min = 0;
    }
    const ticks = niceTicks(min, max, 4);
    const low = ticks[0];
    const high = ticks[ticks.length - 1];
    const digits = ticks.length > 1 && ticks[1] - ticks[0] < 1 ? 2 : 0;
    const labels = ticks.map((tick) => this._money(tick, digits));
    margin.left = Math.max(...labels.map((label) => label.length)) * 7 + 10;
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const y = (value) => margin.top + plotHeight - ((value - low) / (high - low || 1)) * plotHeight;
    const count = this._data.series.length;
    const band = plotWidth / count;
    const x = (index) => margin.left + band * (index + 0.5);
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img" });
    const grid = s("g");
    ticks.forEach((tick, index) => {
      grid.append(
        s("line", {
          x1: margin.left,
          x2: width - margin.right,
          y1: y(tick),
          y2: y(tick),
          style: { stroke: tick === 0 ? "var(--ec-axis)" : "var(--ec-grid)", "stroke-width": "1px" },
        }),
        s("text", { x: margin.left - 8, y: y(tick), "text-anchor": "end", "dominant-baseline": "middle" }, labels[index]),
      );
    });
    const step = Math.max(1, Math.ceil((this._data.group_by === "month" ? 34 : 26) / band));
    this._data.series.forEach((bucket, index) => {
      if (index % step !== 0) return;
      let label = this._bucketLabel(bucket.start, false);
      if (this._data.group_by === "month" && (index === 0 || bucket.start.slice(5, 7) === "01") && band * step >= 52) {
        label = this._dayLabel(bucket.start, { month: "short", year: "2-digit" });
      }
      grid.append(s("text", { x: x(index), y: height - 8, "text-anchor": "middle" }, label));
    });
    root.append(grid);
    return { root, width, height, margin, plotWidth, plotHeight, x, y, band, count };
  }

  _drawColumns(container, series) {
    const values = series.flatMap((item) => item.values);
    const frame = this._frame(container, values, false);
    const { root, margin, plotHeight, x, y, band } = frame;
    const wash = s("rect", { y: margin.top, height: plotHeight, width: band, style: { fill: "var(--ec-wash)", visibility: "hidden" } });
    root.insertBefore(wash, root.firstChild);
    const gap = 2;
    const group = band * 0.8;
    const barWidth = Math.max(2, Math.min(24, (group - gap * (series.length - 1)) / series.length));
    const used = barWidth * series.length + gap * (series.length - 1);
    const marks = s("g");
    const base = y(0);
    this._data.series.forEach((bucket, index) => {
      const left = x(index) - used / 2;
      series.forEach((item, position) => {
        const value = item.values[index];
        if (!value) return;
        marks.append(
          s("path", {
            d: columnPath(left + position * (barWidth + gap), barWidth, base, y(value)),
            style: { fill: this._color(item.id) },
          }),
        );
      });
    });
    root.append(marks);
    const tooltip = h("div", { class: "tooltip", hidden: true });
    const hits = s("g");
    this._data.series.forEach((bucket, index) => {
      const show = () => {
        wash.setAttribute("x", x(index) - band / 2);
        wash.style.visibility = "visible";
        this._showTooltip(tooltip, frame, index, series, x(index));
      };
      const hide = () => {
        wash.style.visibility = "hidden";
        tooltip.hidden = true;
      };
      hits.append(
        s("rect", {
          class: "hit",
          x: x(index) - band / 2,
          y: margin.top,
          width: band,
          height: plotHeight,
          tabindex: 0,
          "aria-label": this._bucketLabel(bucket.start, true),
          onpointerenter: show,
          onpointerleave: hide,
          onfocus: show,
          onblur: hide,
        }),
      );
    });
    root.append(hits);
    container.replaceChildren(root, tooltip);
  }

  _drawLines(container, series, { zero }) {
    const values = series.flatMap((item) => item.values);
    const frame = this._frame(container, values, zero);
    const { root, margin, plotHeight, plotWidth, x, y, count } = frame;
    const lines = s("g");
    for (const item of series) {
      const color = this._color(item.id);
      const points = item.values.map((value, index) => `${x(index)},${y(value)}`);
      if (count > 1) {
        lines.append(
          s("polyline", {
            points: points.join(" "),
            style: { fill: "none", stroke: color, "stroke-width": "2px", "stroke-linejoin": "round", "stroke-linecap": "round" },
          }),
        );
      }
      lines.append(
        s("circle", {
          cx: x(count - 1),
          cy: y(item.values[count - 1]),
          r: 4,
          style: { fill: color, stroke: "var(--ec-surface)", "stroke-width": "2px" },
        }),
      );
    }
    root.append(lines);
    const crosshair = s("line", {
      y1: margin.top,
      y2: margin.top + plotHeight,
      style: { stroke: "var(--ec-axis)", "stroke-width": "1px", visibility: "hidden" },
    });
    const dots = s("g", { style: { visibility: "hidden" } });
    root.append(crosshair, dots);
    const tooltip = h("div", { class: "tooltip", hidden: true });
    const show = (index) => {
      crosshair.setAttribute("x1", x(index));
      crosshair.setAttribute("x2", x(index));
      crosshair.style.visibility = "visible";
      dots.replaceChildren(
        ...series.map((item) =>
          s("circle", {
            cx: x(index),
            cy: y(item.values[index]),
            r: 4,
            style: { fill: this._color(item.id), stroke: "var(--ec-surface)", "stroke-width": "2px" },
          }),
        ),
      );
      dots.style.visibility = "visible";
      this._showTooltip(tooltip, frame, index, series, x(index));
    };
    const hide = () => {
      crosshair.style.visibility = "hidden";
      dots.style.visibility = "hidden";
      tooltip.hidden = true;
    };
    let focused = count - 1;
    const hit = s("rect", {
      class: "hit",
      x: margin.left,
      y: margin.top,
      width: plotWidth,
      height: plotHeight,
      tabindex: 0,
      onpointermove: (event) => {
        const box = root.getBoundingClientRect();
        const position = event.clientX - box.left;
        focused = Math.max(0, Math.min(count - 1, Math.round((position - x(0)) / frame.band)));
        show(focused);
      },
      onpointerleave: hide,
      onfocus: () => show(focused),
      onblur: hide,
      onkeydown: (event) => {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        focused = Math.max(0, Math.min(count - 1, focused + (event.key === "ArrowLeft" ? -1 : 1)));
        show(focused);
      },
    });
    root.append(hit);
    container.replaceChildren(root, tooltip);
  }

  _showTooltip(tooltip, frame, index, series, anchor) {
    const bucket = this._data.series[index];
    const rows = [...series]
      .map((item) => ({ item, value: item.values[index] }))
      .sort((first, second) => second.value - first.value)
      .map(({ item, value }) =>
        h("div", { class: "row" }, h("span", { class: "line-key", style: { background: this._color(item.id) } }), h("strong", {}, this._money(value)), h("span", {}, item.name)),
      );
    tooltip.replaceChildren(h("div", { class: "head" }, this._bucketLabel(bucket.start, true)), ...rows);
    tooltip.hidden = false;
    const width = tooltip.offsetWidth;
    const left = anchor + 12 + width > frame.width ? anchor - 12 - width : anchor + 12;
    tooltip.style.left = `${Math.max(0, left)}px`;
    tooltip.style.top = `${frame.margin.top}px`;
  }

  _seriesTable(value, withActual, contracts = this._data.contracts) {
    const head = h(
      "tr",
      {},
      h("th", {}, this._t("period")),
      contracts.map((contract) => h("th", {}, contract.name)),
      withActual && this._data.actual ? h("th", {}, this._t("actual")) : null,
    );
    const rows = this._data.series.map((bucket, index) =>
      h(
        "tr",
        {},
        h("td", {}, this._bucketLabel(bucket.start, true)),
        contracts.map((contract) => {
          const amount = value(bucket, contract, index);
          return h("td", {}, amount === null ? "—" : this._money(amount));
        }),
        withActual && this._data.actual ? h("td", {}, bucket.actual === null ? "—" : this._money(bucket.actual)) : null,
      ),
    );
    return h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, head), h("tbody", {}, rows)));
  }

  // Tranches -------------------------------------------------------------------

  _renderTranches(contracts) {
    const names = TRANCHES[this._language];
    return h(
      "div",
      {},
      contracts.map((contract) => {
        const tranches = Object.entries(contract.tranches);
        const energy = tranches.reduce((sum, [, item]) => sum + item.energy, 0);
        const cost = tranches.reduce((sum, [, item]) => sum + item.cost, 0);
        const bar = (key, total, label) =>
          h(
            "div",
            { class: "split" },
            h("span", { class: "axis-label" }, label),
            h(
              "div",
              {
                class: "segments",
                role: "img",
                "aria-label": `${contract.name}, ${label}: ${tranches
                  .map(([tranche, item]) => `${names[tranche]} ${total ? Math.round((item[key] / total) * 100) : 0} %`)
                  .join(", ")}`,
              },
              tranches
                .filter(([, item]) => item[key] > 0)
                .map(([tranche, item]) => {
                  const share = total ? (item[key] / total) * 100 : 0;
                  const [fill, ink] = TRANCHE_FILLS[tranche] || ["#898781", "#ffffff"];
                  return h(
                    "div",
                    {
                      class: "segment",
                      title: `${names[tranche]} · ${key === "energy" ? this._kwh(item.energy) : this._money(item.cost)} · ${Math.round(share)} %`,
                      style: { "flex-grow": String(item[key]), "flex-basis": "0", background: fill, color: ink },
                    },
                    share >= 9 ? `${Math.round(share)} %` : "",
                  );
                }),
            ),
          );
        const table = h(
          "div",
          { class: "table-wrap" },
          h(
            "table",
            {},
            h("thead", {}, h("tr", {}, h("th", {}, this._t("tranche")), h("th", {}, this._t("energy")), h("th", {}, this._t("cost")), h("th", {}, this._t("average")))),
            h(
              "tbody",
              {},
              tranches.map(([tranche, item]) =>
                h(
                  "tr",
                  {},
                  h(
                    "td",
                    {},
                    h("span", { class: "swatch", style: { background: (TRANCHE_FILLS[tranche] || ["#898781"])[0] } }),
                    names[tranche] || tranche,
                  ),
                  h("td", {}, this._kwh(item.energy)),
                  h("td", {}, this._money(item.cost)),
                  h("td", {}, item.energy ? this._price(item.cost / item.energy) : "—"),
                ),
              ),
            ),
          ),
        );
        return h(
          "div",
          { class: "tranche-contract" },
          h("h3", {}, contract.name),
          tranches.length > 1 ? [bar("energy", energy, "kWh"), bar("cost", cost, "€")] : null,
          table,
        );
      }),
    );
  }

  // Phantom bill ---------------------------------------------------------------

  _renderBillTab() {
    const contracts = this._entry.contracts;
    const selected = contracts.find((contract) => contract.id === this._billContract) || contracts[0];
    this._billContract = selected.id;
    const select = h(
      "select",
      {
        onchange: (event) => {
          this._billContract = event.target.value;
          this._bill = null;
          this._billError = null;
          this._billBusy = false;
          this._billCount++;
          this._renderContent();
        },
      },
      contracts.map((contract) => {
        const option = h("option", { value: contract.id }, contract.name);
        option.selected = contract.id === selected.id;
        return option;
      }),
    );
    const cards = [
      this._card(
        this._t("tabBill"),
        this._t("billIntro"),
        h(
          "div",
          { class: "picker" },
          h("label", {}, this._t("contract"), select),
          h("button", { class: "primary", disabled: this._billBusy, onclick: () => this._computeBill() }, this._t(this._billBusy ? "computing" : "compute")),
        ),
      ),
    ];
    if (this._billError) {
      cards.push(h("section", { class: "card message" }, this._t("loadFailed", { error: this._billError })));
    }
    const bill = this._bill;
    if (!bill) {
      return cards;
    }
    cards.push(this._card(`${this._t("tabBill")} · ${bill.contract.name}`, this._windowText(bill), h("div", { class: "bill" }, this._billBody(bill))));
    if (this._data.actual) {
      this._cumulativeChart = h("div", { class: "chart" });
      cards.push(this._card(this._t("cumulativeOf", { name: bill.contract.name }), this._t("cumulativeHint"), this._cumulativeChart, this._toggle("cumulative")));
    }
    return cards;
  }

  async _computeBill() {
    const count = ++this._billCount;
    this._billBusy = true;
    this._billError = null;
    this._renderContent();
    try {
      const bill = await this._hass.callWS({
        type: `${DOMAIN}/bill`,
        entry_id: this._entryId,
        contract_id: this._billContract,
        start: this._request.start,
        end: this._request.end,
      });
      if (count !== this._billCount) return;
      this._bill = bill;
    } catch (error) {
      if (count !== this._billCount) return;
      this._bill = null;
      this._billError = error.message || String(error);
    }
    this._billBusy = false;
    this._renderContent();
  }

  _billBody(bill) {
    const names = TRANCHES[this._language];
    const parts = bill.periods.map((period) => {
      const start = period.start.slice(0, 10);
      const last = lastDayOf(period.end);
      const days = Math.round((dayTime(last) - dayTime(start)) / DAY_MS) + 1;
      return [
        h("h3", {}, this._t("pricesFrom", { start: this._dayLabel(start), end: this._dayLabel(last) })),
        h(
          "div",
          { class: "table-wrap" },
          h(
            "table",
            {},
            h("thead", {}, h("tr", {}, h("th", {}, this._t("item")), h("th", {}, this._t("quantity")), h("th", {}, this._t("unitPrice")), h("th", {}, this._t("amount")))),
            h(
              "tbody",
              {},
              h(
                "tr",
                {},
                h("td", {}, this._t("subscription")),
                h("td", {}, this._t("days", { count: days })),
                h("td", {}, this._t("subscriptionYear", { amount: this._money(period.fixed_per_year) })),
                h("td", {}, this._money(period.subscription)),
              ),
              period.lines.map((line) =>
                h(
                  "tr",
                  {},
                  h(
                    "td",
                    {},
                    h("span", { class: "swatch", style: { background: (TRANCHE_FILLS[line.tranche] || ["#898781"])[0] } }),
                    names[line.tranche] || line.tranche,
                  ),
                  h("td", {}, this._kwh(line.energy)),
                  h("td", {}, this._price(line.price)),
                  h("td", {}, this._money(line.cost)),
                ),
              ),
            ),
          ),
        ),
      ];
    });
    const totals = [
      h("span", {}, `${this._t("consumption")} (${this._kwh(bill.energy)})`),
      h("span", { class: "num" }, this._money(bill.consumption)),
      h("span", {}, this._t("subscription")),
      h("span", { class: "num" }, this._money(bill.subscription)),
      h("span", { class: "strong" }, this._t("total")),
      h("span", { class: "num strong" }, this._money(bill.total)),
    ];
    if (bill.actual !== null) {
      let verdict = this._t("same");
      if (bill.difference > 0) {
        verdict = this._t("moreExpensive", { amount: this._money(bill.difference) });
      } else if (bill.difference < 0) {
        verdict = this._t("cheaper", { amount: this._money(-bill.difference) });
      }
      totals.push(
        h("hr"),
        h("span", {}, this._t("actualPaid")),
        h("span", { class: "num" }, this._money(bill.actual)),
        h("span", {}, this._t("difference")),
        h("span", { class: "num" }, `${bill.difference > 0 ? "+" : ""}${this._money(bill.difference)}`),
        h("span", { class: "verdict" }, verdict),
      );
    }
    return [...parts.flat(), h("div", { class: "totals" }, totals)];
  }
}

if (!customElements.get("electricity-contracts-panel")) {
  customElements.define("electricity-contracts-panel", ElectricityContractsPanel);
}
