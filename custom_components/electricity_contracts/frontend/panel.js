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
    livePrice: "Price now",
    livePriceHint: "{contract} · the next 24 hours",
    until: "Until {time}, then {tranche} at {price}",
    untilUnknown: "Until {time}, then not published yet",
    cheapestNow: "The cheapest time of the next 24 hours",
    cheaperFrom: "Cheaper from {time}: {price}",
    singlePrice: "One price all day: no better time",
    nowLabel: "Now",
    unknownColor: "Color not published yet",
    perKwh: "{price}/kWh",
    budget: "Season budget {season}",
    budgetHint: "1 September to 31 August · {contract}",
    budgetTotal: "Expected for the whole season",
    budgetSpent: "Spent up to {day}",
    budgetRest: "Expected up to 31 August",
    budgetPrevious: "Last season",
    budgetToDate: "Last season at the same date",
    budgetPartial: "The data starts after 1 September: the season so far is partial.",
    budgetMethod: "The rest of the season consumes like the same days a year before (a day only known in total is spread like your typical day), at today's prices; the red and white days left go to the days that consumed the most.",
    budgetNoProjection: "Not enough data a year before to project the rest of the season.",
    budgetVsPrevious: "{change} vs last season",
    spentLegend: "Spent",
    expectedLegend: "Expected",
    temperatureStrip: "Average outdoor temperature",
    temperature: "Temperature",
    weather: "Consumption and weather",
    weatherHint: "Each dot is a day: its average outdoor temperature and what it consumed",
    weatherSetup: "Choose an outdoor temperature sensor in the integration's options to compare the consumption with the weather.",
    weatherOpen: "Open the options",
    weatherNoData: "No outdoor temperature recorded over this period.",
    weatherFewDays: "Too few days to tell the heating apart.",
    heating: "Heating",
    heatingValue: "{energy} per degree day",
    withoutHeating: "Without heating",
    perDay: "{energy} a day",
    coldShare: "Due to the cold",
    degreeDays: "Degree days (below {base})",
    meanTemperature: "Average temperature",
    dailyTemperature: "Average temperature of the day",
    weatherNote: "A degree day is one degree below 18 °C for a day. Compare the slope from one winter to the next to see what insulation or a heating setting changed.",
    dayDots: "Days",
    trend: "Trend",
    baseload: "Baseload",
    baseloadHint: "What runs all the time: the consumption between 3:00 and 5:00 on the quietest nights",
    weekOf: "Week of {day}",
    baseloadYear: "Over a year",
    baseloadShare: "Share of the consumption",
    baseloadCostHint: "At the prices of the last 12 months",
    tabActual: "Actual cost",
    tabBill: "Phantom bill",
    vsPrevious: "{change} vs the period before",
    tomorrow: "Tomorrow",
    today: "Today: {color}",
    notPublished: "Not published yet",
    estimate: "About {energy} and {cost}, going by your recent {weekday}s",
    estimateEnergy: "About {energy}, going by your recent {weekday}s",
    season: "Tempo season {season}",
    daysLeft: "{left} left out of {total}",
    redDaysCard: "Red days",
    noRedDay: "No red day over this period.",
    redDaysCount: "Red days",
    redDaysCost: "What they cost",
    redDaysPeak: "Peak hours per red day",
    redDaysPeakHint: "{other} on the other days ({change})",
    topDays: "Most expensive days",
    day: "Day",
    calendar: "Calendar",
    calendarHint: "One square per day: the darker, the more it cost",
    calendarHintTempo: "One square per day, in its Tempo color: the darker, the more it cost",
    profile: "A typical day",
    profileHint: "Average consumption at each hour",
    profileOffPeak: "{share} of your consumption falls in off-peak hours",
    offPeak: "Off-peak hours",
    peak: "Peak hours",
    priceRise: "With the same consumption, today's prices cost {amount} more per year than the ones before ({change}).",
    priceDrop: "With the same consumption, today's prices cost {amount} less per year than the ones before ({change}).",
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
    livePrice: "Prix en direct",
    livePriceHint: "{contract} · les prochaines 24 h",
    until: "Jusqu'à {time}, puis {tranche} à {price}",
    untilUnknown: "Jusqu'à {time}, puis couleur pas encore publiée",
    cheapestNow: "Le moment le moins cher des prochaines 24 h",
    cheaperFrom: "Moins cher à partir de {time} : {price}",
    singlePrice: "Un seul prix toute la journée : pas de meilleur moment",
    nowLabel: "Maintenant",
    unknownColor: "Couleur pas encore publiée",
    perKwh: "{price}/kWh",
    budget: "Budget de la saison {season}",
    budgetHint: "Du 1er septembre au 31 août · {contract}",
    budgetTotal: "Prévu pour toute la saison",
    budgetSpent: "Dépensé jusqu'au {day}",
    budgetRest: "Prévu d'ici au 31 août",
    budgetPrevious: "Saison dernière",
    budgetToDate: "Saison dernière à la même date",
    budgetPartial: "Les données commencent après le 1er septembre : le début de saison est incomplet.",
    budgetMethod: "Le reste de la saison consomme comme les mêmes jours l'an dernier (un jour connu seulement en total est réparti selon votre journée type), aux prix d'aujourd'hui ; les jours rouges et blancs restants vont aux jours qui ont le plus consommé.",
    budgetNoProjection: "Pas assez de données l'an dernier pour prévoir la fin de la saison.",
    budgetVsPrevious: "{change} vs la saison dernière",
    spentLegend: "Dépensé",
    expectedLegend: "Prévu",
    temperatureStrip: "Température extérieure moyenne",
    temperature: "Température",
    weather: "Consommation et météo",
    weatherHint: "Chaque point est un jour : sa température extérieure moyenne et ce qu'il a consommé",
    weatherSetup: "Choisissez un capteur de température extérieure dans les options de l'intégration pour comparer la consommation à la météo.",
    weatherOpen: "Ouvrir les options",
    weatherNoData: "Aucune température extérieure enregistrée sur cette période.",
    weatherFewDays: "Trop peu de jours pour isoler le chauffage.",
    heating: "Chauffage",
    heatingValue: "{energy} par degré-jour",
    withoutHeating: "Hors chauffage",
    perDay: "{energy} par jour",
    coldShare: "Part due au froid",
    degreeDays: "Degrés-jours (sous {base})",
    meanTemperature: "Température moyenne",
    dailyTemperature: "Température moyenne du jour",
    weatherNote: "Un degré-jour, c'est 1 °C sous 18 °C pendant une journée. Comparez la pente d'un hiver à l'autre pour mesurer l'effet d'une isolation ou d'un réglage du chauffage.",
    dayDots: "Jours",
    trend: "Tendance",
    baseload: "Talon de consommation",
    baseloadHint: "Ce qui tourne en permanence : la consommation entre 3 h et 5 h des nuits les plus calmes",
    weekOf: "Semaine du {day}",
    baseloadYear: "Sur un an",
    baseloadShare: "Part de la consommation",
    baseloadCostHint: "Aux prix des 12 derniers mois",
    tabActual: "Coût réel",
    tabBill: "Facture fantôme",
    vsPrevious: "{change} vs la période précédente",
    tomorrow: "Demain",
    today: "Aujourd'hui : {color}",
    notPublished: "Pas encore publiée",
    estimate: "Environ {energy} et {cost}, d'après vos derniers {weekday}s",
    estimateEnergy: "Environ {energy}, d'après vos derniers {weekday}s",
    season: "Saison Tempo {season}",
    daysLeft: "{left} restants sur {total}",
    redDaysCard: "Jours rouges",
    noRedDay: "Aucun jour rouge sur cette période.",
    redDaysCount: "Jours rouges",
    redDaysCost: "Ce qu'ils ont coûté",
    redDaysPeak: "Heures pleines par jour rouge",
    redDaysPeakHint: "{other} les autres jours ({change})",
    topDays: "Journées les plus chères",
    day: "Jour",
    calendar: "Calendrier",
    calendarHint: "Un carré par jour : plus il est foncé, plus la journée a coûté",
    calendarHintTempo: "Un carré par jour, à sa couleur Tempo : plus il est foncé, plus la journée a coûté",
    profile: "Une journée type",
    profileHint: "Consommation moyenne à chaque heure",
    profileOffPeak: "{share} de votre consommation tombe en heures creuses",
    offPeak: "Heures creuses",
    peak: "Heures pleines",
    priceRise: "À consommation identique, les prix actuels coûtent {amount} de plus par an que les précédents ({change}).",
    priceDrop: "À consommation identique, les prix actuels coûtent {amount} de moins par an que les précédents ({change}).",
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

