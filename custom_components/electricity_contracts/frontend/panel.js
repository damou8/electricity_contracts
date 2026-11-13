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
    tabFollow: "Overview",
    tabUnderstand: "Understand",
    tabCompare: "Compare",
    nowLabel: "Now",
    unknownColor: "Color not published yet",
    perKwh: "{price}/kWh",
    seasonTitle: "Season {season}",
    spentUntil: "spent up to {day}",
    previousSeason: "Last season: {total}, of which {toDate} at the same date.",
    howComputed: "How is it computed?",
    budgetPartial: "The data starts after 1 September: the season so far is partial.",
    budgetMethod: "The forecast assumes you will consume like last year on the same dates, at current prices. The red and white days left are placed on the days you consume the most.",
    budgetNoProjection: "Not enough data a year before to project the rest of the season.",
    spentLegend: "Spent",
    expectedLegend: "Expected",
    temperatureStrip: "Average outdoor temperature",
    temperature: "Temperature",
    weather: "Weather",
    weatherSetup: "Choose an outdoor temperature sensor in the integration's options to compare the consumption with the weather.",
    weatherOpen: "Open the options",
    weatherNoData: "No outdoor temperature recorded over this period.",
    weatherFewDays: "Too few days to tell the heating apart.",
    baseload: "Baseload",
    weekOf: "Week of {day}",
    hourOfDay: "{hour}:00",
    offPeakBand: "off-peak hours",
    offPeakBandShort: "off-peak",
    peakOnBlue: "{share} on blue days",
    peakShort: "Peak",
    offPeakShort: "Off-peak",
    oneDay: "{count} day",
    dayCount: "{count} days",
    perYear: "{amount} a year",
    baseloadNote: "We look at the consumption between 3:00 and 5:00, when almost everything is off, and keep the lowest nights. The yearly cost applies that consumption all year round, at the average price of a kWh, subscription excluded.",
    noHeating: "The consumption doesn't rise with the cold over this period.",
    kwhPerDay: "kWh per day",
    cheaper: "Cheaper",
    dearer: "Dearer",
    calendarKeys: "Calendar: the arrow keys change the day",
    color: "Color",
    spend: "Where the money goes",
    energyShare: "Share of kWh",
    costShare: "Share of euros",
    averagePaid: "Average price paid",
    tabBill: "Phantom bill",
    notPublished: "color not published yet",
    season: "Tempo season {season}",
    daysLeft: "{left} left out of {total}",
    topDays: "Most expensive days",
    day: "Day",
    calendar: "Calendar",
    profile: "Typical day",
    priceRise: "With the same consumption, today's prices cost {amount} more per year than the ones before ({change}).",
    priceDrop: "With the same consumption, today's prices cost {amount} less per year than the ones before ({change}).",
    regulated: "regulated prices",
    manualPrices: "prices entered by hand",
    since: "since {date}",
    offPeakHours: "off-peak {ranges}",
    weekendOffPeak: "weekends off-peak",
    pricesSince: "Prices in force since {date}",
    noPrices: "No price is known for this contract.",
    sincePrevious: "{change} vs previous prices",
    showPrices: "Show the prices",
    hidePrices: "Hide the prices",
    unit: "€/kWh",
    noContractInForce: "Set when your contract started (in the contract's settings) to see what you paid.",
    ofWhichSubscription: "of which {amount} of subscription",
    offPeakShare: "Off-peak hours",
    rolling: "12 months",
    seasonMode: "Season",
    year: "Year",
    month: "Month",
    custom: "Dates",
    previous: "Previous",
    next: "Next",
    from: "From",
    to: "To",
    window: "{start} to {end}",
    windowDays: "{window} · {count} days of data",
    noData: "No data for this period.",
    preparing: "Preparing the figures… The page updates by itself.",
    ifItLasts: "If this lasts, see the state of the integration.",
    noContract: "Add a contract to the integration to compare it here.",
    loadFailed: "Loading failed: {error}",
    liveFailed: "The price now could not be loaded: {error}",
    insightsFailed: "These figures could not be loaded: {error}",
    retry: "Retry",
    actualCost: "Actual cost",
    costPerMonth: "The cost of each month, subscription included",
    costPerDay: "The cost of each day, subscription included",
    energyPerMonth: "The consumption of each month",
    energyPerDay: "The consumption of each day",
    pricePerMonth: "The average price of a kWh each month, subscription included",
    pricePerDay: "The average price of a kWh each day, subscription included",
    measure: "Measure",
    partialActual:
      "No contract was in force on part of the period: those days are left out.",
    chart: "Chart",
    table: "Table",
    period: "Period",
    actual: "Actual cost",
    tranche: "Tranche",
    energy: "Energy",
    cost: "Cost",
    pricesFrom: "Prices from {start} to {end}",
    pricesOf: "prices of {date}",
    quantity: "Quantity",
    amount: "Amount",
    subscription: "Subscription",
    subscriptionYear: "{amount}/year",
    days: "{count} days",
    consumption: "Consumption",
    same: "Same as what you paid",
    ranking: "Ranking",
    yourContract: "your contract",
    notCompared: "Not compared yet",
    waitingPrices: "Priced by hand, without a price period yet: not compared",
    waitingPrice: "Not compared yet: its prices for {day} are missing",
    waitingColor: "Not compared yet: the Tempo color of {day} isn't known",
    addPrices: "Add its prices",
    untilTime: "until {time}",
    tomorrow: "Tomorrow",
    seasonHint: "From {start} to {end}, with the {contract} contract.",
    expectedPerMonth: "expected · {amount} a month",
    spent: "spent",
    seasonSpent: "{spent} spent up to {day} ({energy}).",
    seasonExpected: "{expected} expected by 31 August ({energy}).",
    redLeft: "Red left",
    whiteLeft: "White left",
    withHeating: "Above {base}, you use about {energy} a day. Below, heating uses {slope} for each degree less.",
    weatherInfo: "Each dot is a day with its outdoor temperature and what you consumed.",
    perDegreeBelow: "per degree below {base}",
    ofTheConsumption: "{share} of the consumption",
    aroundTheClock: "around the clock",
    baseloadInfo: "What runs all the time, measured on quiet nights: {energy} a year.",
    weeklyLowKey: "Lowest of each week",
    nightlyLowKey: "Lowest of each night",
    oneDayKey: "A day",
    trend: "Trend",
    profileInfo: "The average consumption of each hour, over the {days} days of the period.",
    offPeakLead: "in off-peak hours",
    aDay: "a day",
    peakAt: "peak at {hour}",
    peaksAt: "peaks at {first} and {second}",
    hourlyKwh: "kWh per hour",
    peakByColor: "Peak hours by color",
    inPeakOnBlue: "in peak hours on blue days",
    inPeakOnWhite: "in peak hours on white days",
    inPeakOnRed: "in peak hours on red days",
    peakSplitLabel: "{color}: {peak} in peak hours, {offPeak} in off-peak hours",
    calendarTempo: "Tempo calendar",
    spendLead: "of the euros go to {tranche}, for {energy} of the kWh",
    perDayEnergy: "{energy} a day",
    averagePrice: "Average price",
    averageSub: "subscription excluded · {price} all in",
    redPeak: "Red peak hours",
    costByMonth: "Cost by month",
    costByDay: "Cost by day",
    energyByMonth: "Consumption by month",
    energyByDay: "Consumption by day",
    priceByMonth: "Average price by month",
    priceByDay: "Average price by day",
    partialMonth: "Incomplete month",
    verdictActual: "What you paid is the lowest",
    isCheapest: "is the cheapest",
    cheapestBy: "is the cheapest · {amount} less than {name}",
    wouldSave: "would have cost {amount} less ({change})",
    rankingInfo: "Each contract is applied to your actual consumption, hour by hour, with its prices and its subscription.",
    rankingChoose: "Choose a contract to see its phantom bill.",
    mineAllIn: "{name}, your contract: {price}/kWh all in.",
    billInfo: "What you would have paid with {name}, on the same consumption.",
    billActual: "Your actual bill: {actual}.",
    billPeriodsInfo: "One line per price period: each keeps the prices in force at its dates.",
    billVsActual: "{amount} against your bill",
    range: "{start} → {end}",
    price: "Price",
    gapWith: "Gap with {name}",
    gapSavedWith: "saved with {mine} since {day}",
    gapSavedSince: "saved since {day}",
    gapLostLead: "more than with {name} since {day}",
    cheaperArrowUp: "↑ {name} cheaper",
    cheaperArrowDown: "↓ {name} cheaper",
    yourContractName: "Your contract",
    gapInfo: "What {mine} saved against {name}, added up since the start of the period.",
    gapNote: "Above zero, {mine} is the cheaper; below, {name} would have been.",
  },
  fr: {
    title: "Contrats",
    tabFollow: "Suivi",
    tabUnderstand: "Comprendre",
    tabCompare: "Comparer",
    nowLabel: "Maintenant",
    unknownColor: "Couleur pas encore publiée",
    perKwh: "{price}/kWh",
    seasonTitle: "Saison {season}",
    spentUntil: "dépensés jusqu'au {day}",
    previousSeason: "Saison dernière : {total}, dont {toDate} à la même date.",
    howComputed: "Comment c'est calculé ?",
    budgetPartial: "Les données commencent après le 1er septembre : le début de saison est incomplet.",
    budgetMethod: "La prévision suppose que vous consommerez comme l'an dernier aux mêmes dates, aux prix actuels. Les jours rouges et blancs restants sont placés sur les jours où vous consommez le plus.",
    budgetNoProjection: "Pas assez de données l'an dernier pour prévoir la fin de la saison.",
    spentLegend: "Dépensé",
    expectedLegend: "Prévu",
    temperatureStrip: "Température extérieure moyenne",
    temperature: "Température",
    weather: "Météo",
    weatherSetup: "Choisissez un capteur de température extérieure dans les options de l'intégration pour comparer la consommation à la météo.",
    weatherOpen: "Ouvrir les options",
    weatherNoData: "Aucune température extérieure enregistrée sur cette période.",
    weatherFewDays: "Trop peu de jours pour isoler le chauffage.",
    baseload: "Talon",
    weekOf: "Semaine du {day}",
    hourOfDay: "{hour} h",
    offPeakBand: "heures creuses",
    offPeakBandShort: "HC",
    peakOnBlue: "{share} les jours bleus",
    peakShort: "HP",
    offPeakShort: "HC",
    oneDay: "{count} jour",
    dayCount: "{count} jours",
    perYear: "{amount} par an",
    baseloadNote: "On regarde la consommation entre 3 h et 5 h, quand presque tout est éteint, et on retient les nuits les plus basses. Le coût annuel applique cette consommation toute l'année, au prix moyen du kWh, hors abonnement.",
    noHeating: "La consommation ne monte pas avec le froid sur cette période.",
    kwhPerDay: "kWh par jour",
    cheaper: "Moins cher",
    dearer: "Plus cher",
    calendarKeys: "Calendrier : les flèches changent de jour",
    color: "Couleur",
    spend: "Où partent les euros",
    energyShare: "Part des kWh",
    costShare: "Part des euros",
    averagePaid: "Prix moyen payé",
    tabBill: "Facture fantôme",
    notPublished: "couleur pas encore publiée",
    season: "Saison Tempo {season}",
    daysLeft: "{left} restants sur {total}",
    topDays: "Jours les plus chers",
    day: "Jour",
    calendar: "Calendrier",
    profile: "Journée type",
    priceRise: "À consommation identique, les prix actuels coûtent {amount} de plus par an que les précédents ({change}).",
    priceDrop: "À consommation identique, les prix actuels coûtent {amount} de moins par an que les précédents ({change}).",
    regulated: "tarif réglementé",
    manualPrices: "prix saisis à la main",
    since: "depuis le {date}",
    offPeakHours: "heures creuses {ranges}",
    weekendOffPeak: "week-end en heures creuses",
    pricesSince: "Prix en vigueur depuis le {date}",
    noPrices: "Aucun prix n'est connu pour ce contrat.",
    sincePrevious: "{change} vs prix précédents",
    showPrices: "Voir les prix",
    hidePrices: "Masquer les prix",
    unit: "€/kWh",
    noContractInForce: "Indiquez le début de votre contrat (dans les réglages du contrat) pour voir ce que vous avez payé.",
    ofWhichSubscription: "dont {amount} d'abonnement",
    offPeakShare: "Heures creuses",
    rolling: "12 mois",
    seasonMode: "Saison",
    year: "Année",
    month: "Mois",
    custom: "Dates",
    previous: "Précédent",
    next: "Suivant",
    from: "Du",
    to: "Au",
    window: "Du {start} au {end}",
    windowDays: "{window} · {count} jours de données",
    noData: "Pas de données sur cette période.",
    preparing: "Préparation des calculs… La page se met à jour toute seule.",
    ifItLasts: "Si cela dure, voyez l'état de l'intégration.",
    noContract: "Ajoutez un contrat à l'intégration pour le comparer ici.",
    loadFailed: "Le chargement a échoué : {error}",
    liveFailed: "Le prix en direct n'a pas pu être chargé : {error}",
    insightsFailed: "Ces chiffres n'ont pas pu être chargés : {error}",
    retry: "Réessayer",
    actualCost: "Coût réel",
    costPerMonth: "Le coût de chaque mois, abonnement compris",
    costPerDay: "Le coût de chaque jour, abonnement compris",
    energyPerMonth: "La consommation de chaque mois",
    energyPerDay: "La consommation de chaque jour",
    pricePerMonth: "Le prix moyen du kWh de chaque mois, abonnement compris",
    pricePerDay: "Le prix moyen du kWh de chaque jour, abonnement compris",
    measure: "Mesure",
    partialActual:
      "Aucun contrat n'était en vigueur sur une partie de la période : ces jours sont laissés de côté.",
    chart: "Graphique",
    table: "Tableau",
    period: "Période",
    actual: "Coût réel",
    tranche: "Tranche",
    energy: "Énergie",
    cost: "Coût",
    pricesFrom: "Prix du {start} au {end}",
    pricesOf: "prix du {date}",
    quantity: "Quantité",
    amount: "Montant",
    subscription: "Abonnement",
    subscriptionYear: "{amount}/an",
    days: "{count} jours",
    consumption: "Consommation",
    same: "Identique à ce que vous avez payé",
    ranking: "Classement",
    yourContract: "votre contrat",
    notCompared: "Pas encore comparé",
    waitingPrices: "Prix saisis à la main, sans période de prix pour l'instant : pas encore comparé",
    waitingPrice: "Pas encore comparé : il manque ses prix du {day}",
    waitingColor: "Pas encore comparé : la couleur Tempo du {day} n'est pas encore connue",
    addPrices: "Ajouter ses prix",
    untilTime: "jusqu'à {time}",
    tomorrow: "Demain",
    seasonHint: "Du {start} au {end}, avec le contrat {contract}.",
    expectedPerMonth: "prévus · {amount} par mois",
    spent: "dépensés",
    seasonSpent: "{spent} dépensés jusqu'au {day} ({energy}).",
    seasonExpected: "{expected} prévus d'ici au 31 août ({energy}).",
    redLeft: "Rouges restants",
    whiteLeft: "Blancs restants",
    withHeating: "Au-dessus de {base}, vous consommez environ {energy} par jour. En dessous, le chauffage consomme {slope} par degré de moins.",
    weatherInfo: "Chaque point est une journée avec sa température extérieure et ce que vous avez consommé.",
    perDegreeBelow: "par degré sous {base}",
    ofTheConsumption: "{share} de la consommation",
    aroundTheClock: "en continu",
    baseloadInfo: "Ce qui tourne en permanence, mesuré les nuits calmes : {energy} par an.",
    weeklyLowKey: "Minimum de chaque semaine",
    nightlyLowKey: "Minimum de chaque nuit",
    oneDayKey: "Un jour",
    trend: "Tendance",
    profileInfo: "La consommation moyenne de chaque heure, sur les {days} jours de la période.",
    offPeakLead: "en heures creuses",
    aDay: "par jour",
    peakAt: "pointe à {hour}",
    peaksAt: "pointes à {first} et {second}",
    hourlyKwh: "kWh par heure",
    peakByColor: "Heures pleines par couleur",
    inPeakOnBlue: "en HP les jours bleus",
    inPeakOnWhite: "en HP les jours blancs",
    inPeakOnRed: "en HP les jours rouges",
    peakSplitLabel: "{color} : {peak} en heures pleines, {offPeak} en heures creuses",
    calendarTempo: "Calendrier Tempo",
    spendLead: "des euros en {tranche}, pour {energy} des kWh",
    perDayEnergy: "{energy} par jour",
    averagePrice: "Prix moyen",
    averageSub: "hors abonnement · {price} tout compris",
    redPeak: "HP rouges",
    costByMonth: "Coût par mois",
    costByDay: "Coût par jour",
    energyByMonth: "Consommation par mois",
    energyByDay: "Consommation par jour",
    priceByMonth: "Prix moyen par mois",
    priceByDay: "Prix moyen par jour",
    partialMonth: "Mois incomplet",
    verdictActual: "Ce que vous avez payé est le plus bas",
    isCheapest: "est le moins cher",
    cheapestBy: "est le moins cher · {amount} de moins que {name}",
    wouldSave: "aurait coûté {amount} de moins ({change})",
    rankingInfo: "Chaque contrat est appliqué à votre consommation réelle, heure par heure, avec ses prix et son abonnement.",
    rankingChoose: "Choisissez un contrat pour voir sa facture fantôme.",
    mineAllIn: "{name}, votre contrat : {price}/kWh abonnement compris.",
    billInfo: "Ce que vous auriez payé avec {name}, sur la même consommation.",
    billActual: "Votre facture réelle : {actual}.",
    billPeriodsInfo: "Une ligne par période de prix : chacune garde les tarifs en vigueur à ses dates.",
    billVsActual: "{amount} par rapport à votre facture",
    range: "{start} → {end}",
    price: "Prix",
    gapWith: "Écart avec {name}",
    gapSavedWith: "gagnés avec {mine} depuis le {day}",
    gapSavedSince: "gagnés depuis le {day}",
    gapLostLead: "de plus qu'avec {name} depuis le {day}",
    cheaperArrowUp: "↑ {name} moins cher",
    cheaperArrowDown: "↓ {name} moins cher",
    yourContractName: "Votre contrat",
    gapInfo: "Ce que {mine} vous a fait gagner face à {name}, cumulé depuis le début de la période.",
    gapNote: "Au-dessus de zéro, {mine} est le moins cher ; en dessous, {name} l'aurait été.",
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

// Tempo tranches keep their day's color; the other contracts take the money
// violet, blue being kept for Tempo. Off-peak is the lighter step. Text inside
// a block takes the ink its fill needs.
const TRANCHE_FILLS = {
  base: ["#8a7fe8", "#0b0b0b"],
  hc: ["#b1a9f1", "#0b0b0b"],
  hp: ["#5b4fc9", "#ffffff"],
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
  --ec-warn: #a35f00;
  --ec-money: var(--ec-s7);
  --ec-money-soft: rgba(98, 80, 214, 0.35);
  --ec-money-2: #b9b1f0;
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
  --ec-warn: #e0a030;
  --ec-money-soft: rgba(144, 133, 233, 0.4);
  --ec-money-2: #4b4578;
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
.contract-chips { display: inline-flex; gap: 8px; }
.contract-chip {
  font: inherit;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 8px 0 14px;
  border: 1px solid currentColor;
  border-radius: 18px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  white-space: nowrap;
}
.contract-chip strong { font-weight: 500; }
.contract-chip .kva { opacity: 0.75; }
.contract-chip svg { width: 20px; height: 20px; fill: currentColor; transition: transform 0.15s; }
.contract-chip[aria-expanded="true"] svg { transform: rotate(180deg); }
.facts { margin: -4px 0 8px; }
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
/* A tint rather than a solid fill: text on the primary color is too faint. */
.segmented button[aria-pressed="true"] {
  background: color-mix(in srgb, var(--primary-color) 26%, transparent);
  box-shadow: inset 0 0 0 1px var(--primary-color);
  color: var(--ec-text);
  font-weight: 500;
}
.segmented.small { padding: 3px; border-radius: 18px; flex-wrap: nowrap; }
.segmented.small button { font-size: 13px; padding: 4px 12px; min-height: 30px; }
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
.window { color: var(--ec-text-2); font-size: 14px; }
.filters:empty { display: none; }
@media (min-width: 601px) {
  /* The period stays in reach while the page scrolls. */
  .filters {
    position: sticky;
    top: var(--header-height, 56px);
    z-index: 1;
    margin: -8px 0;
    padding: 8px 0;
    background: var(--primary-background-color);
    border-bottom: 1px solid var(--divider-color, var(--ec-grid));
  }
}
.head { display: flex; flex-direction: column; gap: 16px; }
.head:empty { display: none; }
.content { display: flex; flex-direction: column; gap: 16px; transition: opacity 0.2s; }
.content.loading { opacity: 0.5; pointer-events: none; }
.card {
  background: var(--ec-surface);
  border-radius: var(--ha-card-border-radius, 12px);
  border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  box-shadow: var(--ha-card-box-shadow, none);
  padding: 16px;
}
.card-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 12px; min-height: 32px; margin-bottom: 8px; }
.card-head > div:first-child { flex: 1 1 200px; min-width: 0; }
/* The title names the card; its figure leads. */
.card h2 { margin: 0; font-size: 14px; font-weight: 400; color: var(--ec-text-2); }
.card h2::first-letter { text-transform: uppercase; }
.card-tools { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 8px; }
.info {
  font: inherit;
  width: 40px;
  height: 40px;
  margin: -8px -8px -8px 0;
  flex: none;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--ec-text-2);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.info:hover { background: var(--ec-wash); }
.info[aria-expanded="true"] { color: var(--ec-text); }
.info svg { width: 20px; height: 20px; fill: currentColor; }
.method { margin: 12px 0 0; padding: 10px 12px; border-radius: 8px; background: var(--ec-wash); color: var(--ec-text-2); font-size: 13px; line-height: 1.5; }
.method p { margin: 0; }
.method p + p { margin-top: 8px; }
.lead { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 10px; margin-bottom: 12px; }
.lead strong { font-size: 28px; font-weight: 500; line-height: 1.2; font-variant-numeric: tabular-nums; }
.lead span { color: var(--ec-text-2); font-size: 14px; }
.keys { display: flex; flex-wrap: wrap; gap: 4px 16px; margin: 10px 0 0; padding: 0; list-style: none; font-size: 13px; color: var(--ec-text-2); }
.keys li { display: inline-flex; align-items: center; gap: 6px; }
.dash-key { width: 14px; height: 0; border-top: 2px dashed var(--ec-text); flex: none; }
.dot-key { width: 8px; height: 8px; border-radius: 50%; background: var(--ec-money); flex: none; }
.error { display: flex; gap: 12px; align-items: flex-start; }
.error svg { width: 22px; height: 22px; flex: none; fill: var(--ec-warn); }
.error p { margin: 0 0 10px; }
.skeleton .bone { display: block; border-radius: 6px; background: var(--ec-wash); animation: ec-pulse 1.6s ease-in-out infinite; }
@keyframes ec-pulse { 50% { opacity: 0.45; } }
@media (prefers-reduced-motion: reduce) { .skeleton .bone { animation: none; } }
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
.message a { color: var(--primary-color); }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); padding: 0; overflow: hidden; }
.kpi { padding: 14px 16px; box-shadow: -1px 0 0 var(--divider-color, var(--ec-grid)), 0 -1px 0 var(--divider-color, var(--ec-grid)); }
.kpi .label { color: var(--ec-text-2); font-size: 13px; }
.kpi .value { font-size: 26px; font-weight: 500; margin: 2px 0; line-height: 1.2; overflow-wrap: anywhere; font-variant-numeric: tabular-nums; }
.kpi .value .unit { font-size: 15px; font-weight: 400; color: var(--ec-text-2); }
.kpi .sub { color: var(--ec-text-2); font-size: 13px; }
.tomorrow { margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--divider-color, var(--ec-grid)); display: flex; flex-direction: column; gap: 8px; font-size: 14px; }
.tomorrow .line { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; }
.tomorrow .line strong { font-weight: 500; }
.price-now { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; margin-bottom: 4px; }
.price-now strong { font-size: 28px; font-weight: 500; line-height: 1.2; font-variant-numeric: tabular-nums; }
.price-now .tranche { align-self: center; padding: 2px 10px; border-radius: 12px; font-size: 13px; font-weight: 500; }
.pills { display: flex; flex-wrap: wrap; gap: 8px; }
.pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 14px; border: 1px solid var(--divider-color, var(--ec-grid)); font-size: 13px; font-variant-numeric: tabular-nums; }
.meters.compact { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--divider-color, var(--ec-grid)); }
.meters.compact .meter { margin-top: 0; }
.meters.compact .track { height: 6px; border-radius: 3px; }
.price-tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; margin-top: 8px; }
.price-tile { border: 1px solid var(--divider-color, var(--ec-grid)); border-radius: 10px; padding: 10px 12px; min-width: 0; }
.price-tile .name { display: flex; align-items: center; gap: 6px; color: var(--ec-text-2); font-size: 13px; }
.price-tile .price { font-size: 18px; font-weight: 600; margin: 2px 0; }
.price-tile .delta { color: var(--ec-text-2); font-size: 12px; }
.price-tile svg { display: block; margin-top: 8px; overflow: visible; }
.price-tile rect { fill: transparent; cursor: pointer; }
.pair { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.duo { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr)); gap: 16px; }
.colors { display: flex; flex-direction: column; gap: 14px; }
.color-row { display: grid; grid-template-columns: 8em minmax(0, 1fr); align-items: center; gap: 12px; font-size: 14px; }
.meter { margin-top: 10px; }
.meter .row { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; color: var(--ec-text-2); margin-bottom: 4px; }
.meter .row strong { color: var(--ec-text); font-weight: 500; }
.meter .track { height: 8px; border-radius: 4px; background: var(--ec-wash); overflow: hidden; }
.meter .fill { height: 100%; border-radius: 4px; }
.sub { color: var(--ec-text-2); font-size: 13px; }
.ribbon { display: flex; gap: 2px; height: 28px; margin-top: 12px; }
.ribbon .unknown {
  background: repeating-linear-gradient(135deg, var(--ec-grid) 0 4px, transparent 4px 8px);
  box-shadow: inset 0 0 0 1px var(--ec-grid);
  color: var(--ec-text-2);
}
.ribbon-ticks { position: relative; height: 18px; font-size: 12px; color: var(--ec-muted); }
.ribbon-ticks span { position: absolute; top: 4px; white-space: nowrap; }
.budget { position: relative; padding-top: 4px; margin: 4px 0 8px; }
.budget-bar { position: relative; display: flex; gap: 2px; height: 16px; border-radius: 4px; background: var(--ec-wash); }
.budget-bar .spent { background: var(--ec-money); border-radius: 4px 0 0 4px; }
.budget-bar .rest { background: repeating-linear-gradient(135deg, var(--ec-money-soft) 0 3px, transparent 3px 7px); box-shadow: inset 0 0 0 1px var(--ec-money-soft); border-radius: 0 4px 4px 0; }
.budget-bar .alone { border-radius: 4px; }
.budget .marker { position: absolute; top: 0; height: 24px; width: 2px; margin-left: -1px; background: var(--ec-text); border-radius: 1px; }
.spent-line { font-size: 14px; }
.spent-line strong { font-weight: 500; font-variant-numeric: tabular-nums; }
.swatch.hatched { background: repeating-linear-gradient(135deg, var(--ec-money) 0 2px, transparent 2px 4px); box-shadow: inset 0 0 0 1px var(--ec-money); }
.meters { margin-top: 12px; }
a.toggle { display: inline-block; margin-top: 8px; text-decoration: none; }
.scroll { overflow-x: auto; }
.calendar { display: block; outline: none; }
.calendar:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; border-radius: 4px; }
.calendar text { font-size: 10px; fill: var(--ec-muted); }
.calendar .cell { cursor: pointer; }
.calendar .empty { fill: none; stroke: var(--ec-axis); stroke-width: 1px; }
.swatch.empty { box-shadow: inset 0 0 0 1px var(--ec-axis); }
.legend .scale { display: inline-flex; gap: 2px; }
.day-detail { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; margin-top: 10px; padding: 10px 12px; border-radius: 8px; background: var(--ec-wash); font-size: 14px; font-variant-numeric: tabular-nums; }
.day-detail strong { display: inline-flex; align-items: center; gap: 6px; font-weight: 500; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 16px; margin: 0 0 8px; padding: 0; list-style: none; font-size: 13px; color: var(--ec-text-2); }
.legend li { display: inline-flex; align-items: center; gap: 6px; }
.swatch { width: 10px; height: 10px; border-radius: 2px; flex: none; }
.line-key { width: 14px; height: 2px; border-radius: 1px; flex: none; }
.chart { position: relative; width: 100%; }
.chart svg { display: block; overflow: visible; }
.chart text { font-size: 12px; fill: var(--ec-muted); font-variant-numeric: tabular-nums; }
.chart .hit { fill: transparent; cursor: crosshair; outline: none; }
.chart text.ink { fill: var(--ec-text); }
.chart text.halo { paint-order: stroke; stroke: var(--ec-surface); stroke-width: 3px; stroke-linejoin: round; }
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
th:first-child, td:first-child, th.left, td.left { text-align: left; }
.wrap-head th { white-space: normal; }
th { color: var(--ec-text-2); font-weight: 500; }
td .swatch { display: inline-block; vertical-align: -1px; margin-right: 6px; }
tfoot td { font-weight: 600; border-bottom: none; }
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
.ranking { display: flex; flex-direction: column; gap: 4px; }
.rank {
  font: inherit;
  display: grid;
  grid-template-columns: 24px minmax(120px, 220px) minmax(0, 1fr) minmax(110px, auto);
  gap: 12px;
  align-items: center;
  width: 100%;
  min-height: 56px;
  padding: 8px 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--ec-text);
  text-align: left;
  cursor: pointer;
}
.rank:hover { background: var(--ec-wash); }
.rank[aria-pressed="true"] { border-color: var(--ec-money); background: color-mix(in srgb, var(--ec-money) 12%, transparent); }
.rank .position { color: var(--ec-text-2); font-size: 14px; }
.rank .who { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.rank .name { font-size: 15px; font-weight: 500; }
.rank .fact { white-space: nowrap; }
.rank .bars { display: flex; height: 14px; }
.rank .bar { background: var(--ec-money-2); border-radius: 0 4px 4px 0; }
.rank .bar.mine { background: var(--ec-money); }
.rank .total { display: flex; flex-direction: column; align-items: flex-end; font-variant-numeric: tabular-nums; }
.rank .total strong { font-size: 18px; font-weight: 500; }
.rank.pending { cursor: default; }
.rank.pending:hover { background: transparent; }
.rank.pending .who { grid-column: 2 / 4; }
.rank .cta {
  justify-self: end;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid var(--primary-color);
  border-radius: 18px;
  color: var(--primary-color);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
}
.rank .cta svg { width: 16px; height: 16px; fill: currentColor; }
.chart .side { position: absolute; font-size: 12px; color: var(--ec-text-2); pointer-events: none; }
.bill-periods { border: 1px solid var(--divider-color, var(--ec-grid)); border-radius: 10px; overflow: hidden; }
.bill-period {
  font: inherit;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 48px;
  padding: 8px 14px;
  border: none;
  background: var(--ec-wash);
  color: var(--ec-text);
  text-align: left;
  cursor: pointer;
}
.bill-period + .table-wrap, .table-wrap + .bill-period, .bill-period + .bill-period { border-top: 1px solid var(--divider-color, var(--ec-grid)); }
.bill-period svg { width: 20px; height: 20px; fill: currentColor; flex: none; transition: transform 0.15s; }
.bill-period[aria-expanded="true"] svg { transform: rotate(90deg); }
.bill-period .what { flex: 1; display: flex; flex-direction: column; gap: 2px; font-weight: 500; }
.bill-period .what .sub { font-weight: 400; }
.bill-period .num { font-weight: 500; font-variant-numeric: tabular-nums; }
.bill-periods .table-wrap td:first-child, .bill-periods .table-wrap th:first-child { padding-left: 14px; white-space: normal; }
.bill-periods .table-wrap td:last-child, .bill-periods .table-wrap th:last-child { padding-right: 14px; }
.bill-sum { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px 24px; margin-top: 12px; color: var(--ec-text-2); font-size: 14px; font-variant-numeric: tabular-nums; }
.bill-sum strong { color: var(--ec-text); font-weight: 500; }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--divider-color, var(--ec-grid)); }
.tabs button {
  font: inherit;
  font-size: 15px;
  font-weight: 500;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  padding: 0 20px;
  min-height: 48px;
  background: transparent;
  color: var(--ec-text-2);
  cursor: pointer;
}
.tabs button:hover { background: var(--ec-wash); }
.tabs button[aria-selected="true"] { color: var(--ec-text); border-bottom-color: var(--primary-color); }
@media (max-width: 600px) {
  main { padding: 12px; gap: 12px; }
  .duo { gap: 12px; }
  .card { padding: 14px; }
  .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); padding: 0; }
  .kpi .value { font-size: 22px; }
  .nav .label { min-width: 7em; }
  .tabs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0; }
  .tabs button { padding: 0 4px; }
  /* The periods scroll sideways rather than wrapping on a phone. */
  .filters > .segmented { flex-wrap: nowrap; overflow-x: auto; max-width: 100%; }
  .filters > .segmented button { flex: none; }
  .filters { gap: 4px 12px; }
  .meters.compact { gap: 12px; }
  .rank { grid-template-columns: 20px minmax(0, 1fr) auto; gap: 4px 10px; }
  .rank .bars { grid-column: 2 / -1; grid-row: 2; }
  .rank.pending .who, .rank.pending .cta { grid-column: 2 / -1; }
  .rank.pending .cta { justify-self: start; }
  th, td { padding: 6px 4px; }
}
`;

const ICONS = {
  left: "M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z",
  right: "M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z",
  down: "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",
  info: "M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z",
  alert: "M12,2L1,21H23M12,6L19.53,19H4.47M11,10V14H13V10M11,16V18H13V16",
  plus: "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",
};

const MEASURES = { cost: "€", energy: "kWh", price: "€/kWh" };
const TABS = ["follow", "understand", "compare"];
const TAB_KEYS = { follow: "tabFollow", understand: "tabUnderstand", compare: "tabCompare" };
// Past this many nights, the baseload chart shows the lowest of each week.
const WEEKLY_NIGHTS = 62;
// While its source is set up, the page asks again this often.
const PREPARING_RETRY_MS = 5000;
const IN_PEAK_ON = { blue: "inPeakOnBlue", white: "inPeakOnWhite", red: "inPeakOnRed" };

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

// Off-peak ranges, in hours of the day, cut at midnight.
function dayPieces(ranges) {
  return ranges.flatMap(([start, end]) => (start < end ? [[start, end]] : [[start, 24], [0, end]]));
}

// The part of the hour starting at `hour` that is off-peak.
function offPeakPart(ranges, hour) {
  return dayPieces(ranges).reduce((sum, [start, end]) => sum + Math.max(0, Math.min(end, hour + 1) - Math.max(start, hour)), 0);
}

// A step of the violet scale, from the card's color (0) to the full violet.
function costFill(step) {
  return `color-mix(in srgb, var(--ec-money) ${Math.round(step)}%, var(--ec-surface))`;
}

function capitalize(text, locale) {
  return text.charAt(0).toLocaleUpperCase(locale) + text.slice(1);
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
    this._views = { time: "chart", cumulative: "chart", tranches: "chart" };
    this._tab = "follow";
    // What the time chart shows: cost, energy or price.
    this._measure = "cost";
    // The method notes opened, by name.
    this._open = {};
    this._season = null;
    this._insightsError = null;
    this._outlookError = null;
    this._outlookLoaded = false;
    this._billContract = null;
    this._bill = null;
    this._billError = null;
    this._billBusy = false;
    this._billCount = 0;
    this._billKey = null;
    // The bill's price periods opened or closed by hand, by position.
    this._billOpen = {};
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
    clearTimeout(this._entriesTimer);
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

  // A tariff has 4 decimals, an average price 3.
  _price(value) {
    return this._money(value, 4);
  }

  _average(value) {
    return this._money(value, 3);
  }

  // Whole kWh, with a decimal under 100.
  _kwh(value) {
    const digits = Math.abs(value) < 100 ? 1 : 0;
    return `${new Intl.NumberFormat(this._locale, { maximumFractionDigits: digits }).format(value)} kWh`;
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
    if (contractId === ACTUAL) return "var(--ec-money)";
    return index >= 0 && index < SERIES_SLOTS ? `var(--ec-s${index + 1})` : "var(--ec-other)";
  }

  async _loadEntries() {
    clearTimeout(this._entriesTimer);
    try {
      this._entries = await this._hass.callWS({ type: `${DOMAIN}/entries` });
      this._error = null;
    } catch (error) {
      this._entries = [];
      this._error = error.message || String(error);
    }
    if (!this._entries.some((entry) => entry.entry_id === this._entryId)) {
      this._entryId = this._entries.length ? this._entries[0].entry_id : null;
      this._resetPeriod();
    }
    if (!this._entries.length && !this._error) {
      // The page stays while its source is set up again, after a restart or a
      // change of contract: it shows up once ready. Back on the page asks too.
      this._entriesTimer = setTimeout(() => this.isConnected && this._loadEntries(), PREPARING_RETRY_MS);
    }
    this._renderSources();
    this._refreshOutlook();
    await this._load();
  }

  _resetPeriod() {
    this._year = null;
    this._month = null;
    this._season = null;
    this._custom = null;
  }

  _refreshOutlook() {
    this._outlook = null;
    this._outlookLoaded = false;
    this._outlookError = null;
    this._renderHead();
    this._loadOutlook().then(() => this._renderHead());
  }

  _window() {
    const entry = this._entry;
    const last = entry.last_day;
    const [year, month, day] = last.split("-").map(Number);
    if (this._year === null) {
      this._year = year;
      this._month = month;
    }
    if (this._season === null) {
      // Seasons run from 1 September to 31 August.
      this._season = month >= 9 ? year : year - 1;
    }
    switch (this._mode) {
      case "year":
        return { start: `${this._year}-01-01`, end: `${this._year}-12-31` };
      case "season":
        return { start: `${this._season}-09-01`, end: `${this._season + 1}-08-31` };
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
    // Another period asks for the bill again.
    this._bill = null;
    this._billError = null;
    this._billBusy = false;
    this._billKey = null;
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
    if (this._data) {
      this._content.classList.add("loading");
    } else {
      // The first time, cards the size of the ones to come.
      this._error = null;
      this._content.replaceChildren(...this._skeleton());
    }
    let insightsError = null;
    try {
      const request = { entry_id: entry.entry_id, start: window.start, end: window.end };
      const [data, insights] = await Promise.all([
        this._hass.callWS({ type: `${DOMAIN}/compare`, ...request }),
        // The page stands without them: their cards tell what went wrong.
        this._hass.callWS({ type: `${DOMAIN}/insights`, ...request }).catch((error) => {
          insightsError = error.message || String(error);
          return null;
        }),
      ]);
      if (count !== this._loadCount) return;
      this._request = window;
      this._data = data;
      this._insights = insights;
      this._insightsError = insightsError;
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

  // Grey cards standing for the KPIs and a chart while the data loads.
  _skeleton() {
    const bone = (width, height) => h("span", { class: "bone", style: { width, height: `${height}px` } });
    const tile = () => h("div", { class: "kpi" }, bone("50%", 12), h("div", { style: { height: "12px" } }), bone("70%", 26));
    return [
      h("section", { class: "card kpis skeleton", "aria-busy": "true" }, tile(), tile(), tile(), tile()),
      h("section", { class: "card skeleton" }, bone("30%", 14), h("div", { style: { height: "16px" } }), bone("100%", 220)),
    ];
  }

  // A card that says what failed, with a way to try again.
  _errorCard(title, message, retry) {
    return this._card(
      title,
      h(
        "div",
        { class: "error", role: "alert" },
        icon(ICONS.alert),
        h("div", {}, h("p", {}, message), retry ? h("button", { class: "toggle", onclick: retry }, this._t("retry")) : null),
      ),
    );
  }

  // A card's figure first, with one line of context.
  _lead(value, context) {
    return h("div", { class: "lead" }, h("strong", {}, value), context ? h("span", {}, context) : null);
  }

  // What the marks of a chart stand for, under it.
  _keys(...items) {
    return h("ul", { class: "keys" }, items.filter(Boolean).map(([mark, label]) => h("li", {}, mark, label)));
  }

  // Layout --------------------------------------------------------------------

  _build() {
    const root = this.shadowRoot;
    root.append(h("style", {}, STYLE));
    this._menu = document.createElement("ha-menu-button");
    this._menu.hass = this._hass;
    this._menu.narrow = this._narrow;
    this._sources = h("span");
    this._chips = h("span", { class: "contract-chips" });
    root.append(h("div", { class: "toolbar" }, this._menu, h("h1", {}, this._t("title")), this._chips, this._sources));
    this._tabs = h("div", { class: "tabs", role: "tablist", "aria-label": this._t("title") });
    // What happens today: only on the first tab, and not tied to the period.
    this._head = h("div", { class: "head" });
    this._filters = h("div", { class: "filters" });
    this._content = h("div", { class: "content", role: "tabpanel" });
    root.append(h("main", {}, this._tabs, this._head, this._filters, this._content));
    this._renderTabs();
    if (this._observer) {
      this._observer.observe(this._content);
    }
  }

  _renderTabs() {
    const select = (tab, focus) => {
      if (this._tab !== tab) {
        this._tab = tab;
        this._renderTabs();
        this._renderContent();
      }
      if (focus) this._tabs.querySelector('[aria-selected="true"]').focus();
    };
    this._tabs.replaceChildren(
      ...TABS.map((tab, index) =>
        h(
          "button",
          {
            role: "tab",
            "aria-selected": String(this._tab === tab),
            tabindex: this._tab === tab ? 0 : -1,
            onclick: () => select(tab, false),
            onkeydown: (event) => {
              const step = { ArrowLeft: -1, ArrowRight: 1 }[event.key];
              if (!step) return;
              event.preventDefault();
              select(TABS[(index + step + TABS.length) % TABS.length], true);
            },
          },
          this._t(TAB_KEYS[tab]),
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
          this._resetPeriod();
          this._data = null;
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
    const modes = ["month", "season", "year", "rolling", "custom"].map((mode) =>
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
        this._t(mode === "season" ? "seasonMode" : mode),
      ),
    );
    const children = [h("div", { class: "segmented", role: "group", "aria-label": this._t("period") }, modes)];
    const first = entry.first_day || entry.last_day;
    if (this._mode === "season" && this._season !== null) {
      children.push(
        this._nav(
          `${this._season}-${this._season + 1}`,
          first < `${this._season}-09-01`,
          entry.last_day > `${this._season + 1}-08-31`,
          (step) => {
            this._season += step;
            this._load();
          },
        ),
      );
    } else if (this._mode === "year" && this._year !== null) {
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
      children.push(h("div", { class: "window" }, this._t("windowDays", { window: this._windowText(), count: this._days() })));
    }
    this._filters.replaceChildren(...children);
  }

  // The days of data in the period, once narrowed to the data.
  _days(data = this._data) {
    return Math.round((Date.parse(data.end) - Date.parse(data.start)) / DAY_MS);
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

  // A card: its title, the (i) opening what its figures mean, its tools, then
  // its body. The notes open under the body.
  _card(title, body, { info = [], tools = null, rerender = () => this._renderContent() } = {}) {
    const notes = info.filter(Boolean);
    const open = notes.length > 0 && Boolean(this._open[title]);
    const button = notes.length
      ? h(
          "button",
          {
            class: "info",
            title: this._t("howComputed"),
            "aria-label": this._t("howComputed"),
            "aria-expanded": String(open),
            onclick: () => {
              this._open[title] = !open;
              rerender();
            },
          },
          icon(ICONS.info),
        )
      : null;
    return h(
      "section",
      { class: "card" },
      h("div", { class: "card-head" }, h("h2", {}, title), tools || button ? h("div", { class: "card-tools" }, tools, button) : null),
      body,
      open ? h("div", { class: "method" }, notes.map((note) => h("p", {}, note))) : null,
    );
  }

  _renderContent() {
    this._renderHead();
    const entry = this._entry;
    if (this._error) {
      // Listing the sources again finds one that was reloaded meanwhile.
      this._content.replaceChildren(this._errorCard(this._t("title"), this._t("loadFailed", { error: this._error }), () => this._loadEntries()));
      return;
    }
    let message = null;
    if (!entry) {
      message = this._entries
        ? [this._t("preparing"), " ", h("a", { href: `/config/integrations/integration/${DOMAIN}` }, this._t("ifItLasts"))]
        : null;
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
    let cards;
    if (this._tab === "compare") {
      cards = this._renderCompare();
    } else if (this._tab === "understand") {
      cards = this._renderUnderstand();
    } else {
      cards = this._renderFollow();
    }
    this._content.replaceChildren(...cards.filter(Boolean));
    this._width = this._content.clientWidth;
    this._renderCharts();
  }

  // Above the period: the prices of the contract in force when its chip is
  // open, then on the first tab its price now and the season.
  _renderHead() {
    const entry = this._entry;
    this._renderContractChips();
    if (!entry || !entry.contracts.length) {
      this._head.replaceChildren();
      return;
    }
    const cards = this._tab === "follow" ? [this._renderNow(), this._renderSeason()].filter(Boolean) : [];
    this._head.replaceChildren(...this._renderContractPrices(), ...(cards.length ? [h("div", { class: "pair" }, cards)] : []));
  }

  _renderFollow() {
    if (!this._data.actual) {
      return [h("section", { class: "card message" }, this._t("noContractInForce"))];
    }
    return [this._renderKpis(), this._renderEvolution()];
  }

  _renderUnderstand() {
    const insights = this._insights;
    if (this._insightsError) {
      return [this._errorCard(this._t("tabUnderstand"), this._t("insightsFailed", { error: this._insightsError }), () => this._load())];
    }
    if (!insights || !insights.days.length) {
      return [h("section", { class: "card message" }, this._t(this._data.actual ? "noData" : "noContractInForce"))];
    }
    // Cards go in pairs; one alone takes the whole row.
    const duo = (...cards) => {
      const present = cards.filter(Boolean);
      return present.length ? h("div", { class: "duo" }, present) : null;
    };
    return [
      duo(this._renderProfile(), this._renderPeakByColor()),
      duo(this._renderBaseload(), this._renderWeather()),
      duo(this._renderCalendar(), this._renderTopDays()),
      this._renderSpend(),
    ];
  }

  _renderEvolution() {
    this._timeChart = h("div", { class: "chart" });
    const by = this._data.group_by === "month" ? "Month" : "Day";
    const measures = h(
      "div",
      { class: "segmented small", role: "group", "aria-label": this._t("measure") },
      Object.entries(MEASURES).map(([measure, label]) =>
        h(
          "button",
          {
            "aria-pressed": String(this._measure === measure),
            onclick: () => {
              if (this._measure === measure) return;
              this._measure = measure;
              this._renderContent();
            },
          },
          label,
        ),
      ),
    );
    return this._card(this._t(`${this._measure}By${by}`), this._timeChart, {
      info: [this._t(`${this._measure}Per${by}`)],
      tools: [measures, this._toggle("time")],
    });
  }

  // What the time chart shows of each bucket, and how to write it.
  _measureOf() {
    switch (this._measure) {
      case "energy":
        return { value: (bucket) => bucket.energy, format: (value) => this._kwh(value), axis: (value, digits) => `${this._number(value, digits)} kWh` };
      case "price":
        return {
          value: (bucket) => (bucket.actual !== null && bucket.energy > 0 ? bucket.actual / bucket.energy : null),
          format: (value) => this._average(value),
          axis: (value, digits) => this._money(value, Math.max(digits, 2)),
        };
      default:
        return { value: (bucket) => bucket.actual, format: (value) => this._money(value), axis: (value, digits) => this._money(value, digits) };
    }
  }

  // The months the data covers only in part, at both ends of the period.
  _partialBuckets() {
    const partial = new Set();
    const series = this._data.series;
    if (this._data.group_by !== "month" || !series.length) return partial;
    if (this._data.start.slice(8, 10) !== "01") partial.add(0);
    const [year, month, day] = lastDayOf(this._data.end).split("-").map(Number);
    if (day !== monthEnd(year, month)) partial.add(series.length - 1);
    return partial;
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

  // The period's figures in one band: each with one line of context.
  _renderKpis() {
    const actual = this._data.actual;
    const tile = (label, value, sub) => h("div", { class: "kpi" }, h("div", { class: "label" }, label), h("div", { class: "value" }, value), sub ? h("div", { class: "sub" }, sub) : null);
    const days = this._days();
    return h(
      "section",
      { class: "card kpis" },
      tile(this._t("actualCost"), this._money(actual.total_cost, 0), this._t("ofWhichSubscription", { amount: this._money(actual.fixed_cost, 0) })),
      tile(this._t("consumption"), this._kwh(actual.energy), days > 0 ? this._t("perDayEnergy", { energy: this._kwh(actual.energy / days) }) : null),
      actual.energy
        ? tile(
            this._t("averagePrice"),
            [this._average(actual.variable_cost / actual.energy), h("span", { class: "unit" }, "/kWh")],
            this._t("averageSub", { price: this._average(actual.total_cost / actual.energy) }),
          )
        : null,
      this._renderUsage(tile),
    );
  }

  // How the contract in force is used: the red peak hours of Tempo, the
  // off-peak hours of HP/HC.
  _renderUsage(tile) {
    const inForce = this._contractsInForce();
    if (inForce.length !== 1) return null;
    const { kind, tranches } = inForce[0];
    const energy = Object.values(tranches).reduce((sum, item) => sum + item.energy, 0);
    if (!(energy > 0)) return null;
    const used = (...keys) => keys.reduce((sum, key) => sum + (tranches[key] ? tranches[key].energy : 0), 0);
    if (kind === "hphc") {
      return tile(this._t("offPeakShare"), this._share(used("hc") / energy), this._kwh(used("hc")));
    }
    // Without a red day, there is nothing to tell.
    if (kind !== "tempo" || !(used("red_hc", "red_hp") > 0)) return null;
    return tile(this._t("redPeak"), this._share(used("red_hp") / energy, 1), this._kwh(used("red_hp")));
  }

  _share(value, digits = 0) {
    return new Intl.NumberFormat(this._locale, { style: "percent", minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
  }

  _contractsToday() {
    const today = dayString(Date.now());
    const entry = this._entry;
    return entry ? entry.contracts.filter((contract) => contract.active_from && contract.active_from <= today && (!contract.active_to || contract.active_to >= today)) : [];
  }

  // The contracts in force today, in the toolbar: each opens its prices.
  _renderContractChips() {
    this._chips.replaceChildren(
      ...this._contractsToday().map((contract) => {
        const open = Boolean(this._contractOpen[contract.id]);
        return h(
          "button",
          {
            class: "contract-chip",
            "aria-expanded": String(open),
            title: this._t(open ? "hidePrices" : "showPrices"),
            onclick: () => {
              this._contractOpen[contract.id] = !open;
              this._renderHead();
            },
          },
          h("strong", {}, contract.name),
          contract.kva ? h("span", { class: "kva" }, `${contract.kva} kVA`) : null,
          icon(ICONS.down),
        );
      }),
    );
  }

  // The prices of each contract whose chip is open: every price it has had.
  _renderContractPrices() {
    const today = dayString(Date.now());
    const inForce = this._data ? this._contractsInForce() : [];
    return this._contractsToday()
      .filter((contract) => this._contractOpen[contract.id])
      .map((contract) => {
        const kind = KINDS[this._language][contract.kind] || contract.kind;
        const facts = [
          // The kind says nothing more when the contract is named after it.
          kind !== contract.name ? kind : null,
          contract.kva ? `${contract.kva} kVA` : null,
          this._t(contract.official ? "regulated" : "manualPrices"),
          this._t("since", { date: this._dayLabel(contract.active_from) }),
          contract.off_peak.length ? this._t("offPeakHours", { ranges: contract.off_peak.join(", ") }) : null,
          contract.weekend_off_peak ? this._t("weekendOffPeak") : null,
        ];
        const sub = h("p", { class: "sub facts" }, facts.filter(Boolean).join(" · "));
        const periods = contract.prices;
        if (!periods.length) {
          return this._card(contract.name, [sub, h("p", { class: "sub" }, this._t("noPrices"))]);
        }
        const current = periods.findIndex((period) => period.start <= today && (!period.end || period.end >= today));
        const index = Math.min(this._pricePeriods[contract.id] ?? (current >= 0 ? current : periods.length - 1), periods.length - 1);
        const rise = current > 0 && inForce.length === 1 && inForce[0].id === contract.id ? this._priceRise(inForce[0], periods[current], periods[current - 1]) : null;
        return this._card(contract.name, [
          sub,
          this._nav(this._periodLabel(periods[index]), index > 0, index < periods.length - 1, (step) => {
            this._pricePeriods[contract.id] = index + step;
            this._renderHead();
          }),
          this._priceTiles(contract, periods, index, today),
          rise,
        ]);
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
    if (this._cumulativeChart) {
      this._renderCumulativeChart(this._data.contracts.find((contract) => contract.id === this._billContract));
    }
    if (this._calendarChart) {
      this._drawCalendar(this._calendarChart, this._calendarDetail, this._insights.days);
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
    const actual = { id: ACTUAL, name: this._t({ energy: "consumption", price: "averagePrice" }[this._measure] || "actual") };
    const missing = this._data.series.some((bucket) => bucket.actual === null);
    const temperatures = this._bucketTemperatures();
    const measure = this._measureOf();
    const partial = this._partialBuckets();
    if (this._views.time === "chart") {
      const series = [{ ...actual, values: this._data.series.map((bucket) => measure.value(bucket) ?? 0) }];
      const options = { temperatures, axis: measure.axis, format: measure.format, partial };
      const frame =
        this._data.group_by === "month"
          ? this._drawColumns(this._timeChart, series, options)
          : this._drawLines(this._timeChart, series, { zero: false, ...options });
      if (temperatures) {
        this._timeChart.append(this._temperatureStrip(frame, temperatures));
      }
    } else {
      const extra = temperatures && { label: this._t("temperature"), values: temperatures, format: (value) => this._degrees(value) };
      this._timeChart.replaceChildren(this._seriesTable((bucket) => measure.value(bucket), false, [actual], extra, measure.format));
    }
    if (this._views.time === "chart") {
      this._timeChart.append(
        this._keys(
          [h("span", { class: "swatch", style: { background: "var(--ec-money)" } }), actual.name],
          partial.size ? [h("span", { class: "swatch hatched" }), this._t("partialMonth")] : null,
          temperatures ? [h("span", { class: "line-key", style: { background: "var(--ec-s2)" } }), this._t("temperature")] : null,
        ),
      );
    }
    if (missing && this._measure !== "energy") {
      this._timeChart.append(h("p", { class: "note" }, this._t("partialActual")));
    }
  }

  _renderCumulativeChart(contract) {
    const gap = this._gap(contract.id);
    const series = [{ id: ACTUAL, name: contract.name, values: gap.values }];
    if (this._views.cumulative === "chart") {
      const frame = this._drawLines(this._cumulativeChart, series, { zero: true });
      // Each side of zero says which contract it favors.
      const mine = this._mineName() || this._t("yourContractName");
      const left = `${frame.margin.left + 8}px`;
      if (Math.max(...gap.values) > 0) {
        this._cumulativeChart.append(h("span", { class: "side", style: { left, top: `${frame.margin.top + 2}px` } }, this._t("cheaperArrowUp", { name: mine })));
      }
      if (Math.min(...gap.values) < 0) {
        this._cumulativeChart.append(h("span", { class: "side", style: { left, top: `${frame.margin.top + frame.plotHeight - 18}px` } }, this._t("cheaperArrowDown", { name: contract.name })));
      }
    } else {
      this._cumulativeChart.replaceChildren(this._seriesTable((bucket, item, index) => gap.values[index], false, series));
    }
    if (gap.partial) {
      this._cumulativeChart.append(h("p", { class: "note" }, this._t("partialActual")));
    }
  }

  // What the contract would have cost more than what was paid, summed bucket
  // after bucket: above zero, the contract in force was the cheaper.
  _gap(contractId) {
    let total = 0;
    let partial = false;
    const values = this._data.series.map((bucket) => {
      if (bucket.actual === null) {
        partial = true;
      } else {
        total += (bucket.contracts[contractId] ?? 0) - bucket.actual;
      }
      return Math.round(total * 100) / 100;
    });
    return { values, partial };
  }

  _frame(container, values, zero, axis = (value, digits) => this._money(value, digits)) {
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
    const tickStep = ticks.length > 1 ? ticks[1] - ticks[0] : 1;
    const digits = tickStep < 0.1 ? 2 : tickStep < 1 ? 1 : 0;
    const labels = ticks.map((tick) => axis(tick, digits));
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

  // Columns, hatched where a bucket is only partly covered by the data.
  _drawColumns(container, series, { temperatures = null, axis, format, partial = new Set() } = {}) {
    const values = series.flatMap((item) => item.values);
    const frame = this._frame(container, values, false, axis);
    frame.temperatures = temperatures;
    frame.format = format;
    const { root, margin, plotHeight, x, y, band } = frame;
    const wash = s("rect", { y: margin.top, height: plotHeight, width: band, style: { fill: "var(--ec-wash)", visibility: "hidden" } });
    root.insertBefore(wash, root.firstChild);
    const hatch = `ec-hatch-${(this._patterns = (this._patterns || 0) + 1)}`;
    root.insertBefore(
      s(
        "defs",
        {},
        s(
          "pattern",
          { id: hatch, width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" },
          s("rect", { width: 6, height: 6, style: { fill: "var(--ec-money-soft)" } }),
          s("rect", { width: 2.5, height: 6, style: { fill: "var(--ec-money)" } }),
        ),
      ),
      root.firstChild,
    );
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
        const color = this._color(item.id);
        marks.append(
          s("path", {
            d: columnPath(left + position * (barWidth + gap), barWidth, base, y(value)),
            style: partial.has(index) ? { fill: `url(#${hatch})`, stroke: color, "stroke-width": "1.5px" } : { fill: color },
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

  _drawLines(container, series, { zero, temperatures = null, axis, format }) {
    const values = series.flatMap((item) => item.values);
    const frame = this._frame(container, values, zero, axis);
    frame.temperatures = temperatures;
    frame.format = format;
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
        h(
          "div",
          { class: "row" },
          h("span", { class: "line-key", style: { background: this._color(item.id) } }),
          h("strong", {}, (frame.format || ((amount) => this._money(amount)))(value)),
          h("span", {}, item.name),
        ),
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

  _seriesTable(value, withActual, contracts = this._data.contracts, extra = null, format = (amount) => this._money(amount)) {
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
          return h("td", {}, amount === null || amount === undefined ? "—" : format(amount));
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
      this._outlookLoaded = true;
      return;
    }
    try {
      this._outlook = await this._hass.callWS({ type: `${DOMAIN}/outlook`, entry_id: entry.entry_id });
      this._outlookError = null;
    } catch (error) {
      // The rest of the page stands without it.
      this._outlook = null;
      this._outlookError = error.message || String(error);
    }
    this._outlookLoaded = true;
    // Again when the price changes, and at least every half hour.
    const first = this._outlook && this._outlook.prices[0];
    const wait = first ? Date.parse(first.end) - Date.now() + 5000 : Infinity;
    this._outlookTimer = setTimeout(() => this._loadOutlook().then(() => this._renderHead()), Math.max(60000, Math.min(wait, 30 * 60000)));
  }

  _time(iso) {
    return new Intl.DateTimeFormat(this._locale, { hour: "numeric", minute: "2-digit", timeZone: "Europe/Paris" }).format(new Date(iso));
  }

  _degrees(value) {
    return `${this._number(value, 1)} °C`;
  }

  // A card standing for one still loading.
  _loadingCard() {
    const bone = (width, height) => h("span", { class: "bone", style: { width, height: `${height}px` } });
    return h("section", { class: "card skeleton", "aria-busy": "true" }, bone("40%", 14), h("div", { style: { height: "16px" } }), bone("60%", 28), h("div", { style: { height: "16px" } }), bone("100%", 32));
  }

  // Today's date over the price now and over the next 24 hours, then
  // tomorrow's Tempo color.
  _renderNow() {
    const day = capitalize(new Intl.DateTimeFormat(this._locale, { weekday: "long", day: "numeric", month: "long", timeZone: "Europe/Paris" }).format(new Date()), this._locale);
    if (this._outlookError) {
      return this._errorCard(day, this._t("liveFailed", { error: this._outlookError }), () => this._refreshOutlook());
    }
    if (!this._outlookLoaded) return this._loadingCard();
    const outlook = this._outlook;
    if (!outlook || !outlook.contract || !outlook.prices.length) return null;
    const names = TRANCHES[this._language];
    const segments = outlook.prices;
    const [current, next] = segments;
    const name = (tranche) => (tranche ? names[tranche] : this._t("unknownColor"));
    const perKwh = (price) => this._t("perKwh", { price: this._price(price) });
    const priced = segments.filter((segment) => segment.price !== null);
    const cheapest = priced.length ? Math.min(...priced.map((segment) => segment.price)) : null;
    // The cheaper time ahead, written in its block of the ribbon.
    let cheaper = null;
    let cheaperLabel = "";
    if (cheapest !== null && (current.price === null || current.price > cheapest + 1e-9)) {
      cheaper = priced.find((segment) => segment.price === cheapest);
      const change = current.price ? this._percent(cheapest / current.price - 1) : null;
      cheaperLabel = change ? `${this._price(cheapest)} · ${change}` : this._price(cheapest);
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
          segment === cheaper && share(segment) > 0.14 ? cheaperLabel : "",
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
    const tempo = this._insights && this._insights.tempo;
    const [fill, ink] = current.tranche ? TRANCHE_FILLS[current.tranche] : [];
    return this._card(
      day,
      [
        h(
          "div",
          { class: "price-now" },
          h("strong", {}, current.price !== null ? this._price(current.price) : "—"),
          h("span", { class: "sub" }, "/kWh"),
          h("span", { class: "tranche", style: fill ? { background: fill, color: ink } : {} }, name(current.tranche)),
          current.tranche && next ? h("span", { class: "sub" }, this._t("untilTime", { time: this._time(current.end) })) : null,
        ),
        ribbon,
        ticks,
        tempo ? this._tomorrowLine(tempo) : null,
      ],
    );
  }

  // Tomorrow's Tempo color, with what the day should cost: in each color
  // until it is published.
  _tomorrowLine(tempo) {
    const colors = COLORS[this._language];
    const estimate = tempo.tomorrow_estimate;
    const color = (name, cost) => [
      h("span", { class: "swatch", style: { background: DAY_FILLS[name] } }),
      h("span", {}, colors[name]),
      cost !== null && cost !== undefined ? [h("span", { class: "sub" }, "·"), h("strong", {}, this._money(cost))] : null,
    ];
    return h(
      "div",
      { class: "tomorrow" },
      h(
        "div",
        { class: "line" },
        h("span", { class: "sub" }, this._t("tomorrow")),
        tempo.tomorrow ? color(tempo.tomorrow, estimate && estimate.cost) : h("span", { class: "sub" }, this._t("notPublished")),
      ),
      estimate && !tempo.tomorrow && estimate.costs
        ? h(
            "div",
            { class: "pills" },
            ["blue", "white", "red"].map((name) => h("span", { class: "pill" }, color(name, estimate.costs[name]))),
          )
        : null,
    );
  }

  // The red and white days left in the Tempo season.
  _tempoMeters(tempo, compact = false) {
    const colors = COLORS[this._language];
    const season = tempo.season;
    const meter = (color, left, total) =>
      h(
        "div",
        { class: "meter" },
        h(
          "div",
          { class: "row" },
          h("span", {}, compact ? this._t(`${color}Left`) : colors[color]),
          h("strong", { title: this._t("daysLeft", { left, total }) }, compact ? String(left) : this._t("daysLeft", { left, total })),
        ),
        h("div", { class: "track", role: "img", "aria-label": `${colors[color]}: ${this._t("daysLeft", { left, total })}` }, h("div", { class: "fill", style: { width: `${(left / total) * 100}%`, background: DAY_FILLS[color] } })),
      );
    return h("div", { class: compact ? "meters compact" : "meters" }, meter("red", season.red_left, season.red_total), meter("white", season.white_left, season.white_total));
  }

  // What the season should cost by 31 August, against what it has cost so far.
  _renderSeason() {
    if (!this._outlookLoaded) return this._loadingCard();
    const tempo = this._insights && this._insights.tempo;
    const season = this._outlook && this._outlook.season;
    if (!season) {
      if (!tempo) return null;
      const label = `${tempo.season.start.slice(0, 4)}-${tempo.season.end.slice(0, 4)}`;
      return this._card(this._t("season", { season: label }), this._tempoMeters(tempo), { rerender: () => this._renderHead() });
    }
    const label = `${season.start.slice(0, 4)}-${season.end.slice(0, 4)}`;
    const long = { day: "numeric", month: "long", year: "numeric" };
    const until = this._dayLabel(season.until, { day: "numeric", month: "long" });
    const { total, previous, projection, spent } = season;
    const span = (first, last) => (dayTime(last) - dayTime(first)) / DAY_MS + 1;
    // Where spending at an even pace would be, marked on the money bar.
    const elapsed = span(season.start, season.until) / span(season.start, season.end);
    let bar = null;
    if (projection) {
      const width = (amount) => `${(amount / Math.max(total, 1)) * 100}%`;
      bar = h(
        "div",
        {
          class: "budget",
          role: "img",
          "aria-label": `${this._t("spentLegend")} ${this._money(spent.cost, 0)}, ${this._t("expectedLegend")} ${this._money(projection.cost, 0)}`,
        },
        h(
          "div",
          { class: "budget-bar" },
          spent.cost > 0 ? h("div", { class: "spent", style: { width: width(spent.cost) } }) : null,
          h("div", { class: spent.cost > 0 ? "rest" : "rest alone", style: { width: width(projection.cost) } }),
        ),
        h("span", { class: "marker", title: until, style: { left: width(elapsed * total) } }),
      );
    }
    return this._card(
      this._t("seasonTitle", { season: label }),
      [
        total !== null
          ? this._lead(this._money(total, 0), this._t("expectedPerMonth", { amount: this._money(total / 12, 0) }))
          : this._lead(this._money(spent.cost, 0), this._t("spentUntil", { day: until })),
        bar,
        bar ? h("div", { class: "spent-line" }, h("strong", {}, this._money(spent.cost, 0)), " ", h("span", { class: "sub" }, this._t("spent"))) : null,
        tempo ? this._tempoMeters(tempo, true) : null,
      ],
      {
        info: [
          this._t("seasonHint", { start: this._dayLabel(season.start, long), end: this._dayLabel(season.end, long), contract: this._outlook.contract.name }),
          [
            this._t("seasonSpent", { spent: this._money(spent.cost, 0), day: until, energy: this._kwh(spent.energy) }),
            projection ? this._t("seasonExpected", { expected: this._money(projection.cost, 0), energy: this._kwh(projection.energy) }) : null,
          ]
            .filter(Boolean)
            .join(" "),
          previous ? this._t("previousSeason", { total: this._money(previous.total, 0), toDate: this._money(previous.to_date, 0) }) : null,
          season.complete ? null : this._t("budgetPartial"),
          projection ? this._t("budgetMethod") : this._t("budgetNoProjection"),
        ],
        rerender: () => this._renderHead(),
      },
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
    const height = 104;
    const top = 12;
    const bottom = 8;
    const ticks = niceTicks(Math.min(...known), Math.max(...known), 3);
    const low = ticks[0];
    const high = ticks[ticks.length - 1];
    const plot = height - top - bottom;
    const y = (value) => top + plot - ((value - low) / (high - low || 1)) * plot;
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": this._t("temperatureStrip") });
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

  // The typical day -------------------------------------------------------------

  // The average hour of the period, with the off-peak hours of the contract in
  // force shaded behind it.
  _renderProfile() {
    const values = this._insights.profile.map((value) => value ?? 0);
    const day = values.reduce((sum, value) => sum + value, 0);
    if (!(day > 0)) return null;
    const share = this._offPeakShare();
    // The highest hour, and the next one when it comes close.
    const order = values.map((value, hour) => hour).sort((first, second) => values[second] - values[first]);
    const peaks =
      values[order[1]] >= 0.75 * values[order[0]]
        ? this._t("peaksAt", { first: this._hour(order[0]), second: this._hour(order[1]) })
        : this._t("peakAt", { hour: this._hour(order[0]) });
    this._profileChart = h("div", { class: "chart" });
    return this._card(
      this._t("profile"),
      [
        share !== null
          ? this._lead(this._share(share), `${this._t("offPeakLead")} · ${peaks}`)
          : this._lead(this._kwh(day), `${this._t("aDay")} · ${peaks}`),
        this._profileChart,
        this._keys(
          [h("span", { class: "swatch", style: { background: "var(--ec-money)" } }), this._t("hourlyKwh")],
          this._offPeakRanges().length ? [h("span", { class: "swatch", style: { background: "var(--ec-wash)", "box-shadow": "inset 0 0 0 1px var(--ec-axis)" } }), capitalize(this._t("offPeakBand"), this._locale)] : null,
        ),
      ],
      { info: [this._t("profileInfo", { days: this._number(this._insights.days.length) })] },
    );
  }

  // The off-peak ranges of the one contract in force, in hours of the day.
  _offPeakRanges() {
    const inForce = this._contractsInForce();
    const contract = inForce.length === 1 ? this._entry.contracts.find((item) => item.id === inForce[0].id) : null;
    if (!contract) return [];
    const ranges = contract.kind === "tempo" ? ["22:00-06:00"] : contract.off_peak || [];
    return ranges.map((range) => range.split("-").map((time) => Number(time.slice(0, 2)) + Number(time.slice(3, 5)) / 60));
  }

  // The share of the consumption in off-peak hours, from the tranches of the
  // one contract in force: exact, weekends included.
  _offPeakShare() {
    const inForce = this._contractsInForce();
    if (inForce.length !== 1 || inForce[0].kind === "base") return null;
    const tranches = Object.entries(inForce[0].tranches);
    const energy = tranches.reduce((sum, [, item]) => sum + item.energy, 0);
    if (!(energy > 0)) return null;
    return tranches.filter(([tranche]) => tranche === "hc" || tranche.endsWith("_hc")).reduce((sum, [, item]) => sum + item.energy, 0) / energy;
  }

  _hour(hour) {
    return this._t("hourOfDay", { hour: hour % 24 });
  }

  _drawProfile(container, profile) {
    const values = profile.map((value) => value ?? 0);
    const width = Math.max(container.clientWidth || 320, 240);
    const height = 200;
    const ticks = niceTicks(0, Math.max(...values, 0.01), 3);
    const high = ticks[ticks.length - 1];
    const tickStep = ticks[1] - ticks[0];
    const labels = ticks.map((tick) => this._number(tick, Number.isInteger(tick) ? 0 : tickStep < 0.1 ? 2 : 1));
    const margin = { top: 22, right: 4, bottom: 24, left: Math.max(...labels.map((label) => label.length)) * 7 + 10 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const band = plotWidth / 24;
    const at = (hour) => margin.left + band * hour;
    const y = (value) => margin.top + plotHeight - (value / high) * plotHeight;
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": this._t("profile") });
    // The off-peak hours, shaded behind the columns and named above them.
    const long = this._t("offPeakBand");
    const short = this._t("offPeakBandShort");
    for (const [start, end] of dayPieces(this._offPeakRanges())) {
      const span = at(end) - at(start);
      if (span <= 0) continue;
      root.append(s("rect", { x: at(start), y: margin.top, width: span, height: plotHeight, style: { fill: "var(--ec-wash)" } }));
      const label = span >= long.length * 6.5 + 8 ? long : span >= short.length * 6.5 + 4 ? short : null;
      if (label) root.append(s("text", { x: at(start) + span / 2, y: margin.top - 8, "text-anchor": "middle" }, label));
    }
    ticks.forEach((tick, index) => {
      root.append(
        s("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), style: { stroke: tick === 0 ? "var(--ec-axis)" : "var(--ec-grid)", "stroke-width": "1px" } }),
        s("text", { x: margin.left - 6, y: y(tick), "text-anchor": "end", "dominant-baseline": "middle" }, labels[index]),
      );
    });
    const bar = Math.max(2, Math.min(16, band * 0.65));
    const every = band * 3 >= 48 ? 3 : 6;
    values.forEach((value, hour) => {
      if (value > 0) {
        root.append(s("path", { d: columnPath(at(hour) + (band - bar) / 2, bar, y(0), y(value)), style: { fill: "var(--ec-money)" } }));
      }
      if (hour % every === 0) {
        root.append(s("text", { x: at(hour) + band / 2, y: height - 6, "text-anchor": "middle" }, this._hour(hour)));
      }
    });
    const tooltip = this._bandHits(root, {
      x: at,
      band,
      top: margin.top,
      height: plotHeight,
      count: 24,
      head: (hour) => `${this._hour(hour)} – ${this._hour(hour + 1)}`,
      value: (hour) => `${this._number(values[hour], 2)} kWh`,
    });
    container.replaceChildren(root, tooltip);
  }

  // The pointer and keyboard layer of a chart of bands: the band under the
  // pointer or the focus is washed and described in a tooltip.
  _bandHits(root, { x, band, top, height, count, head, value }) {
    const width = Number(root.getAttribute("width"));
    const wash = s("rect", { y: top, width: band, height, style: { fill: "var(--ec-wash)", visibility: "hidden" } });
    root.insertBefore(wash, root.firstChild);
    const tooltip = h("div", { class: "tooltip", hidden: true });
    const hits = s("g");
    for (let index = 0; index < count; index++) {
      const show = () => {
        wash.setAttribute("x", x(index));
        wash.style.visibility = "visible";
        tooltip.replaceChildren(h("div", { class: "head" }, head(index)), h("div", { class: "row" }, h("strong", {}, value(index))));
        tooltip.hidden = false;
        const center = x(index) + band / 2;
        const left = center + 12 + tooltip.offsetWidth > width ? center - 12 - tooltip.offsetWidth : center + 12;
        tooltip.style.left = `${Math.max(0, left)}px`;
        tooltip.style.top = `${top}px`;
      };
      const hide = () => {
        wash.style.visibility = "hidden";
        tooltip.hidden = true;
      };
      hits.append(
        s("rect", {
          class: "hit",
          x: x(index),
          y: top,
          width: band,
          height,
          tabindex: 0,
          "aria-label": `${head(index)}, ${value(index)}`,
          onpointerenter: show,
          onpointerleave: hide,
          onfocus: show,
          onblur: hide,
        }),
      );
    }
    root.append(hits);
    return tooltip;
  }

  // Tempo colors ------------------------------------------------------------------

  // The Tempo contract the colors are read from: the one in force, else the
  // first compared.
  _tempoContract() {
    const tempo = (contract) => contract.kind === "tempo";
    return this._contractsInForce().find(tempo) || this._data.contracts.find(tempo) || null;
  }

  // How much of a Tempo day of each color went into peak hours: red days spent
  // in off-peak hours show the consumption is moved.
  _renderPeakByColor() {
    const contract = this._tempoContract();
    if (!contract) return null;
    const names = COLORS[this._language];
    const days = {};
    for (const day of this._insights.days) {
      if (day.color) days[day.color] = (days[day.color] || 0) + 1;
    }
    const energy = (tranche) => (contract.tranches[tranche] ? contract.tranches[tranche].energy : 0);
    const rows = ["blue", "white", "red"]
      .map((color) => {
        const peak = energy(`${color}_hp`);
        const total = peak + energy(`${color}_hc`);
        return { color, days: days[color] || 0, share: total > 0 ? peak / total : null };
      })
      .filter((row) => row.share !== null);
    if (!rows.length) return null;
    const blue = rows.find((row) => row.color === "blue");
    const red = rows.find((row) => row.color === "red");
    const lead = red || blue || rows[0];
    const context = [this._t(IN_PEAK_ON[lead.color]), red && blue ? this._t("peakOnBlue", { share: this._share(blue.share) }) : null].filter(Boolean).join(" · ");
    const segment = (tranche, part, label) => {
      const [fill, ink] = TRANCHE_FILLS[tranche];
      return part > 0 ? h("div", { class: "segment", style: { "flex-grow": String(part), "flex-basis": "0", background: fill, color: ink } }, label) : null;
    };
    const label = (short, part) => (part >= 0.2 ? `${this._t(short)} ${this._share(part)}` : part >= 0.08 ? this._share(part) : "");
    return this._card(
      this._t("peakByColor"),
      [
        this._lead(this._share(lead.share), context),
        h(
          "div",
          { class: "colors" },
          rows.map((row) =>
            h(
              "div",
              { class: "color-row" },
              h("span", { class: "who" }, names[row.color], h("span", { class: "sub" }, ` ${this._count(row.days, "oneDay", "dayCount")}`)),
              h(
                "div",
                {
                  class: "segments",
                  role: "img",
                  "aria-label": this._t("peakSplitLabel", { color: names[row.color], peak: this._share(row.share), offPeak: this._share(1 - row.share) }),
                },
                segment(`${row.color}_hp`, row.share, label("peakShort", row.share)),
                segment(`${row.color}_hc`, 1 - row.share, label("offPeakShort", 1 - row.share)),
              ),
            ),
          ),
        ),
      ],
    );
  }

  _count(count, one, other) {
    return this._t(new Intl.PluralRules(this._locale).select(count) === "one" ? one : other, { count: this._number(count) });
  }

  // Baseload -----------------------------------------------------------------------

  _renderBaseload() {
    const baseload = this._insights.baseload;
    if (!baseload) return null;
    const weekly = baseload.nights.length > WEEKLY_NIGHTS;
    this._baseloadChart = baseload.nights.length > 1 ? h("div", { class: "chart" }) : null;
    const context = [
      this._t("aroundTheClock"),
      baseload.annual_cost !== null ? this._t("perYear", { amount: this._money(baseload.annual_cost, 0) }) : null,
      baseload.share !== null ? this._t("ofTheConsumption", { share: this._share(baseload.share) }) : null,
    ];
    return this._card(
      this._t("baseload"),
      [
        this._lead(`${this._number(baseload.power)} W`, context.filter(Boolean).join(" · ")),
        this._baseloadChart,
        this._baseloadChart
          ? this._keys(
              [h("span", { class: "swatch", style: { background: "var(--ec-money)" } }), this._t(weekly ? "weeklyLowKey" : "nightlyLowKey")],
              [h("span", { class: "dash-key" }), this._t("baseload")],
            )
          : null,
      ],
      { info: [this._t("baseloadInfo", { energy: this._kwh(baseload.annual_energy) }), this._t("baseloadNote")] },
    );
  }

  // The quietest hour night after night, or week after week over a long period,
  // with the baseload the headline gives. A night far above the others is cut
  // at the top of the scale, its value written beside it.
  _drawNights(container, baseload) {
    const weekly = baseload.nights.length > WEEKLY_NIGHTS;
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
    const height = 160;
    const sorted = nights.map((night) => night.power).sort((first, second) => first - second);
    const usual = Math.max(sorted[Math.floor(0.9 * (sorted.length - 1))] * 1.25, baseload.power * 1.5, 1);
    const most = sorted[sorted.length - 1];
    const ticks = niceTicks(0, most > usual * 1.3 ? usual : most, 3);
    const high = ticks[ticks.length - 1];
    const labels = ticks.map((tick, index) => (index === ticks.length - 1 ? `${this._number(tick)} W` : this._number(tick)));
    const margin = { top: 20, right: 8, bottom: 22, left: Math.max(...labels.map((label) => label.length)) * 7 + 10 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const band = plotWidth / nights.length;
    const at = (index) => margin.left + band * index;
    const y = (value) => margin.top + plotHeight - (Math.min(value, high) / high) * plotHeight;
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": this._t("baseload") });
    ticks.forEach((tick, index) => {
      root.append(
        s("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), style: { stroke: tick === 0 ? "var(--ec-axis)" : "var(--ec-grid)", "stroke-width": "1px" } }),
        s("text", { x: margin.left - 6, y: y(tick), "text-anchor": "end", "dominant-baseline": "middle" }, labels[index]),
      );
    });
    const bar = Math.max(2, Math.min(14, band * 0.6));
    let cut = null;
    nights.forEach((night, index) => {
      const left = at(index) + (band - bar) / 2;
      root.append(s("path", { d: columnPath(left, bar, y(0), y(night.power)), style: { fill: "var(--ec-money)" } }));
      if (night.power > high) {
        // Two strokes of the card's color across a cut column.
        root.append(s("path", { d: `M${left - 1},${margin.top + 10}l${bar + 2},-4m${-(bar + 2)},8l${bar + 2},-4`, style: { fill: "none", stroke: "var(--ec-surface)", "stroke-width": "2px" } }));
        if (cut === null || night.power > nights[cut].power) cut = index;
      }
    });
    if (cut !== null) {
      const center = at(cut) + band / 2;
      const right = center + bar / 2 + 4;
      const label = `${this._number(nights[cut].power)} W`;
      const before = right + label.length * 7 > width;
      root.append(s("text", { x: before ? center - bar / 2 - 4 : right, y: margin.top + 6, "text-anchor": before ? "end" : "start", "dominant-baseline": "middle", class: "ink" }, label));
    }
    // The dates under the columns: the months of a long period, a day a week
    // otherwise.
    let month = null;
    let end = -Infinity;
    nights.forEach((night, index) => {
      if (weekly ? night.date.slice(0, 7) === month : index % 7 !== 0) return;
      month = night.date.slice(0, 7);
      const label = this._dayLabel(night.date, weekly ? { month: "short" } : { day: "numeric", month: "short" });
      const x = at(index) + band / 2;
      if (x - label.length * 3.5 < end + 4) return;
      root.append(s("text", { x, y: height - 6, "text-anchor": "middle" }, label));
      end = x + label.length * 3.5;
    });
    root.append(
      s("line", { x1: margin.left, x2: width - margin.right, y1: y(baseload.power), y2: y(baseload.power), style: { stroke: "var(--ec-text)", "stroke-width": "1.5px", "stroke-dasharray": "4 3" } }),
      s("text", { x: width - margin.right, y: y(baseload.power) - 6, "text-anchor": "end", class: "ink halo" }, `${this._number(baseload.power)} W`),
    );
    const tooltip = this._bandHits(root, {
      x: at,
      band,
      top: margin.top,
      height: plotHeight,
      count: nights.length,
      head: (index) =>
        weekly
          ? this._t("weekOf", { day: this._dayLabel(nights[index].date, { day: "numeric", month: "long", year: "numeric" }) })
          : this._dayLabel(nights[index].date, { weekday: "long", day: "numeric", month: "long" }),
      value: (index) => `${this._number(nights[index].power)} W`,
    });
    container.replaceChildren(root, tooltip);
  }

  // Consumption and weather ------------------------------------------------------

  _renderWeather() {
    const weather = this._insights.weather;
    if (!weather) {
      return this._card(this._t("weather"), [
        h("p", { class: "message" }, this._t("weatherSetup")),
        h("a", { class: "toggle", href: `/config/integrations/integration/${DOMAIN}` }, this._t("weatherOpen")),
      ]);
    }
    if (!weather.days) {
      return this._card(this._t("weather"), h("p", { class: "message" }, this._t("weatherNoData")));
    }
    const base = `${this._number(weather.base)} °C`;
    const heating = weather.slope !== null && weather.slope > 0;
    this._weatherChart = h("div", { class: "chart" });
    return this._card(
      this._t("weather"),
      [
        heating
          ? this._lead(
              `+${this._kwh(weather.slope)}`,
              [this._t("perDegreeBelow", { base }), weather.heating_share !== null ? this._t("ofTheConsumption", { share: this._share(weather.heating_share) }) : null].filter(Boolean).join(" · "),
            )
          : h("p", { class: "message" }, this._t(weather.slope === null ? "weatherFewDays" : "noHeating")),
        this._weatherChart,
        this._keys(
          [h("span", { class: "dot-key" }), this._t("oneDayKey")],
          heating ? [h("span", { class: "line-key", style: { background: "var(--ec-text)" } }), this._t("trend")] : null,
        ),
      ],
      {
        info: [
          this._t("weatherInfo"),
          heating ? this._t("withHeating", { base, energy: this._kwh(Math.max(0, weather.intercept)), slope: this._kwh(weather.slope) }) : null,
        ],
      },
    );
  }

  // Each day at its temperature and consumption, with the fitted line: flat
  // above the base temperature, rising below it.
  _drawWeather(container, insights) {
    const weather = insights.weather;
    const points = insights.days.filter((day) => day.temperature !== null);
    const width = Math.max(container.clientWidth || 320, 240);
    const height = width < 500 ? 220 : 240;
    const temperatures = points.map((point) => point.temperature);
    const xTicks = niceTicks(Math.min(...temperatures), Math.max(...temperatures), width < 500 ? 4 : 6);
    const yTicks = niceTicks(0, Math.max(...points.map((point) => point.energy), 0.01), 4);
    const yStep = yTicks[1] - yTicks[0];
    const yLabels = yTicks.map((tick) => this._number(tick, Number.isInteger(tick) ? 0 : yStep < 0.1 ? 2 : 1));
    const margin = { top: 24, right: 18, bottom: 24, left: Math.max(...yLabels.map((label) => label.length)) * 7 + 12 };
    const low = xTicks[0];
    const high = xTicks[xTicks.length - 1];
    const top = yTicks[yTicks.length - 1];
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const x = (value) => margin.left + ((value - low) / (high - low || 1)) * plotWidth;
    const y = (value) => margin.top + plotHeight - (value / top) * plotHeight;
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": this._t("weather") });
    const clip = `ec-clip-${(this._patterns = (this._patterns || 0) + 1)}`;
    root.append(s("defs", {}, s("clipPath", { id: clip }, s("rect", { x: margin.left, y: margin.top, width: plotWidth, height: plotHeight }))));
    yTicks.forEach((tick, index) => {
      root.append(
        s("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), style: { stroke: tick === 0 ? "var(--ec-axis)" : "var(--ec-grid)", "stroke-width": "1px" } }),
        s("text", { x: margin.left - 8, y: y(tick), "text-anchor": "end", "dominant-baseline": "middle" }, yLabels[index]),
      );
    });
    root.append(s("text", { x: margin.left, y: 12 }, this._t("kwhPerDay")));
    xTicks.forEach((tick, index) => {
      root.append(s("text", { x: x(tick), y: height - 6, "text-anchor": "middle" }, index === xTicks.length - 1 ? `${this._number(tick)} °C` : this._number(tick)));
    });
    if (weather.base > low && weather.base < high) {
      root.append(
        s("line", { x1: x(weather.base), x2: x(weather.base), y1: margin.top, y2: margin.top + plotHeight, style: { stroke: "var(--ec-muted)", "stroke-width": "1px", "stroke-dasharray": "3 3" } }),
        s("text", { x: x(weather.base) + 6, y: margin.top + 10, class: "ink halo" }, `${this._number(weather.base)} °C`),
      );
    }
    const dots = s("g");
    for (const point of points) {
      dots.append(s("circle", { cx: x(point.temperature), cy: y(point.energy), r: 4, style: { fill: "var(--ec-money)", "fill-opacity": "0.7", stroke: "var(--ec-surface)", "stroke-width": "1px" } }));
    }
    root.append(dots);
    if (weather.slope !== null && weather.slope > 0) {
      const model = (value) => Math.max(0, weather.intercept + weather.slope * Math.max(0, weather.base - value));
      const knots = [low, ...(weather.base > low && weather.base < high ? [weather.base] : []), high];
      root.append(
        s("polyline", {
          points: knots.map((value) => `${x(value)},${y(model(value))}`).join(" "),
          "clip-path": `url(#${clip})`,
          style: { fill: "none", stroke: "var(--ec-text)", "stroke-width": "2px", "stroke-linejoin": "round", "stroke-linecap": "round" },
        }),
      );
    }
    // The pointer picks the nearest day; the arrow keys go through the days from
    // the coldest to the warmest.
    const names = COLORS[this._language];
    const order = points.map((point, index) => index).sort((first, second) => points[first].temperature - points[second].temperature);
    const ring = s("circle", { r: 6, style: { fill: "none", stroke: "var(--ec-text)", "stroke-width": "2px", visibility: "hidden", "pointer-events": "none" } });
    const tooltip = h("div", { class: "tooltip", hidden: true });
    let focused = order.length - 1;
    const show = (index) => {
      const point = points[index];
      const cx = x(point.temperature);
      const cy = y(point.energy);
      ring.setAttribute("cx", cx);
      ring.setAttribute("cy", cy);
      ring.style.visibility = "visible";
      tooltip.replaceChildren(
        h("div", { class: "head" }, [this._dayLabel(point.date, { weekday: "long", day: "numeric", month: "long" }), point.color ? names[point.color].toLowerCase() : null].filter(Boolean).join(" · ")),
        h("div", { class: "row" }, h("strong", {}, this._kwh(point.energy)), h("span", {}, this._degrees(point.temperature))),
      );
      tooltip.hidden = false;
      const left = cx + 12 + tooltip.offsetWidth > width ? cx - 12 - tooltip.offsetWidth : cx + 12;
      tooltip.style.left = `${Math.max(0, left)}px`;
      tooltip.style.top = `${Math.max(0, cy - 24)}px`;
    };
    const hide = () => {
      ring.style.visibility = "hidden";
      tooltip.hidden = true;
    };
    root.append(
      ring,
      s("rect", {
        class: "hit",
        x: margin.left,
        y: margin.top,
        width: plotWidth,
        height: plotHeight,
        tabindex: 0,
        "aria-label": this._t("weather"),
        onpointermove: (event) => {
          const box = root.getBoundingClientRect();
          let nearest = null;
          let distance = 24 * 24;
          points.forEach((point, index) => {
            const gap = (x(point.temperature) - (event.clientX - box.left)) ** 2 + (y(point.energy) - (event.clientY - box.top)) ** 2;
            if (gap < distance) {
              distance = gap;
              nearest = index;
            }
          });
          if (nearest === null) {
            hide();
            return;
          }
          focused = order.indexOf(nearest);
          show(nearest);
        },
        onpointerleave: hide,
        onfocus: () => show(order[focused]),
        onblur: hide,
        onkeydown: (event) => {
          if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
          event.preventDefault();
          focused = Math.max(0, Math.min(order.length - 1, focused + (event.key === "ArrowLeft" ? -1 : 1)));
          show(order[focused]);
        },
      }),
    );
    container.replaceChildren(root, tooltip);
  }

  // Calendar and expensive days ---------------------------------------------------

  _renderCalendar() {
    const days = this._insights.days;
    const tempo = days.some((day) => day.color);
    const names = COLORS[this._language];
    const legend = tempo
      ? h(
          "ul",
          { class: "legend" },
          ["blue", "white", "red"].map((color) => h("li", {}, h("span", { class: "swatch", style: { background: DAY_FILLS[color] } }), names[color])),
        )
      : h(
          "ul",
          { class: "legend" },
          h(
            "li",
            {},
            this._t("cheaper"),
            h(
              "span",
              { class: "scale" },
              [30, 53, 77, 100].map((step) => h("span", { class: "swatch", style: { background: costFill(step) } })),
            ),
            this._t("dearer"),
          ),
        );
    this._calendarChart = h("div", { class: "scroll" });
    this._calendarDetail = h("div", { class: "day-detail", "aria-live": "polite" });
    return this._card(this._t(tempo ? "calendarTempo" : "calendar"), [this._calendarChart, this._calendarDetail], { tools: legend });
  }

  // One square per day, a column per week from Monday to Sunday: the Tempo color
  // of the day, or its cost in shades of violet. Picking a day describes it
  // under the grid.
  _drawCalendar(container, detail, days) {
    const names = COLORS[this._language];
    const tempo = days.some((day) => day.color);
    const byDate = new Map(days.map((day) => [day.date, day]));
    const first = dayTime(days[0].date);
    const last = dayTime(days[days.length - 1].date);
    // Monday of the first week.
    const origin = first - ((new Date(first).getUTCDay() + 6) % 7) * DAY_MS;
    const weeks = Math.floor((last - origin) / (7 * DAY_MS)) + 1;
    const left = 30;
    const top = 16;
    // Squares big enough to tap, bigger over a few weeks.
    const pitch = Math.max(10, Math.min(26, Math.floor(((container.clientWidth || 320) - left) / weeks)));
    const size = pitch - 2;
    const costs = days.map((day) => day.cost);
    const cheapest = Math.min(...costs);
    const spread = Math.max(...costs) - cheapest || 1;
    const fill = (day) => (tempo ? DAY_FILLS[day.color] || "var(--ec-axis)" : costFill(30 + 70 * ((day.cost - cheapest) / spread)));
    const place = (time) => {
      const offset = Math.round((time - origin) / DAY_MS);
      return { x: left + Math.floor(offset / 7) * pitch, y: top + (offset % 7) * pitch };
    };
    const root = s("svg", { class: "calendar", width: left + weeks * pitch, height: top + 7 * pitch, tabindex: 0, role: "application", "aria-label": this._t("calendarKeys") });
    [0, 2, 4].forEach((weekday) => {
      const label = new Intl.DateTimeFormat(this._locale, { weekday: "short", timeZone: "UTC" }).format(origin + weekday * DAY_MS);
      root.append(s("text", { x: left - 6, y: top + weekday * pitch + size / 2, "text-anchor": "end", "dominant-baseline": "middle" }, label));
    });
    // A month label too close to the one before is left out.
    let month = null;
    let labelEnd = -Infinity;
    for (const day of days) {
      if (day.date.slice(0, 7) === month) continue;
      month = day.date.slice(0, 7);
      const label = this._dayLabel(day.date, { month: "short" });
      const { x } = place(dayTime(day.date));
      if (x >= labelEnd + 4) {
        root.append(s("text", { x, y: 10 }, label));
        labelEnd = x + label.length * 6;
      }
    }
    const outline = s("rect", { width: size + 3, height: size + 3, rx: 3, style: { fill: "none", stroke: "var(--ec-text)", "stroke-width": "2px", "pointer-events": "none" } });
    const select = (date) => {
      const day = byDate.get(date);
      this._calendarDay = date;
      const { x, y } = place(dayTime(date));
      outline.setAttribute("x", x - 1.5);
      outline.setAttribute("y", y - 1.5);
      const label = this._dayLabel(date, { weekday: "long", day: "numeric", month: "long" });
      detail.replaceChildren(
        h(
          "strong",
          {},
          h("span", { class: "swatch", style: { background: fill(day) } }),
          [capitalize(label, this._locale), day.color ? names[day.color].toLowerCase() : null].filter(Boolean).join(" · "),
        ),
        h("span", {}, this._kwh(day.energy)),
        h("span", {}, this._money(day.cost)),
        day.temperature !== null ? h("span", { class: "sub" }, this._degrees(day.temperature)) : null,
      );
      // Keep the day in view when the grid scrolls.
      if (container.scrollWidth > container.clientWidth) {
        container.scrollLeft = Math.max(0, x - container.clientWidth / 2);
      }
    };
    // Every day of the weeks shown: a square, or an outline without data.
    for (let time = origin; time < origin + weeks * 7 * DAY_MS; time += DAY_MS) {
      const date = dayString(time);
      const day = byDate.get(date);
      const { x, y } = place(time);
      root.append(
        day
          ? s("rect", { class: "cell", x, y, width: size, height: size, rx: 2, style: { fill: fill(day) }, onclick: () => select(date) })
          : s("rect", { class: "empty", x: x + 0.5, y: y + 0.5, width: size - 1, height: size - 1, rx: 2 }),
      );
    }
    root.append(outline);
    root.addEventListener("keydown", (event) => {
      const moves = { ArrowLeft: -7, ArrowRight: 7, ArrowUp: -1, ArrowDown: 1 };
      let target = null;
      if (event.key in moves) {
        // The nearest day with data that way.
        const step = moves[event.key] * DAY_MS;
        for (let time = dayTime(this._calendarDay) + step; time >= first && time <= last; time += step) {
          if (byDate.has(dayString(time))) {
            target = dayString(time);
            break;
          }
        }
      } else if (event.key === "Home" || event.key === "End") {
        target = days[event.key === "Home" ? 0 : days.length - 1].date;
      } else {
        return;
      }
      event.preventDefault();
      if (target) select(target);
    });
    container.replaceChildren(root);
    select(byDate.has(this._calendarDay) ? this._calendarDay : days[days.length - 1].date);
  }

  _renderTopDays() {
    const days = this._insights.days;
    const names = COLORS[this._language];
    const weather = days.some((day) => day.temperature !== null);
    const top = [...days].sort((first, second) => second.cost - first.cost).slice(0, 5);
    return this._card(
      this._t("topDays"),
      h(
        "div",
        { class: "table-wrap" },
        h(
          "table",
          {},
          h("thead", {}, h("tr", {}, h("th", {}, this._t("day")), h("th", {}, "kWh"), weather ? h("th", {}, "°C") : null, h("th", {}, this._t("cost")))),
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
                  day.color ? h("span", { class: "swatch", role: "img", "aria-label": names[day.color], title: names[day.color], style: { background: DAY_FILLS[day.color] } }) : null,
                  capitalize(this._dayLabel(day.date, { weekday: "short", day: "numeric", month: "short" }), this._locale),
                ),
                h("td", {}, this._number(day.energy, 1)),
                weather ? h("td", { class: "sub" }, day.temperature !== null ? this._number(day.temperature, 1) : "—") : null,
                h("td", {}, h("strong", {}, this._money(day.cost))),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // Tranches -------------------------------------------------------------------

  // Where the money goes: the share of the kWh of each tranche against its share
  // of the euros, for the one contract in force over the period.
  _renderSpend() {
    const inForce = this._contractsInForce();
    if (inForce.length !== 1) return null;
    const names = TRANCHES[this._language];
    const tranches = Object.entries(inForce[0].tranches).filter(([, item]) => item.energy > 0);
    const energy = tranches.reduce((sum, [, item]) => sum + item.energy, 0);
    const cost = tranches.reduce((sum, [, item]) => sum + item.cost, 0);
    if (tranches.length < 2 || !(cost > 0)) return null;
    const share = (value) => this._share(value, value < 0.1 ? 1 : 0);
    // The tranche whose euros weigh the most against its kWh: the dearest.
    const [dearest, item] = tranches.reduce((best, entry) => (entry[1].cost / entry[1].energy > best[1].cost / best[1].energy ? entry : best));
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
            "aria-label": `${label}, ${tranches.map(([tranche, value]) => `${names[tranche] || tranche} ${share(value[key] / total)}`).join(", ")}`,
          },
          tranches
            .filter(([, value]) => value[key] > 0)
            .map(([tranche, value]) => {
              const part = value[key] / total;
              const [fill, ink] = TRANCHE_FILLS[tranche] || ["#898781", "#ffffff"];
              return h(
                "div",
                { class: "segment", title: `${names[tranche] || tranche} · ${share(part)}`, style: { "flex-grow": String(value[key]), "flex-basis": "0", background: fill, color: ink } },
                part >= 0.3 ? `${names[tranche] || tranche} ${this._share(part)}` : part >= 0.09 ? this._share(part) : "",
              );
            }),
        ),
      );
    const table = h(
      "div",
      { class: "table-wrap wrap-head" },
      h(
        "table",
        {},
        h(
          "thead",
          {},
          h(
            "tr",
            {},
            [this._t("tranche"), "kWh", this._t("energyShare"), this._t("cost"), this._t("costShare"), this._t("averagePaid")].map((label) => h("th", {}, label)),
          ),
        ),
        h(
          "tbody",
          {},
          tranches.map(([tranche, value]) =>
            h(
              "tr",
              {},
              h("td", {}, h("span", { class: "swatch", style: { background: (TRANCHE_FILLS[tranche] || ["#898781"])[0] } }), names[tranche] || tranche),
              h("td", {}, this._number(value.energy, value.energy < 100 ? 1 : 0)),
              h("td", {}, share(value.energy / energy)),
              h("td", {}, this._money(value.cost)),
              h("td", {}, share(value.cost / cost)),
              h("td", {}, this._average(value.cost / value.energy)),
            ),
          ),
        ),
      ),
    );
    return this._card(
      this._t("spend"),
      [
        this._lead(share(item.cost / cost), this._t("spendLead", { tranche: names[dearest] || dearest, energy: share(item.energy / energy) })),
        this._views.tranches === "chart" ? [bar("energy", energy, "kWh"), bar("cost", cost, "€")] : table,
      ],
      { tools: this._toggle("tranches") },
    );
  }

  // Comparison ----------------------------------------------------------------

  // Every contract on the period's consumption: a ranking led by its verdict,
  // the bill of the one chosen, and how the gap with it built up.
  _renderCompare() {
    const contracts = [...this._data.contracts].sort((first, second) => first.total_cost - second.total_cost);
    const actual = this._data.actual;
    const inForce = this._contractsInForce();
    const mine = inForce.length === 1 ? inForce[0].id : null;
    // Only contracts waiting for their prices: nothing to compare yet.
    if (!contracts.length) return [this._renderRanking(contracts, actual, mine)];
    if (!contracts.some((contract) => contract.id === this._billContract)) {
      // The cheapest other contract is the first one worth a look.
      this._billContract = (contracts.find((contract) => contract.id !== mine) || contracts[0]).id;
    }
    this._ensureBill();
    return [
      this._renderRanking(contracts, actual, mine),
      this._renderBill(),
      actual && this._billContract !== mine ? this._renderGap() : null,
    ];
  }

  // Who comes first, and by how much.
  _verdict(contracts, actual, mine) {
    const best = contracts[0];
    if (!best) return null;
    if (!actual) return this._lead(best.name, contracts.length > 1 ? this._t("isCheapest") : null);
    if (actual.total_cost - best.total_cost >= 0.5) {
      const saving = actual.total_cost - best.total_cost;
      return this._lead(best.name, this._t("wouldSave", { amount: this._money(saving, 0), change: this._percent(-saving / actual.total_cost) }));
    }
    const name = mine && this._data.contracts.find((contract) => contract.id === mine).name;
    const next = contracts.find((contract) => contract.id !== mine && contract.total_cost - actual.total_cost >= 0.5);
    if (!name) return this._lead(this._t("verdictActual"));
    return this._lead(name, next ? this._t("cheapestBy", { amount: this._money(next.total_cost - actual.total_cost, 0), name: next.name }) : this._t("isCheapest"));
  }

  _renderRanking(contracts, actual, mine) {
    const known = Object.fromEntries(this._entry.contracts.map((contract) => [contract.id, contract]));
    const most = Math.max(...contracts.map((contract) => contract.total_cost), 0.01);
    const signed = new Intl.NumberFormat(this._locale, {
      style: "currency",
      currency: (this._hass.config && this._hass.config.currency) || "EUR",
      maximumFractionDigits: 0,
      signDisplay: "exceptZero",
    });
    const select = (id) => {
      if (this._billContract === id) return;
      this._billContract = id;
      this._renderContent();
    };
    const rows = contracts.map((contract, index) => {
      const info = known[contract.id] || {};
      const kind = KINDS[this._language][contract.kind] || contract.kind;
      // Each fact stays on one line; the line breaks between them.
      const facts = (
        contract.id === mine
          ? [this._t("yourContract")]
          : [kind !== contract.name ? kind : null, ...(info.off_peak || []).map((range) => range.replace("-", "–")), info.kva ? `${info.kva} kVA` : null].filter(Boolean)
      ).flatMap((fact, position) => [position ? " · " : null, h("span", { class: "fact" }, fact)]);
      const difference = actual ? contract.total_cost - actual.total_cost : null;
      const sub = difference === null || Math.abs(difference) < 0.5 ? "" : `${signed.format(difference)} · ${this._percent(difference / actual.total_cost)}`;
      return h(
        "button",
        { class: "rank", "aria-pressed": String(contract.id === this._billContract), onclick: () => select(contract.id) },
        h("span", { class: "position" }, String(index + 1)),
        h("span", { class: "who" }, h("span", { class: "name" }, contract.name), facts.length ? h("span", { class: "sub" }, facts) : null),
        h("span", { class: "bars", "aria-hidden": "true" }, h("span", { class: contract.id === mine ? "bar mine" : "bar", style: { width: `${(Math.max(0, contract.total_cost) / most) * 100}%` } })),
        h("span", { class: "total" }, h("strong", {}, this._money(contract.total_cost, 0)), h("span", { class: "sub" }, sub)),
      );
    });
    const yours = mine && contracts.find((contract) => contract.id === mine);
    return this._card(this._t("ranking"), [this._verdict(contracts, actual, mine), h("div", { class: "ranking" }, rows, this._pendingRanks())], {
      info: [
        this._t("rankingInfo"),
        contracts.length > 1 ? this._t("rankingChoose") : null,
        yours && yours.energy ? this._t("mineAllIn", { name: yours.name, price: this._average(yours.total_cost / yours.energy) }) : null,
      ],
    });
  }

  // The contracts not compared yet, and why: one priced by hand waits for its
  // prices, which the integration's page adds.
  _pendingRanks() {
    return this._entry.contracts
      .filter((contract) => contract.costed === false)
      .map((contract) => {
        const waiting = contract.waiting;
        const day = waiting ? this._dayLabel(waiting.day, { day: "numeric", month: "long", year: "numeric" }) : null;
        let why = this._t("notCompared");
        if (!contract.official && !contract.prices.length) {
          why = this._t("waitingPrices");
        } else if (waiting) {
          why = this._t(waiting.reason === "color" ? "waitingColor" : "waitingPrice", { day });
        }
        return h(
          "div",
          { class: "rank pending" },
          h("span", { class: "position" }, "–"),
          h("span", { class: "who" }, h("span", { class: "name" }, contract.name), h("span", { class: "sub" }, why)),
          contract.official
            ? null
            : h("a", { class: "cta", href: `/config/integrations/integration/${DOMAIN}` }, icon(ICONS.plus), this._t("addPrices")),
        );
      });
  }

  // The chosen contract's bill is asked for as soon as it is shown.
  _ensureBill() {
    const key = `${this._billContract}|${this._request.start}|${this._request.end}`;
    if (this._billKey === key && (this._bill || this._billBusy || this._billError)) return;
    this._billKey = key;
    this._bill = null;
    this._billError = null;
    this._billOpen = {};
    this._computeBill();
  }

  async _computeBill() {
    const count = ++this._billCount;
    this._billBusy = true;
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
    if (this._tab === "compare") this._renderContent();
  }

  // The bill with its verdict first, then each price period, folded.
  _renderBill() {
    const contract = this._data.contracts.find((item) => item.id === this._billContract);
    const title = `${this._t("tabBill")} · ${contract ? contract.name : ""}`;
    if (this._billError) {
      return this._errorCard(title, this._t("loadFailed", { error: this._billError }), () => {
        this._billKey = null;
        this._renderContent();
      });
    }
    const bill = this._bill;
    if (!bill) return this._loadingCard();
    const names = TRANCHES[this._language];
    let verdict = null;
    if (bill.actual !== null) {
      const signed = new Intl.NumberFormat(this._locale, {
        style: "currency",
        currency: (this._hass.config && this._hass.config.currency) || "EUR",
        minimumFractionDigits: 2,
        signDisplay: "exceptZero",
      });
      verdict = Math.abs(bill.difference) > 0.005 ? this._t("billVsActual", { amount: signed.format(bill.difference) }) : this._t("same");
    }
    // The first period is open unless the user chose otherwise.
    const open = (index) => this._billOpen[index] ?? index === 0;
    const prices = (this._entry.contracts.find((item) => item.id === bill.contract.id) || {}).prices || [];
    // The prices of a period date from the change of tariff, before the period.
    const since = (day) => (prices.find((period) => period.start <= day && (!period.end || period.end >= day)) || { start: day }).start;
    const periods = bill.periods.map((period, index) => {
      const start = period.start.slice(0, 10);
      const last = lastDayOf(period.end);
      const days = Math.round((dayTime(last) - dayTime(start)) / DAY_MS) + 1;
      const total = period.subscription + period.lines.reduce((sum, line) => sum + line.cost, 0);
      const expanded = open(index);
      const button = h(
        "button",
        {
          class: "bill-period",
          "aria-expanded": String(expanded),
          onclick: () => {
            this._billOpen[index] = !expanded;
            this._renderContent();
          },
        },
        icon(ICONS.right),
        h(
          "span",
          { class: "what" },
          h("span", {}, this._t("range", { start: this._dayLabel(start), end: this._dayLabel(last) })),
          h("span", { class: "sub" }, this._t("pricesOf", { date: this._dayLabel(since(start)) })),
        ),
        h("span", { class: "num" }, this._money(total)),
      );
      if (!expanded) return [button];
      const table = h(
        "div",
        { class: "table-wrap" },
        h(
          "table",
          {},
          h("thead", {}, h("tr", {}, h("th", {}), h("th", {}, this._t("quantity")), h("th", {}, this._t("price")), h("th", {}, this._t("amount")))),
          h(
            "tbody",
            {},
            period.lines
              .filter((line) => line.energy > 0)
              .map((line) =>
                h(
                  "tr",
                  {},
                  h("td", {}, h("span", { class: "swatch", style: { background: (TRANCHE_FILLS[line.tranche] || ["#898781"])[0] } }), names[line.tranche] || line.tranche),
                  h("td", {}, this._kwh(line.energy)),
                  h("td", {}, `${this._price(line.price)}/kWh`),
                  h("td", {}, this._money(line.cost)),
                ),
              ),
            h(
              "tr",
              {},
              h("td", {}, this._t("subscription")),
              h("td", {}, this._t("days", { count: days })),
              h("td", {}, this._t("subscriptionYear", { amount: this._money(period.fixed_per_year) })),
              h("td", {}, this._money(period.subscription)),
            ),
          ),
        ),
      );
      return [button, table];
    });
    return this._card(
      title,
      [
        this._lead(this._money(bill.total), verdict),
        h("div", { class: "bill-periods" }, periods.flat()),
        h(
          "div",
          { class: "bill-sum" },
          h("span", {}, `${this._t("consumption")} `, h("strong", {}, this._money(bill.consumption))),
          h("span", {}, `${this._t("subscription")} `, h("strong", {}, this._money(bill.subscription))),
        ),
      ],
      {
        info: [
          [this._t("billInfo", { name: contract ? contract.name : "" }), bill.actual !== null ? this._t("billActual", { actual: this._money(bill.actual) }) : null].filter(Boolean).join(" "),
          this._t("billPeriodsInfo"),
        ],
      },
    );
  }

  // How the gap between the chosen contract and what was paid built up.
  _renderGap() {
    const contract = this._data.contracts.find((item) => item.id === this._billContract);
    if (!contract) return null;
    const gap = this._gap(contract.id);
    const last = gap.values[gap.values.length - 1] ?? 0;
    const day = this._dayLabel(this._data.start.slice(0, 10), { day: "numeric", month: "long" });
    const mine = this._mineName();
    this._cumulativeChart = h("div", { class: "chart" });
    let lead;
    if (last >= 0) {
      lead = this._lead(this._money(last, 0), mine ? this._t("gapSavedWith", { mine, day }) : this._t("gapSavedSince", { day }));
    } else {
      lead = this._lead(this._money(-last, 0), this._t("gapLostLead", { name: contract.name, day }));
    }
    const names = { mine: mine || this._t("yourContract"), name: contract.name };
    return this._card(this._t("gapWith", { name: contract.name }), [lead, this._cumulativeChart], {
      info: [this._t("gapInfo", names), this._t("gapNote", names)],
      tools: this._toggle("cumulative"),
    });
  }

  // The name of the one contract in force over the period, if one alone was.
  _mineName() {
    const inForce = this._contractsInForce();
    return inForce.length === 1 ? inForce[0].name : null;
  }

}

if (!customElements.get("electricity-contracts-panel")) {
  customElements.define("electricity-contracts-panel", ElectricityContractsPanel);
}