const COLORS = {
  en: { blue: "Blue", white: "White", red: "Red" },
  fr: { blue: "Bleu", white: "Blanc", red: "Rouge" },
};

// Tempo day colors, readable on both surfaces.
const DAY_FILLS = { blue: "#3987e5", white: "#a3a29a", red: "#e34948" };

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
.pair { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.big { font-size: 22px; font-weight: 600; display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.big .swatch { width: 14px; height: 14px; border-radius: 3px; }
.meter { margin-top: 10px; }
.meter .row { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; color: var(--ec-text-2); margin-bottom: 4px; }
.meter .row strong { color: var(--ec-text); font-weight: 500; }
.meter .track { height: 8px; border-radius: 4px; background: var(--ec-wash); overflow: hidden; }
.meter .fill { height: 100%; border-radius: 4px; }
.sub { color: var(--ec-text-2); font-size: 13px; }
.note.good { color: var(--ec-good); display: flex; align-items: center; gap: 6px; }
.note.good svg { width: 16px; height: 16px; fill: currentColor; flex: none; }
.ribbon { display: flex; gap: 2px; height: 28px; margin-top: 12px; }
.ribbon .unknown {
  background: repeating-linear-gradient(135deg, var(--ec-grid) 0 4px, transparent 4px 8px);
  box-shadow: inset 0 0 0 1px var(--ec-grid);
  color: var(--ec-text-2);
}
.ribbon-ticks { position: relative; height: 18px; font-size: 12px; color: var(--ec-muted); }
.ribbon-ticks span { position: absolute; top: 4px; white-space: nowrap; }
.budget-bar { position: relative; display: flex; gap: 2px; height: 16px; margin: 14px 0 8px; border-radius: 4px; background: var(--ec-wash); }
.budget-bar .spent { background: var(--ec-s1); border-radius: 4px 0 0 4px; }
.budget-bar .rest { background: repeating-linear-gradient(135deg, var(--ec-s1) 0 2px, transparent 2px 6px); box-shadow: inset 0 0 0 1px var(--ec-s1); border-radius: 0 4px 4px 0; }
.budget-bar .alone { border-radius: 4px; }
.budget-bar .marker { position: absolute; top: -4px; bottom: -4px; width: 2px; margin-left: -1px; background: var(--ec-text); border-radius: 1px; }
.swatch.hatched { background: repeating-linear-gradient(135deg, var(--ec-s1) 0 2px, transparent 2px 4px); box-shadow: inset 0 0 0 1px var(--ec-s1); }
.swatch.round { border-radius: 50%; }
.tick-key { width: 2px; height: 12px; border-radius: 1px; background: var(--ec-text); flex: none; }
.meters { margin-top: 12px; }
.chart text.strip-title { fill: var(--ec-text-2); font-size: 13px; }
.chart + .facts, .facts + .chart { margin-top: 12px; }
a.toggle { display: inline-block; margin-top: 8px; text-decoration: none; }
.facts { display: grid; grid-template-columns: 1fr auto; gap: 6px 16px; font-size: 14px; }
.facts .num { text-align: right; font-weight: 500; font-variant-numeric: tabular-nums; }
.facts .hint { grid-column: 1 / -1; margin: -4px 0 0; text-align: right; }
.scroll { overflow-x: auto; }
.calendar rect { stroke: var(--ec-surface); stroke-width: 1px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 13px; }
.chip { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; color: var(--ec-text-2); }
.chip strong { color: var(--ec-text); font-weight: 500; font-variant-numeric: tabular-nums; }
.details { margin-top: 12px; padding-top: 8px; border-top: 1px solid var(--divider-color, var(--ec-grid)); }
.legend { display: flex; flex-wrap: wrap; gap: 4px 16px; margin: 0 0 8px; padding: 0; list-style: none; font-size: 13px; color: var(--ec-text-2); }
.legend li { display: inline-flex; align-items: center; gap: 6px; }
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
  check: "M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z",
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
    this._insights = null;
    this._outlook = null;
    this._outlookTimer = null;
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
    clearTimeout(this._outlookTimer);
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

  _percent(value) {
    return new Intl.NumberFormat(this._locale, { style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" }).format(value);
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
    this._refreshOutlook();
    await this._load();
  }

  _refreshOutlook() {
    this._outlook = null;
    this._loadOutlook().then(() => {
      if (this._data && this._tab === "compare") this._renderContent();
    });
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
      const request = { entry_id: entry.entry_id, start: window.start, end: window.end };
      const [data, insights] = await Promise.all([
        this._hass.callWS({ type: `${DOMAIN}/compare`, ...request }),
        // The page stands without them.
        this._hass.callWS({ type: `${DOMAIN}/insights`, ...request }).catch(() => null),
      ]);
      if (count !== this._loadCount) return;
      this._request = window;
      this._data = data;
      this._insights = insights;
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
          this._refreshOutlook();
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
    this._calendarChart = null;
    this._profileChart = null;
    this._weatherChart = null;
    this._baseloadChart = null;
    if (this._tab === "bill") {
      this._content.replaceChildren(...this._renderBillTab());
    } else if (!this._data.actual) {
      this._content.replaceChildren(h("section", { class: "card message" }, this._t("noContractInForce")));
    } else {
      this._timeChart = h("div", { class: "chart" });
      const inForce = this._contractsInForce();
      const insights = this._insights;
      const live = this._renderLive();
      const tomorrow = insights && insights.tempo ? this._renderTomorrow(insights.tempo) : null;
      const cards = [
        ...this._renderContractCards(inForce),
        live || tomorrow ? h("div", { class: "pair" }, live, tomorrow) : null,
        this._renderBudget(),
        this._renderKpis(),
        this._card(this._t("costOverTime"), this._t(this._data.group_by === "month" ? "costPerMonth" : "costPerDay"), this._timeChart, this._toggle("time")),
      ].filter(Boolean);
      if (insights && insights.days.length) {
        const tempo = insights.days.some((day) => day.color);
        this._calendarChart = h("div", { class: "scroll" });
        this._profileChart = h("div", { class: "chart" });
        cards.push(
          this._card(this._t("calendar"), this._t(tempo ? "calendarHintTempo" : "calendarHint"), this._calendarChart),
          h("div", { class: "pair" }, tempo ? this._renderRedDays(insights.days) : null, this._renderTopDays(insights.days)),
          this._card(this._t("profile"), this._t("profileHint"), this._profileChart),
          this._renderBaseload(),
          this._renderWeather(),
        );
      }
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
    const tile = (label, value, ...subs) =>
      h(
        "section",
        { class: "card kpi" },
        h("div", { class: "label" }, label),
        h("div", { class: "value" }, value),
        subs.filter(Boolean).map((sub) => h("div", { class: "sub" }, sub)),
      );
    const previous = this._insights && this._insights.previous;
    const change = (value, before) => (previous && before ? this._t("vsPrevious", { change: this._percent(value / before - 1) }) : null);
    return h(
      "div",
      { class: "kpis" },
      tile(
        this._t("actualCost"),
        this._money(actual.total_cost),
        this._t("ofWhichSubscription", { amount: this._money(actual.fixed_cost) }),
        change(actual.total_cost, previous && previous.cost),
      ),
      tile(this._t("consumption"), this._kwh(actual.energy), change(actual.energy, previous && previous.energy)),
      tile(this._t("average"), actual.energy ? `${this._price(actual.variable_cost / actual.energy)}/kWh` : "—", this._t("withoutSubscription")),
    );
  }

  // The contracts in force today, with the prices they have had.
  _renderContractCards(inForce) {
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
        const rise = current > 0 && inForce.length === 1 && inForce[0].id === contract.id ? this._priceRise(inForce[0], periods[current], periods[current - 1]) : null;
        return this._card(title, facts.filter(Boolean).join(" · "), h("div", {}, chips, rise, details), toggle);
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
    if (this._calendarChart) {
      this._drawCalendar(this._calendarChart, this._insights.days);
    }
    if (this._profileChart) {
      this._drawProfile(this._profileChart, this._insights.profile);
    }
    if (this._baseloadChart) {
      this._drawNights(this._baseloadChart, this._insights.baseload);
    }
    if (this._weatherChart) {
      this._drawWeather(this._weatherChart, this._insights);
    }
  }

  _renderTimeChart() {
    const actual = { id: ACTUAL, name: this._t("actual") };
    const partial = this._data.series.some((bucket) => bucket.actual === null);
    const temperatures = this._bucketTemperatures();
    if (this._views.time === "chart") {
      const series = [{ ...actual, values: this._data.series.map((bucket) => bucket.actual ?? 0) }];
      const frame =
        this._data.group_by === "month"
          ? this._drawColumns(this._timeChart, series, temperatures)
          : this._drawLines(this._timeChart, series, { zero: false, temperatures });
      if (temperatures) {
        this._timeChart.append(this._temperatureStrip(frame, temperatures));
      }
    } else {
      const extra = temperatures && { label: this._t("temperature"), values: temperatures, format: (value) => this._degrees(value) };
      this._timeChart.replaceChildren(this._seriesTable((bucket) => bucket.actual, false, [actual], extra));
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

  _drawColumns(container, series, temperatures = null) {
    const values = series.flatMap((item) => item.values);
    const frame = this._frame(container, values, false);
    frame.temperatures = temperatures;
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
    return frame;
  }

  _drawLines(container, series, { zero, temperatures = null }) {
    const values = series.flatMap((item) => item.values);
    const frame = this._frame(container, values, zero);
    frame.temperatures = temperatures;
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
    return frame;
  }

  _showTooltip(tooltip, frame, index, series, anchor) {
    const bucket = this._data.series[index];
    const rows = [...series]
      .map((item) => ({ item, value: item.values[index] }))
      .sort((first, second) => second.value - first.value)
      .map(({ item, value }) =>
        h("div", { class: "row" }, h("span", { class: "line-key", style: { background: this._color(item.id) } }), h("strong", {}, this._money(value)), h("span", {}, item.name)),
      );
    const temperature = frame.temperatures ? frame.temperatures[index] : null;
    if (temperature !== null) {
      rows.push(h("div", { class: "row" }, h("span", { class: "line-key", style: { background: "var(--ec-s2)" } }), h("strong", {}, this._degrees(temperature)), h("span", {}, this._t("temperature"))));
    }
    tooltip.replaceChildren(h("div", { class: "head" }, this._bucketLabel(bucket.start, true)), ...rows);
    tooltip.hidden = false;
    const width = tooltip.offsetWidth;
    const left = anchor + 12 + width > frame.width ? anchor - 12 - width : anchor + 12;
    tooltip.style.left = `${Math.max(0, left)}px`;
    tooltip.style.top = `${frame.margin.top}px`;
  }

  _seriesTable(value, withActual, contracts = this._data.contracts, extra = null) {
    const head = h(
      "tr",
      {},
      h("th", {}, this._t("period")),
      contracts.map((contract) => h("th", {}, contract.name)),
      withActual && this._data.actual ? h("th", {}, this._t("actual")) : null,
      extra ? h("th", {}, extra.label) : null,
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
        extra ? h("td", {}, extra.values[index] === null ? "—" : extra.format(extra.values[index])) : null,
      ),
    );
    return h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, head), h("tbody", {}, rows)));
  }

  // What today's prices change over a year, with the consumption of the period.
  _priceRise(costed, now, before) {
    const days = (Date.parse(this._data.end) - Date.parse(this._data.start)) / DAY_MS;
    if (!(days > 0)) return null;
    const yearly = (period) =>
      Object.entries(costed.tranches).reduce((sum, [tranche, item]) => sum + item.energy * (period.tranches[tranche] ?? 0), 0) * (365 / days) + period.fixed_per_year;
    const difference = yearly(now) - yearly(before);
    if (Math.abs(difference) < 0.5) return null;
    return h(
      "p",
      { class: "note" },
      this._t(difference > 0 ? "priceRise" : "priceDrop", { amount: this._money(Math.abs(difference), 0), change: this._percent(difference / yearly(before)) }),
    );
  }

  // Price now and season budget -------------------------------------------------

  async _loadOutlook() {
    clearTimeout(this._outlookTimer);
    const entry = this._entry;
    if (!entry || !entry.contracts.length) {
      this._outlook = null;
      return;
    }
    try {
      this._outlook = await this._hass.callWS({ type: `${DOMAIN}/outlook`, entry_id: entry.entry_id });
    } catch (error) {
      // The page stands without it.
      this._outlook = null;
    }
    // Again when the price changes, and at least every half hour.
    const first = this._outlook && this._outlook.prices[0];
    const wait = first ? Date.parse(first.end) - Date.now() + 5000 : Infinity;
    this._outlookTimer = setTimeout(
      () => this._loadOutlook().then(() => this._tab === "compare" && this._renderContent()),
      Math.max(60000, Math.min(wait, 30 * 60000)),
    );
  }

  _time(iso) {
    return new Intl.DateTimeFormat(this._locale, { hour: "numeric", minute: "2-digit", timeZone: "Europe/Paris" }).format(new Date(iso));
  }

  _degrees(value) {
    return `${this._number(value, 1)} °C`;
  }

  _renderLive() {
    const outlook = this._outlook;
    if (!outlook || !outlook.contract || !outlook.prices.length) return null;
    const names = TRANCHES[this._language];
    const segments = outlook.prices;
    const [current, next] = segments;
    const name = (tranche) => (tranche ? names[tranche] : this._t("unknownColor"));
    const perKwh = (price) => this._t("perKwh", { price: this._price(price) });
    const priced = segments.filter((segment) => segment.price !== null);
    const cheapest = priced.length ? Math.min(...priced.map((segment) => segment.price)) : null;
    let verdict = null;
    if (segments.length === 1 && current.price !== null) {
      verdict = h("p", { class: "note" }, this._t("singlePrice"));
    } else if (current.price !== null && current.price <= cheapest + 1e-9) {
      verdict = h("p", { class: "note good" }, icon(ICONS.check), this._t("cheapestNow"));
    } else if (cheapest !== null) {
      const when = priced.find((segment) => segment.price === cheapest);
      verdict = h("p", { class: "note" }, this._t("cheaperFrom", { time: this._time(when.start), price: perKwh(cheapest) }));
    }
    let then = null;
    if (next) {
      then =
        next.price === null
          ? this._t("untilUnknown", { time: this._time(current.end) })
          : this._t("until", { time: this._time(current.end), tranche: name(next.tranche), price: perKwh(next.price) });
    }
    const start = Date.parse(segments[0].start);
    const span = Date.parse(segments[segments.length - 1].end) - start;
    const share = (segment) => (Date.parse(segment.end) - Date.parse(segment.start)) / span;
    const describe = (segment) =>
      [`${this._time(segment.start)} – ${this._time(segment.end)}`, name(segment.tranche), segment.price !== null ? perKwh(segment.price) : null].filter(Boolean).join(" · ");
    const ribbon = h(
      "div",
      { class: "ribbon", role: "img", "aria-label": segments.map(describe).join(", ") },
      segments.map((segment) => {
        const [fill, ink] = segment.tranche ? TRANCHE_FILLS[segment.tranche] : [];
        return h(
          "div",
          { class: segment.tranche ? "segment" : "segment unknown", title: describe(segment), style: { flex: `${share(segment)} 1 0`, ...(fill ? { background: fill, color: ink } : {}) } },
          share(segment) > 0.14 ? name(segment.tranche) : "",
        );
      }),
    );
    // A time under each change of price, unless too close to the one before.
    let shown = -1;
    const ticks = h(
      "div",
      { class: "ribbon-ticks", "aria-hidden": "true" },
      segments.map((segment, index) => {
        const left = (Date.parse(segment.start) - start) / span;
        if (index > 0 && (left - shown < 0.12 || left > 0.9)) return null;
        shown = left;
        return h("span", { style: { left: `${left * 100}%` } }, index === 0 ? this._t("nowLabel") : this._time(segment.start));
      }),
    );
    return this._card(
      this._t("livePrice"),
      this._t("livePriceHint", { contract: outlook.contract.name }),
      h(
        "div",
        {},
        h(
          "div",
          { class: "big" },
          current.tranche ? h("span", { class: "swatch", style: { background: TRANCHE_FILLS[current.tranche][0] } }) : null,
          current.price !== null ? perKwh(current.price) : "—",
        ),
        h("div", { class: "sub" }, [name(current.tranche), then].filter(Boolean).join(" · ")),
        verdict,
        ribbon,
        ticks,
      ),
    );
  }

  // Tomorrow's color with what it should cost.
  _renderTomorrow(tempo) {
    const colors = COLORS[this._language];
    const tomorrow = new Date(Date.now() + DAY_MS);
    const weekday = new Intl.DateTimeFormat(this._locale, { weekday: "long" }).format(tomorrow);
    const estimate = tempo.tomorrow_estimate;
    let hint = null;
    if (estimate && estimate.cost !== null) {
      hint = this._t("estimate", { energy: this._kwh(estimate.energy), cost: this._money(estimate.cost), weekday });
    } else if (estimate) {
      hint = this._t("estimateEnergy", { energy: this._kwh(estimate.energy), weekday });
    }
    return this._card(
      this._t("tomorrow"),
      tempo.today ? this._t("today", { color: colors[tempo.today] }) : null,
      h(
        "div",
        {},
        h(
          "div",
          { class: "big" },
          tempo.tomorrow ? h("span", { class: "swatch", style: { background: DAY_FILLS[tempo.tomorrow] } }) : null,
          tempo.tomorrow ? colors[tempo.tomorrow] : this._t("notPublished"),
        ),
        hint ? h("p", { class: "note" }, hint) : null,
      ),
    );
  }

  // The red and white days left in the Tempo season.
  _tempoMeters(tempo) {
    const colors = COLORS[this._language];
    const season = tempo.season;
    const meter = (color, left, total) =>
      h(
        "div",
        { class: "meter" },
        h("div", { class: "row" }, h("span", {}, colors[color]), h("strong", {}, this._t("daysLeft", { left, total }))),
        h("div", { class: "track", role: "img", "aria-label": `${colors[color]}: ${left}/${total}` }, h("div", { class: "fill", style: { width: `${(left / total) * 100}%`, background: DAY_FILLS[color] } })),
      );
    return h("div", { class: "meters" }, meter("red", season.red_left, season.red_total), meter("white", season.white_left, season.white_total));
  }

  // What the season has cost so far, and what it should cost by 31 August.
  _renderBudget() {
    const tempo = this._insights && this._insights.tempo;
    const season = this._outlook && this._outlook.season;
    if (!season) {
      if (!tempo) return null;
      const label = `${tempo.season.start.slice(0, 4)}-${tempo.season.end.slice(0, 4)}`;
      return this._card(this._t("season", { season: label }), null, this._tempoMeters(tempo));
    }
    const label = `${season.start.slice(0, 4)}-${season.end.slice(0, 4)}`;
    const until = this._dayLabel(season.until, { day: "numeric", month: "long" });
    const { total, previous, projection, spent } = season;
    const scale = Math.max(total ?? spent.cost, previous ? previous.total : 0, 1) * 1.04;
    const width = (amount) => `${(amount / scale) * 100}%`;
    const bar = h(
      "div",
      {
        class: "budget-bar",
        role: "img",
        "aria-label": [
          `${this._t("spentLegend")} ${this._money(spent.cost, 0)}`,
          projection ? `${this._t("expectedLegend")} ${this._money(projection.cost, 0)}` : null,
          previous ? `${this._t("budgetPrevious")} ${this._money(previous.total, 0)}` : null,
        ]
          .filter(Boolean)
          .join(", "),
      },
      spent.cost > 0 ? h("div", { class: projection ? "spent" : "spent alone", style: { width: width(spent.cost) } }) : null,
      projection ? h("div", { class: spent.cost > 0 ? "rest" : "rest alone", style: { width: width(projection.cost) } }) : null,
      previous ? h("div", { class: "marker", style: { left: width(previous.total) } }) : null,
    );
    const legend = h(
      "ul",
      { class: "legend" },
      h("li", {}, h("span", { class: "swatch", style: { background: "var(--ec-s1)" } }), this._t("spentLegend")),
      projection ? h("li", {}, h("span", { class: "swatch hatched" }), this._t("expectedLegend")) : null,
      previous ? h("li", {}, h("span", { class: "tick-key" }), this._t("budgetPrevious")) : null,
    );
    const facts = h(
      "div",
      { class: "facts" },
      h("span", {}, this._t("budgetSpent", { day: until })),
      h("span", { class: "num" }, this._money(spent.cost)),
      projection ? [h("span", {}, this._t("budgetRest")), h("span", { class: "num" }, this._money(projection.cost))] : null,
      previous ? [h("span", {}, this._t("budgetToDate")), h("span", { class: "num" }, this._money(previous.to_date))] : null,
      previous ? [h("span", {}, this._t("budgetPrevious")), h("span", { class: "num" }, this._money(previous.total))] : null,
    );
    const notes = [!season.complete ? this._t("budgetPartial") : null, projection ? this._t("budgetMethod") : this._t("budgetNoProjection")];
    // Spent alone needs neither a bar nor a breakdown.
    const detailed = Boolean(projection || previous);
    return this._card(
      this._t("budget", { season: label }),
      this._t("budgetHint", { contract: this._outlook.contract.name }),
      h(
        "div",
        {},
        h("div", { class: "big" }, total !== null ? `≈ ${this._money(total, 0)}` : this._money(spent.cost, 0)),
        h(
          "div",
          { class: "sub" },
          [total !== null ? this._t("budgetTotal") : this._t("budgetSpent", { day: until }), total !== null && previous ? this._t("budgetVsPrevious", { change: this._percent(total / previous.total - 1) }) : null]
            .filter(Boolean)
            .join(" · "),
        ),
        detailed ? [bar, legend, facts] : null,
        tempo ? this._tempoMeters(tempo) : null,
        notes.filter(Boolean).map((note) => h("p", { class: "note" }, note)),
      ),
    );
  }

  // The outdoor temperature of each day or month of the time chart.
  _bucketTemperatures() {
    const days = (this._insights && this._insights.days) || [];
    if (!days.some((day) => day.temperature !== null)) return null;
    const month = this._data.group_by === "month";
    const sums = new Map();
    for (const day of days) {
      if (day.temperature === null) continue;
      const key = month ? day.date.slice(0, 7) : day.date;
      const sum = sums.get(key) || [0, 0];
      sum[0] += day.temperature;
      sum[1] += 1;
      sums.set(key, sum);
    }
    return this._data.series.map((bucket) => {
      const sum = sums.get(month ? bucket.start.slice(0, 7) : bucket.start.slice(0, 10));
      return sum ? sum[0] / sum[1] : null;
    });
  }

  // A second chart under the costs, on the same days or months: never two
  // scales on one chart.
  _temperatureStrip(frame, temperatures) {
    const { width, margin, x } = frame;
    const known = temperatures.filter((value) => value !== null);
    const height = 128;
    const top = 36;
    const bottom = 8;
    const ticks = niceTicks(Math.min(...known), Math.max(...known), 3);
    const low = ticks[0];
    const high = ticks[ticks.length - 1];
    const plot = height - top - bottom;
    const y = (value) => top + plot - ((value - low) / (high - low || 1)) * plot;
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": this._t("temperatureStrip") });
    root.append(s("text", { x: margin.left, y: 20, class: "strip-title" }, this._t("temperatureStrip")));
    for (const tick of ticks) {
      root.append(
        s("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), style: { stroke: "var(--ec-grid)", "stroke-width": "1px" } }),
        s("text", { x: margin.left - 8, y: y(tick), "text-anchor": "end", "dominant-baseline": "middle" }, `${this._number(tick)} °C`),
      );
    }
    let path = "";
    let drawing = false;
    temperatures.forEach((value, index) => {
      if (value === null) {
        drawing = false;
        return;
      }
      path += `${drawing ? "L" : "M"}${x(index)},${y(value)}`;
      drawing = true;
    });
    root.append(s("path", { d: path, style: { fill: "none", stroke: "var(--ec-s2)", "stroke-width": "2px", "stroke-linejoin": "round", "stroke-linecap": "round" } }));
    temperatures.forEach((value, index) => {
      const alone = (temperatures[index - 1] ?? null) === null && (temperatures[index + 1] ?? null) === null;
      if (value === null || (this._data.group_by !== "month" && !alone)) return;
      root.append(s("circle", { cx: x(index), cy: y(value), r: 4, style: { fill: "var(--ec-s2)", stroke: "var(--ec-surface)", "stroke-width": "2px" } }));
    });
    return root;
  }

  // Consumption and weather ------------------------------------------------------

  _renderWeather() {
    const insights = this._insights;
    const weather = insights.weather;
    const head = (body) => this._card(this._t("weather"), weather && weather.days ? this._t("weatherHint") : null, body);
    if (!weather) {
      return head(
        h(
          "div",
          {},
          h("p", { class: "message" }, this._t("weatherSetup")),
          h("a", { class: "toggle", href: `/config/integrations/integration/${DOMAIN}` }, this._t("weatherOpen")),
        ),
      );
    }
    if (!weather.days) {
      return head(h("p", { class: "message" }, this._t("weatherNoData")));
    }
    const kwh = (value) => `${this._number(value, 1)} kWh`;
    const facts = h(
      "div",
      { class: "facts" },
      weather.slope !== null && weather.slope > 0
        ? [
            h("span", {}, this._t("heating")),
            h("span", { class: "num" }, this._t("heatingValue", { energy: kwh(weather.slope) })),
            h("span", {}, this._t("withoutHeating")),
            h("span", { class: "num" }, this._t("perDay", { energy: kwh(Math.max(0, weather.intercept)) })),
          ]
        : null,
      weather.heating_share !== null ? [h("span", {}, this._t("coldShare")), h("span", { class: "num" }, this._percent(weather.heating_share).replace("+", ""))] : null,
      h("span", {}, this._t("degreeDays", { base: `${this._number(weather.base)} °C` })),
      h("span", { class: "num" }, this._number(weather.degree_days)),
      h("span", {}, this._t("meanTemperature")),
      h("span", { class: "num" }, this._degrees(weather.mean_temperature)),
    );
    this._weatherChart = h("div", { class: "chart" });
    return head(
      h(
        "div",
        {},
        this._weatherChart,
        facts,
        weather.slope === null ? h("p", { class: "note" }, this._t("weatherFewDays")) : h("p", { class: "note" }, this._t("weatherNote")),
      ),
    );
  }

  _drawWeather(container, insights) {
    const weather = insights.weather;
    const points = insights.days.filter((day) => day.temperature !== null);
    const width = Math.max(container.clientWidth || 320, 240);
    const height = 240;
    const margin = { top: 8, right: 12, bottom: 40, left: 56 };
    const temperatures = points.map((point) => point.temperature);
    const xTicks = niceTicks(Math.min(...temperatures), Math.max(...temperatures), width < 500 ? 4 : 6);
    const yTicks = niceTicks(0, Math.max(...points.map((point) => point.energy), 0.01), 4);
    const low = xTicks[0];
    const high = xTicks[xTicks.length - 1];
    const top = yTicks[yTicks.length - 1];
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const x = (value) => margin.left + ((value - low) / (high - low || 1)) * plotWidth;
    const y = (value) => margin.top + plotHeight - (value / top) * plotHeight;
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": this._t("weather") });
    for (const tick of yTicks) {
      root.append(
        s("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), style: { stroke: tick === 0 ? "var(--ec-axis)" : "var(--ec-grid)", "stroke-width": "1px" } }),
        s("text", { x: margin.left - 8, y: y(tick), "text-anchor": "end", "dominant-baseline": "middle" }, `${this._number(tick)} kWh`),
      );
    }
    for (const tick of xTicks) {
      root.append(s("text", { x: x(tick), y: height - 22, "text-anchor": "middle" }, `${this._number(tick)} °C`));
    }
    root.append(s("text", { x: margin.left + plotWidth / 2, y: height - 4, "text-anchor": "middle" }, this._t("dailyTemperature")));
    const colors = COLORS[this._language];
    for (const point of points) {
      const what = [this._dayLabel(point.date, { weekday: "long", day: "numeric", month: "long" }), point.color ? colors[point.color] : null, this._degrees(point.temperature), `${this._number(point.energy, 1)} kWh`];
      root.append(
        s(
          "circle",
          { cx: x(point.temperature), cy: y(point.energy), r: 4, class: "dot", style: { fill: "var(--ec-s1)", "fill-opacity": "0.75", stroke: "var(--ec-surface)", "stroke-width": "1px" } },
          s("title", {}, what.filter(Boolean).join(" · ")),
        ),
      );
    }
    const trend = weather.slope !== null && weather.slope > 0;
    if (trend) {
      const model = (value) => weather.intercept + weather.slope * Math.max(0, weather.base - value);
      const knots = [low, ...(weather.base > low && weather.base < high ? [weather.base] : []), high];
      root.append(
        s("polyline", {
          points: knots.map((value) => `${x(value)},${y(Math.max(0, model(value)))}`).join(" "),
          style: { fill: "none", stroke: "var(--ec-s2)", "stroke-width": "2px", "stroke-linejoin": "round", "stroke-linecap": "round" },
        }),
      );
    }
    const legend = h(
      "ul",
      { class: "legend" },
      h("li", {}, h("span", { class: "swatch round", style: { background: "var(--ec-s1)" } }), this._t("dayDots")),
      trend ? h("li", {}, h("span", { class: "line-key", style: { background: "var(--ec-s2)" } }), this._t("trend")) : null,
    );
    container.replaceChildren(legend, root);
  }

  // Baseload -----------------------------------------------------------------------

  _renderBaseload() {
    const baseload = this._insights.baseload;
    if (!baseload) return null;
    const year = [this._kwh(baseload.annual_energy), baseload.annual_cost !== null ? this._money(baseload.annual_cost, 0) : null].filter(Boolean).join(" · ");
    this._baseloadChart = baseload.nights.length > 1 ? h("div", { class: "chart" }) : null;
    return this._card(
      this._t("baseload"),
      this._t("baseloadHint"),
      h(
        "div",
        {},
        h("div", { class: "big" }, `${this._number(baseload.power)} W`),
        h(
          "div",
          { class: "facts" },
          h("span", {}, this._t("baseloadYear")),
          h("span", { class: "num" }, year),
          baseload.annual_cost !== null ? h("p", { class: "hint" }, this._t("baseloadCostHint")) : null,
          baseload.share !== null ? [h("span", {}, this._t("baseloadShare")), h("span", { class: "num" }, this._percent(baseload.share).replace("+", ""))] : null,
        ),
        this._baseloadChart,
      ),
    );
  }

  // The quietest hour night after night, or week after week over a long period,
  // with the baseload the headline gives.
  _drawNights(container, baseload) {
    const weekly = baseload.nights.length > 62;
    let nights = baseload.nights;
    if (weekly) {
      const weeks = new Map();
      for (const night of nights) {
        const time = dayTime(night.date);
        const monday = dayString(time - ((new Date(time).getUTCDay() + 6) % 7) * DAY_MS);
        weeks.set(monday, Math.min(weeks.get(monday) ?? Infinity, night.power));
      }
      nights = [...weeks.entries()].map(([date, power]) => ({ date, power }));
    }
    const width = Math.max(container.clientWidth || 320, 240);
    const height = 120;
    const margin = { top: 16, right: 12, bottom: 22, left: 52 };
    const ticks = niceTicks(0, Math.max(...nights.map((night) => night.power), 1), 2);
    const high = ticks[ticks.length - 1];
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const step = plotWidth / Math.max(1, nights.length - 1);
    const x = (index) => margin.left + index * step;
    const y = (value) => margin.top + plotHeight - (value / high) * plotHeight;
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": this._t("baseload") });
    for (const tick of ticks) {
      root.append(
        s("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), style: { stroke: tick === 0 ? "var(--ec-axis)" : "var(--ec-grid)", "stroke-width": "1px" } }),
        s("text", { x: margin.left - 8, y: y(tick), "text-anchor": "end", "dominant-baseline": "middle" }, `${this._number(tick)} W`),
      );
    }
    const label = (night) => this._dayLabel(night.date, { day: "numeric", month: "short" });
    root.append(
      s("text", { x: x(0), y: height - 4, "text-anchor": "start" }, label(nights[0])),
      s("text", { x: x(nights.length - 1), y: height - 4, "text-anchor": "end" }, label(nights[nights.length - 1])),
      s("line", { x1: margin.left, x2: width - margin.right, y1: y(baseload.power), y2: y(baseload.power), style: { stroke: "var(--ec-text-2)", "stroke-width": "1px", "stroke-dasharray": "4 4" } }),
      s("polyline", {
        points: nights.map((night, index) => `${x(index)},${y(night.power)}`).join(" "),
        style: { fill: "none", stroke: "var(--ec-s1)", "stroke-width": "2px", "stroke-linejoin": "round", "stroke-linecap": "round" },
      }),
    );
    const dot = s("circle", { r: 4, style: { fill: "var(--ec-s1)", stroke: "var(--ec-surface)", "stroke-width": "2px", visibility: "hidden" } });
    const tooltip = h("div", { class: "tooltip", hidden: true });
    let focused = nights.length - 1;
    const show = (index) => {
      const night = nights[index];
      dot.setAttribute("cx", x(index));
      dot.setAttribute("cy", y(night.power));
      dot.style.visibility = "visible";
      const when = weekly
        ? this._t("weekOf", { day: this._dayLabel(night.date, { day: "numeric", month: "long", year: "numeric" }) })
        : this._dayLabel(night.date, { weekday: "long", day: "numeric", month: "long" });
      tooltip.replaceChildren(h("div", { class: "head" }, when), h("div", { class: "row" }, h("strong", {}, `${this._number(night.power)} W`)));
      tooltip.hidden = false;
      const left = x(index) + 12 + tooltip.offsetWidth > width ? x(index) - 12 - tooltip.offsetWidth : x(index) + 12;
      tooltip.style.left = `${Math.max(0, left)}px`;
      tooltip.style.top = "0px";
    };
    const hide = () => {
      dot.style.visibility = "hidden";
      tooltip.hidden = true;
    };
    root.append(
      dot,
      s("rect", {
        class: "hit",
        x: margin.left,
        y: margin.top,
        width: plotWidth,
        height: plotHeight,
        tabindex: 0,
        "aria-label": this._t("baseload"),
        onpointermove: (event) => {
          const box = root.getBoundingClientRect();
          focused = Math.max(0, Math.min(nights.length - 1, Math.round((event.clientX - box.left - margin.left) / step)));
          show(focused);
        },
        onpointerleave: hide,
        onfocus: () => show(focused),
        onblur: hide,
        onkeydown: (event) => {
          if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
          event.preventDefault();
          focused = Math.max(0, Math.min(nights.length - 1, focused + (event.key === "ArrowLeft" ? -1 : 1)));
          show(focused);
        },
      }),
    );
    container.replaceChildren(root, tooltip);
  }

  _renderRedDays(days) {
    const red = days.filter((day) => day.color === "red");
    if (!red.length) {
      return this._card(this._t("redDaysCard"), null, h("p", { class: "message" }, this._t("noRedDay")));
    }
    const others = days.filter((day) => day.color !== "red");
    const mean = (list) => list.reduce((sum, day) => sum + day.peak_energy, 0) / list.length;
    const peak = mean(red);
    const other = others.length ? mean(others) : null;
    const kwh = (value) => `${this._number(value, 1)} kWh`;
    return this._card(
      this._t("redDaysCard"),
      null,
      h(
        "div",
        { class: "facts" },
        h("span", {}, this._t("redDaysCount")),
        h("span", { class: "num" }, String(red.length)),
        h("span", {}, this._t("redDaysCost")),
        h("span", { class: "num" }, this._money(red.reduce((sum, day) => sum + day.cost, 0))),
        h("span", {}, this._t("redDaysPeak")),
        h("span", { class: "num" }, kwh(peak)),
        other ? h("p", { class: "hint" }, this._t("redDaysPeakHint", { other: kwh(other), change: this._percent(peak / other - 1) })) : null,
      ),
    );
  }

  _renderTopDays(days) {
    const colors = COLORS[this._language];
    const top = [...days].sort((first, second) => second.cost - first.cost).slice(0, 5);
    return this._card(
      this._t("topDays"),
      null,
      h(
        "div",
        { class: "table-wrap" },
        h(
          "table",
          {},
          h("thead", {}, h("tr", {}, h("th", {}, this._t("day")), h("th", {}, this._t("energy")), h("th", {}, this._t("cost")))),
          h(
            "tbody",
            {},
            top.map((day) =>
              h(
                "tr",
                {},
                h(
                  "td",
                  {},
                  day.color ? h("span", { class: "swatch", title: colors[day.color], style: { background: DAY_FILLS[day.color] } }) : null,
                  this._dayLabel(day.date, { weekday: "short", day: "numeric", month: "short" }),
                ),
                h("td", {}, `${this._number(day.energy, 1)} kWh`),
                h("td", {}, this._money(day.cost)),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // One square per day, a column per week from Monday to Sunday.
  _drawCalendar(container, days) {
    const colors = COLORS[this._language];
    const first = dayTime(days[0].date);
    // Monday of the first week.
    const origin = first - ((new Date(first).getUTCDay() + 6) % 7) * DAY_MS;
    const weeks = Math.floor((dayTime(days[days.length - 1].date) - origin) / (7 * DAY_MS)) + 1;
    const left = 28;
    const top = 16;
    const width = container.clientWidth || 320;
    const cell = Math.max(10, Math.min(18, Math.floor((width - left) / weeks)));
    const most = Math.max(...days.map((day) => day.cost), 0.01);
    const root = s("svg", { class: "calendar", width: left + weeks * cell, height: top + 7 * cell, role: "img", "aria-label": this._t("calendar") });
    [0, 2, 4, 6].forEach((weekday) => {
      const label = new Intl.DateTimeFormat(this._locale, { weekday: "short", timeZone: "UTC" }).format(origin + weekday * DAY_MS);
      root.append(s("text", { x: 0, y: top + weekday * cell + cell / 2, "dominant-baseline": "middle", style: { "font-size": "10px", fill: "var(--ec-muted)" } }, label));
    });
    let month = null;
    // A month label too close to the one before is left out.
    let labelEnd = -Infinity;
    for (const day of days) {
      const offset = Math.round((dayTime(day.date) - origin) / DAY_MS);
      const week = Math.floor(offset / 7);
      if (day.date.slice(0, 7) !== month) {
        month = day.date.slice(0, 7);
        const label = this._dayLabel(day.date, { month: "short" });
        const x = left + week * cell;
        if (x >= labelEnd + 4) {
          root.append(s("text", { x, y: 10, style: { "font-size": "10px", fill: "var(--ec-muted)" } }, label));
          labelEnd = x + label.length * 6;
        }
      }
      const what = [this._dayLabel(day.date, { weekday: "long", day: "numeric", month: "long" }), day.color ? colors[day.color] : null, `${this._number(day.energy, 1)} kWh`, this._money(day.cost)];
      root.append(
        s(
          "rect",
          {
            x: left + week * cell,
            y: top + (offset % 7) * cell,
            width: cell,
            height: cell,
            rx: 3,
            style: { fill: DAY_FILLS[day.color] || "var(--ec-s1)", opacity: String(0.35 + 0.65 * (day.cost / most)) },
          },
          s("title", {}, what.filter(Boolean).join(" · ")),
        ),
      );
    }
    container.replaceChildren(root);
  }

  // The hours of the day that are off-peak for the contract in force.
  _offPeakHours() {
    const inForce = this._contractsInForce();
    const contract = inForce.length === 1 ? this._entry.contracts.find((item) => item.id === inForce[0].id) : null;
    const hours = new Set();
    if (!contract) return hours;
    const ranges = contract.kind === "tempo" ? ["22:00-06:00"] : contract.off_peak;
    for (const range of ranges) {
      const [start, end] = range.split("-").map((time) => Number(time.slice(0, 2)) + Number(time.slice(3, 5)) / 60);
      for (let hour = 0; hour < 24; hour++) {
        if (start < end ? hour >= start && hour < end : hour >= start || hour < end) hours.add(hour);
      }
    }
    return hours;
  }

  _drawProfile(container, profile) {
    const offPeak = this._offPeakHours();
    const values = profile.map((value) => value ?? 0);
    const width = Math.max(container.clientWidth || 320, 240);
    const height = 200;
    const margin = { top: 12, right: 8, bottom: 24, left: 44 };
    const ticks = niceTicks(0, Math.max(...values, 0.01), 3);
    const high = ticks[ticks.length - 1];
    const plotHeight = height - margin.top - margin.bottom;
    const band = (width - margin.left - margin.right) / 24;
    const y = (value) => margin.top + plotHeight - (value / high) * plotHeight;
    const digits = ticks[1] - ticks[0] < 1 ? (ticks[1] - ticks[0] < 0.1 ? 2 : 1) : 0;
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": this._t("profile") });
    for (const tick of ticks) {
      root.append(
        s("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), style: { stroke: tick === 0 ? "var(--ec-axis)" : "var(--ec-grid)", "stroke-width": "1px" } }),
        s("text", { x: margin.left - 6, y: y(tick), "text-anchor": "end", "dominant-baseline": "middle" }, `${this._number(tick, digits)} kWh`),
      );
    }
    const bar = Math.min(24, band - 2);
    values.forEach((value, hour) => {
      const x = margin.left + band * hour + (band - bar) / 2;
      const quiet = offPeak.has(hour);
      if (value > 0) {
        root.append(
          s(
            "path",
            { d: columnPath(x, bar, y(0), y(value)), style: { fill: quiet ? TRANCHE_FILLS.hc[0] : TRANCHE_FILLS.hp[0] } },
            s("title", {}, `${hour} h – ${hour + 1} h · ${this._number(value, 2)} kWh`),
          ),
        );
      }
      if (hour % 3 === 0) {
        root.append(s("text", { x: margin.left + band * (hour + 0.5), y: height - 6, "text-anchor": "middle" }, `${hour} h`));
      }
    });
    const children = [root];
    if (offPeak.size) {
      const total = values.reduce((sum, value) => sum + value, 0);
      const quiet = values.reduce((sum, value, hour) => sum + (offPeak.has(hour) ? value : 0), 0);
      children.unshift(
        h(
          "ul",
          { class: "legend" },
          h("li", {}, h("span", { class: "swatch", style: { background: TRANCHE_FILLS.hc[0] } }), this._t("offPeak")),
          h("li", {}, h("span", { class: "swatch", style: { background: TRANCHE_FILLS.hp[0] } }), this._t("peak")),
        ),
      );
      if (total > 0) {
        children.push(h("p", { class: "note" }, this._t("profileOffPeak", { share: this._percent(quiet / total).replace("+", "") })));
      }
    }
    container.replaceChildren(...children);
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
