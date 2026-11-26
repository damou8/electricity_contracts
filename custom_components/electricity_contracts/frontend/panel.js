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
    tabHeating: "Heating",
    heating: "Heating",
    hotWater: "Hot water",
    electricity: "Electricity",
    heatingCost: "Heating cost",
    atContractPrices: "at your contract's prices, excluding subscription",
    atGasPrice: "at the gas contract's prices, subscription included",
    noGasPrice: "add a gas contract for euros",
    partlyPriced: "some hours have no price yet",
    fromTheWeather: "from the consumption on cold days",
    heatingShareLabel: "Share of the home",
    ofTheElectricity: "of the electricity consumption",
    ofHomeEnergy: "of the home's energy",
    perDegreeColder: "Per degree colder",
    heatingTile: "{share} {of} · {energy}",
    heatingByDay: "Heating by day",
    heatingByMonth: "Heating by month",
    heatingByDayInfo: "What the heating used each day, each hour at the price of its tranche. Below, the average outdoor temperature of each day.",
    heatingBeforeInfo: "Before your heating statistics, from {start} to {end}, the heating is estimated from the Linky and the outdoor temperature, in kWh only. It's hatched.",
    heatingNoWeather: "From {start} to {end}, there's no outdoor temperature to estimate the heating from the Linky.",
    heatingEstimated: "Estimated",
    measuredOnly: "measured days only",
    estimatedFromLinky: "estimated from the Linky",
    ofTheElectricityMeasured: "of the electricity consumption, measured days only",
    heatingMissing: "{count} days without an outdoor temperature or a Linky reading aren't counted.",
    heatingBeforeAll: "Your heating statistics start on {date}. Before, the heating is estimated from how much the whole consumption rises on cold days.",
    ofWhichEstimated: "of which {energy} estimated",
    heatingByDayGasInfo: "What the heating used each day, at the price of the gas contract in force that day, with its share of the subscription. Below, the average outdoor temperature of each day.",
    whereHeatingGoes: "Where the heating goes",
    byHeater: "By heater",
    byTranche: "By tranche",
    whereHeatingInfo: "Your heating statistics added up hour by hour, each hour at the price of its tranche. Days known only by their total count in kWh, without a price.",
    homeEnergy: "The home's energy",
    homeEnergyInfo: "What the home spent on energy over the period, excluding the subscriptions: gas for the heating and the hot water, and electricity.",
    homeEnergyKwh: "Without a gas contract, in kWh.",
    heatingProfile: "Heating, typical day",
    heatingProfileInfo: "What the heating uses at each hour of the day, on average over the {days} days with hourly values.",
    heatingWeatherInfo: "Each dot is a day with its outdoor temperature and what the heating used. Below {base}, it uses on average {slope} more a day per degree colder, {cost} at the average price of your heating.",
    estimatedHeatingInfo: "Without heating statistics, the heating is estimated from the whole consumption: how much it rises on cold days.",
    waterEstimatedInfo: "Your heating statistics include the hot water. It is estimated each day as what they use on a day without heating, {energy}. That is the median of the days at {base} or more outside over the last 12 months.",
    waterMeasuredInfo: "The hot water is your water heater's statistic.",
    simulator: "Simulate a setting",
    simOutdoor: "Outdoor temperature",
    simIndoor: "Indoor temperature",
    simPeriodMean: "period average: {value}",
    simYourIndoor: "your thermometers: {value}",
    simHeatPerDay: "of heating a day",
    simNoIndoor: "Choose one or several indoor thermometers in the heating options to simulate a setting.",
    simNoIndoorData: "Your indoor thermometers recorded nothing over this period.",
    simFewDays: "Not enough heating days over this period to simulate a setting.",
    simPerDay: "A day",
    simMonth: "30 days",
    simDay: "{color} day",
    simDelta: "{cost} a day compared with {temperature} ({energy}).",
    simDeltaEnergy: "{energy} a day compared with {temperature}.",
    simCurrent: "Your current temperature.",
    simInfo: "The simulator extends the line of the Weather card: each degree warmer inside counts as a degree colder outside. It starts from {indoor}, the average of your thermometers over the period.",
    simInfoPrices: "The kWh are split like {source}: {share} in off-peak hours, at current prices, excluding the subscription.",
    simSourceHeating: "your heating's",
    simSourceHome: "the home's consumption",
    simInfoRange: "The line was drawn between {low} and {high} outside; beyond, it is extended.",
    heatingNoData: "No heating recorded over this period.",
    dpeTitle: "Estimated energy label",
    dpeClass: "Class {letter}",
    dpeEnergy: "Energy, kWh/m²/year",
    dpeClimate: "Climate, kg CO₂/m²/year",
    dpeRange: "{from} to {to}",
    dpeUse: "Use",
    dpeFinal: "Final energy",
    dpePrimary: "Primary energy",
    dpeTotal: "Total",
    dpeInfoPeriod: "The label counts what the heating, the hot water and the auxiliaries (ventilation, pumps) used from {start} to {end}, divided by the living area. Lighting and appliances are not part of it.",
    dpeInfoFactors: "Primary energy: electricity × the coefficient below, gas × 1. Climate: electricity 0.079 kg CO₂/kWh for heating, 0.065 for hot water and 0.064 for the auxiliaries, gas 0.227.",
    dpeInfoClass: "The class shown is the worse of the two labels.",
    dpeConventionalMeasured: "The DPE heats the home to 19 °C by day and 16 °C at night. Your thermometers measured {indoor} on average on heating days: the heating counts {after} instead of {before}.",
    dpeConventionalSetting: "The DPE heats the home to 19 °C by day and 16 °C at night. With your setpoint, set below, the heating counts {after} instead of {before}.",
    dpeConventionalSame: "The DPE heats the home to 19 °C by day and 16 °C at night, like your setpoint set below: the heating counts as it is.",
    dpeConventionalNone: "The DPE heats the home to 19 °C by day and 16 °C at night. Here the heating counts as it is: it takes an outdoor temperature and enough heating days to know what a degree more costs.",
    dpeSetpoint: "Heating temperature by day",
    dpeSetback: "Lowered at night, 22:00 to 6:00",
    dpeInfoNotOfficial: "This is not a real DPE: an assessor rates the home itself (insulation, windows, heating system), not what you used.",
    dpePartial: "Your data starts on {start}: the label only covers {days} days instead of a year.",
    dpeNoWeather: "The label only covers {days} days, from {start}. Before that, there's no outdoor temperature to estimate the heating from the Linky.",
    dpeOpenMeteo: "Turn on Open-Meteo weather in the integration's options to cover the whole year.",
    dpeNoData: "Not enough heating data over the last 12 months to compute a label.",
    dpeSettings: "Settings",
    dpeSurface: "Living area (Carrez law)",
    dpeSurfaceNeeded: "Enter your home's living area to estimate its label.",
    dpeSurfaceNeededAdmin: "An administrator must enter the home's living area to estimate its label.",
    dpeCoefficient: "Electricity coefficient",
    dpeAuxiliaries: "Auxiliaries share",
    dpeWaterShare: "Hot water share",
    dpeWaterUsed: "Used because your hot water is neither measured nor estimated.",
    dpeSave: "Save",
    dpeDefaults: "Default values",
    dpeSaved: "Saved.",
    dpeUnsaved: "Not saved yet.",
    dpeSaveFailed: "The settings could not be saved: {error}",
    dpeReadOnly: "Only an administrator can change these settings.",
    useAuxiliaries: "Auxiliaries",
    useSurface: "Living area",
    shareTag: "estimated share",
    nowLabel: "Now",
    unknownColor: "Color not published yet",
    perKwh: "{price}/kWh",
    seasonTitle: "Season {season}",
    spentUntil: "spent up to {day}",
    previousSeason: "Last season: {total}, of which {toDate} at the same date.",
    howComputed: "How is it computed?",
    budgetPartial: "The data starts after 1 September: the season so far is partial.",
    budgetMethod: "The forecast assumes you will consume like last year on the same dates, at current prices. The red and white days left are placed where you consume the most.",
    budgetNoProjection: "Not enough data a year before to project the rest of the season.",
    spentLegend: "Spent",
    expectedLegend: "Expected",
    temperatureStrip: "Average outdoor temperature",
    temperature: "Temperature",
    weather: "Weather",
    weatherSetup: "Choose an outdoor temperature sensor, or turn on Open-Meteo weather, in the integration's options to compare the consumption with the weather.",
    nowInfo: "The price of a kWh under your contract now and until tomorrow evening, hour by hour, by tranche and Tempo color. Tomorrow's color is unknown until RTE publishes it, around 11:00.",
    tempoLeftInfo: "The red and white days RTE still has to place this season, out of 22 red and 43 white, from September to August.",
    peakByColorInfo: "For each Tempo color, the share of the consumption in peak hours. A red day used mostly off-peak shows the consumption is well shifted.",
    calendarInfo: "Each square is a day of the period. Choose a day to see its consumption and cost.",
    calendarTempoInfo: "Each square is a day of the period, in the Tempo color RTE published. Choose a day to see its consumption and cost.",
    topDaysInfo: "The five days that cost the most over the period, each at the price of its tranches, with the day's average outdoor temperature when there is one.",
    spendInfo: "For each tranche, its share of the kWh against its share of the euros, excluding the subscription. A tranche that weighs more in euros than in kWh is dear: a kWh saved there saves the most.",
    simAbout: "The simulator extends the line of the Weather card to the outdoor and indoor temperatures of your choice, and gives the price of such a day.",
    yourData: "Your data",
    useConsumption: "Consumption",
    useContract: "Contract",
    useChosen: "Chosen contract",
    useColors: "Tempo colors",
    useHeating: "Heating",
    useGasPrice: "Gas price",
    useHotWater: "Hot water",
    useOutdoor: "Outdoor temperature",
    useIndoor: "Indoor temperature",
    useHistory: "History",
    meterTag: "Meter",
    stepHour: "hourly",
    stepDay: "daily",
    rte: "RTE",
    lastYear: "last year",
    notTracked: "not tracked",
    estimatedTag: "estimated",
    missing: "to set",
    hintOutdoor: "With an outdoor temperature, from a sensor or Open-Meteo, in the integration's options, the temperature of each day would show below.",
    hintHeatingStatistics: "With heating statistics, in the heating options, the heating would be measured rather than estimated.",
    hintWaterHeater: "With a water heater tracked on its own, in the heating options, the hot water would be measured.",
    hintGasPrice: "With a gas contract, added on the integration's page, the gas would be counted in euros.",
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
    baseloadNote: "The consumption is read between 3:00 and 5:00, when almost everything is off, and the lowest nights are kept. The yearly cost applies that consumption all year round, at the average price of a kWh, excluding the subscription.",
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
    sensorPrices: "prices read from a sensor",
    since: "since {date}",
    untilDay: "until {date}",
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
    costsFrom: "costs start on {date}",
    fromTo: "{start} to {end}",
    noCosts: "This period has no cost. Before {date}, the Linky gives only one value a day. The price depends on the hour, so these days can't be costed.",
    noData: "No data for this period.",
    preparing: "Preparing the figures… The page updates by itself.",
    ifItLasts: "If this lasts, see the state of the integration.",
    noContract: "Add a contract to the integration to compare it here.",
    noMeter: "Without a meter, this source shows the contract in force, its prices and the Tempo colors, and the heating when its statistics are set. To see costs and comparisons, reconfigure the source with a consumption statistic.",
    loadFailed: "Loading failed: {error}",
    liveFailed: "The price now could not be loaded: {error}",
    insightsFailed: "These figures could not be loaded: {error}",
    retry: "Retry",
    actualCost: "Actual cost",
    costPerMonth: "The cost of each month, subscription included.",
    costPerDay: "The cost of each day, subscription included.",
    energyPerMonth: "The consumption of each month.",
    energyPerDay: "The consumption of each day.",
    pricePerMonth: "The average price of a kWh each month, subscription included.",
    pricePerDay: "The average price of a kWh each day, subscription included.",
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
    waitingSensor: "Not compared yet: its sensor has no price for {day}",
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
    withHeating: "Above {base}, you use about {energy} a day. Below, the heating uses on average {slope} more a day per degree colder.",
    weatherInfo: "Each dot is a day with its outdoor temperature and what you consumed.",
    baseFitted: "Your heating starts below {base}. This temperature is found from your days, between 10 and 20 °C.",
    baseDefault: "Your days don't show the temperature where your heating starts. It is counted below {base}.",
    heatingCurve: "The heating follows a curve. A degree colder costs {mild} where it starts and {cold} on your coldest days.",
    perDegreeBelow: "on average per degree below {base}",
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
    perDayEnergyAverage: "{energy} a day on average",
    perDayAverage: "a day on average",
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
    restOfHome: "Rest of the home",
    wholeHome: "Consumption without the heating detail",
    heatingSplitInfo: "Heating and hot water come from their statistics, at the prices of each hour; the subscription counts in the rest of the home.",
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
    tabHeating: "Chauffage",
    heating: "Chauffage",
    hotWater: "Eau chaude",
    electricity: "Électricité",
    heatingCost: "Coût du chauffage",
    atContractPrices: "aux prix de votre contrat, hors abonnement",
    atGasPrice: "aux prix du contrat de gaz, abonnement compris",
    noGasPrice: "ajoutez un contrat de gaz pour les euros",
    partlyPriced: "des heures n'ont pas encore de prix",
    fromTheWeather: "d'après la consommation des jours froids",
    heatingShareLabel: "Part de la maison",
    ofTheElectricity: "de la consommation d'électricité",
    ofHomeEnergy: "de l'énergie de la maison",
    perDegreeColder: "Par degré de moins",
    heatingTile: "{share} {of} · {energy}",
    heatingByDay: "Chauffage par jour",
    heatingByMonth: "Chauffage par mois",
    heatingByDayInfo: "Ce que le chauffage a consommé chaque jour, chaque heure au prix de sa tranche. Dessous, la température extérieure moyenne de chaque jour.",
    heatingBeforeInfo: "Avant vos statistiques de chauffage, du {start} au {end}, le chauffage est estimé à partir du Linky et de la température extérieure, en kWh seulement. Il est hachuré.",
    heatingNoWeather: "Du {start} au {end}, il manque la température extérieure pour estimer le chauffage à partir du Linky.",
    heatingEstimated: "Estimé",
    measuredOnly: "jours mesurés seulement",
    estimatedFromLinky: "estimés à partir du Linky",
    ofTheElectricityMeasured: "de la consommation d'électricité, jours mesurés seulement",
    heatingMissing: "{count} jours sans température extérieure ou sans relevé du Linky ne sont pas comptés.",
    heatingBeforeAll: "Vos statistiques de chauffage commencent le {date}. Avant, le chauffage est estimé d'après ce que toute la consommation augmente les jours froids.",
    ofWhichEstimated: "dont {energy} estimés",
    heatingByDayGasInfo: "Ce que le chauffage a consommé chaque jour, au prix du contrat de gaz en vigueur ce jour-là, avec sa part de l'abonnement. Dessous, la température extérieure moyenne de chaque jour.",
    whereHeatingGoes: "Où va le chauffage",
    byHeater: "Par radiateur",
    byTranche: "Par tranche",
    whereHeatingInfo: "Vos statistiques de chauffage additionnées heure par heure, chaque heure au prix de sa tranche. Les jours connus seulement par leur total comptent en kWh, sans prix.",
    homeEnergy: "Énergie de la maison",
    homeEnergyInfo: "Ce que la maison a dépensé en énergie sur la période, hors abonnements : le gaz du chauffage et de l'eau chaude, et l'électricité.",
    homeEnergyKwh: "Sans contrat de gaz, en kWh.",
    heatingProfile: "Journée type du chauffage",
    heatingProfileInfo: "Ce que le chauffage consomme à chaque heure de la journée, en moyenne sur les {days} jours connus heure par heure.",
    heatingWeatherInfo: "Chaque point est une journée avec sa température extérieure et ce que le chauffage a consommé. Sous {base}, il consomme en moyenne {slope} de plus par jour et par degré de moins, soit {cost} au prix moyen de votre chauffage.",
    estimatedHeatingInfo: "Sans statistique de chauffage, le chauffage est estimé à partir de toute la consommation : ce qu'elle augmente les jours froids.",
    waterEstimatedInfo: "Vos statistiques de chauffage incluent l'eau chaude. Elle est estimée chaque jour à ce qu'elles consomment un jour sans chauffage, soit {energy}. C'est la médiane des jours à {base} ou plus dehors sur les 12 derniers mois.",
    waterMeasuredInfo: "L'eau chaude est la statistique de votre ballon.",
    simulator: "Simuler un réglage",
    simOutdoor: "Température extérieure",
    simIndoor: "Température intérieure",
    simPeriodMean: "moyenne de la période : {value}",
    simYourIndoor: "vos thermomètres : {value}",
    simHeatPerDay: "de chauffage par jour",
    simNoIndoor: "Choisissez un ou plusieurs thermomètres intérieurs dans les options du chauffage pour simuler un réglage.",
    simNoIndoorData: "Vos thermomètres intérieurs n'ont rien enregistré sur cette période.",
    simFewDays: "Pas assez de jours de chauffage sur cette période pour simuler un réglage.",
    simPerDay: "Par jour",
    simMonth: "30 jours",
    simDay: "Jour {color}",
    simDelta: "{cost} par jour par rapport à {temperature} ({energy}).",
    simDeltaEnergy: "{energy} par jour par rapport à {temperature}.",
    simCurrent: "Votre température actuelle.",
    simInfo: "Le simulateur prolonge la droite de la carte Météo : chaque degré de plus dedans compte comme un degré de moins dehors. Il part de {indoor}, la moyenne de vos thermomètres sur la période.",
    simInfoPrices: "Les kWh sont partagés comme {source} : {share} en heures creuses, aux prix actuels, hors abonnement.",
    simSourceHeating: "ceux de votre chauffage",
    simSourceHome: "la consommation de la maison",
    simInfoRange: "La droite a été tracée entre {low} et {high} dehors ; au-delà, elle est prolongée.",
    heatingNoData: "Aucun chauffage enregistré sur cette période.",
    dpeTitle: "Étiquette DPE estimée",
    dpeClass: "Classe {letter}",
    dpeEnergy: "Énergie, kWh/m²/an",
    dpeClimate: "Climat, kg CO₂/m²/an",
    dpeRange: "{from} à {to}",
    dpeUse: "Usage",
    dpeFinal: "Énergie finale",
    dpePrimary: "Énergie primaire",
    dpeTotal: "Total",
    dpeInfoPeriod: "L'étiquette compte ce que le chauffage, l'eau chaude et les auxiliaires (ventilation, pompes) ont consommé du {start} au {end}, divisé par la surface habitable. L'éclairage et l'électroménager n'en font pas partie.",
    dpeInfoFactors: "Énergie primaire : électricité × le coefficient ci-dessous, gaz × 1. Climat : électricité 0,079 kg CO₂/kWh pour le chauffage, 0,065 pour l'eau chaude et 0,064 pour les auxiliaires, gaz 0,227.",
    dpeInfoClass: "La classe retenue est la plus mauvaise des deux étiquettes.",
    dpeConventionalMeasured: "Le DPE chauffe le logement à 19 °C le jour et 16 °C la nuit. Vos thermomètres ont mesuré {indoor} en moyenne les jours de chauffe : le chauffage compte donc pour {after} au lieu de {before}.",
    dpeConventionalSetting: "Le DPE chauffe le logement à 19 °C le jour et 16 °C la nuit. Avec votre consigne, réglée ci-dessous, le chauffage compte donc pour {after} au lieu de {before}.",
    dpeConventionalSame: "Le DPE chauffe le logement à 19 °C le jour et 16 °C la nuit, comme votre consigne réglée ci-dessous : le chauffage compte tel quel.",
    dpeConventionalNone: "Le DPE chauffe le logement à 19 °C le jour et 16 °C la nuit. Ici, le chauffage compte tel quel : il faut une température extérieure et assez de jours de chauffe pour savoir ce que coûte un degré de plus.",
    dpeSetpoint: "Température de chauffage le jour",
    dpeSetback: "Baisse la nuit, de 22 h à 6 h",
    dpeInfoNotOfficial: "Ce n'est pas un vrai DPE : un diagnostiqueur calcule l'étiquette d'après le logement lui-même (isolation, fenêtres, système de chauffage), pas d'après ce que vous avez consommé.",
    dpePartial: "Vos données commencent le {start} : l'étiquette ne couvre que {days} jours au lieu d'une année.",
    dpeNoWeather: "L'étiquette ne couvre que {days} jours, à partir du {start}. Avant, il manque la température extérieure pour estimer le chauffage à partir du Linky.",
    dpeOpenMeteo: "Activez la météo Open-Meteo dans les options de l'intégration pour couvrir toute l'année.",
    dpeNoData: "Pas assez de données de chauffage sur les 12 derniers mois pour calculer une étiquette.",
    dpeSettings: "Réglages",
    dpeSurface: "Surface habitable (loi Carrez)",
    dpeSurfaceNeeded: "Indiquez la surface habitable de votre logement pour estimer son étiquette.",
    dpeSurfaceNeededAdmin: "Un administrateur doit indiquer la surface habitable du logement pour estimer son étiquette.",
    dpeCoefficient: "Coefficient de l'électricité",
    dpeAuxiliaries: "Part des auxiliaires",
    dpeWaterShare: "Part de l'eau chaude",
    dpeWaterUsed: "Utilisée, car votre eau chaude n'est ni mesurée ni estimée.",
    dpeSave: "Enregistrer",
    dpeDefaults: "Valeurs par défaut",
    dpeSaved: "Enregistré.",
    dpeUnsaved: "Pas encore enregistré.",
    dpeSaveFailed: "Les réglages n'ont pas pu être enregistrés : {error}",
    dpeReadOnly: "Seul un administrateur peut changer ces réglages.",
    useAuxiliaries: "Auxiliaires",
    useSurface: "Surface habitable",
    shareTag: "part estimée",
    nowLabel: "Maintenant",
    unknownColor: "Couleur pas encore publiée",
    perKwh: "{price}/kWh",
    seasonTitle: "Saison {season}",
    spentUntil: "dépensés jusqu'au {day}",
    previousSeason: "Saison dernière : {total}, dont {toDate} à la même date.",
    howComputed: "Comment c'est calculé ?",
    budgetPartial: "Les données commencent après le 1er septembre : le début de saison est incomplet.",
    budgetMethod: "La prévision suppose que vous consommerez comme l'an dernier aux mêmes dates, aux prix actuels. Les jours rouges et blancs restants sont placés là où vous consommez le plus.",
    budgetNoProjection: "Pas assez de données l'an dernier pour prévoir la fin de la saison.",
    spentLegend: "Dépensé",
    expectedLegend: "Prévu",
    temperatureStrip: "Température extérieure moyenne",
    temperature: "Température",
    weather: "Météo",
    weatherSetup: "Choisissez un capteur de température extérieure, ou activez la météo Open-Meteo, dans les options de l'intégration pour comparer la consommation à la météo.",
    nowInfo: "Le prix du kWh de votre contrat maintenant et jusqu'à demain soir, heure par heure, selon la tranche et la couleur Tempo. La couleur de demain est inconnue jusqu'à sa publication par RTE, vers 11 h.",
    tempoLeftInfo: "Les jours rouges et blancs que RTE doit encore placer cette saison, sur 22 rouges et 43 blancs, de septembre à août.",
    peakByColorInfo: "Pour chaque couleur Tempo, la part de la consommation en heures pleines. Un jour rouge consommé surtout en heures creuses montre que la consommation est bien décalée.",
    calendarInfo: "Chaque carré est un jour de la période. Choisissez un jour pour voir sa consommation et son coût.",
    calendarTempoInfo: "Chaque carré est un jour de la période, dans la couleur Tempo publiée par RTE. Choisissez un jour pour voir sa consommation et son coût.",
    topDaysInfo: "Les cinq jours qui ont coûté le plus sur la période, chacun au prix de ses tranches, avec la température extérieure moyenne du jour quand elle est connue.",
    spendInfo: "Pour chaque tranche, sa part des kWh face à sa part des euros, hors abonnement. Une tranche qui pèse plus en euros qu'en kWh est chère : c'est là qu'un kWh évité rapporte le plus.",
    simAbout: "Le simulateur prolonge la droite de la carte Météo jusqu'à la température extérieure et intérieure de votre choix, et donne le prix d'une telle journée.",
    yourData: "Vos données",
    useConsumption: "Consommation",
    useContract: "Contrat",
    useChosen: "Contrat choisi",
    useColors: "Couleurs Tempo",
    useHeating: "Chauffage",
    useGasPrice: "Prix du gaz",
    useHotWater: "Eau chaude",
    useOutdoor: "Température extérieure",
    useIndoor: "Température intérieure",
    useHistory: "Historique",
    meterTag: "Compteur",
    stepHour: "horaire",
    stepDay: "journalier",
    rte: "RTE",
    lastYear: "l'an dernier",
    notTracked: "non suivi",
    estimatedTag: "estimé",
    missing: "à renseigner",
    hintOutdoor: "Avec une température extérieure, d'un capteur ou d'Open-Meteo, dans les options de l'intégration, la température de chaque jour s'afficherait dessous.",
    hintHeatingStatistics: "Avec des statistiques de chauffage, dans les options du chauffage, le chauffage serait mesuré au lieu d'être estimé.",
    hintWaterHeater: "Avec un ballon d'eau chaude suivi à part, dans les options du chauffage, l'eau chaude serait mesurée.",
    hintGasPrice: "Avec un contrat de gaz, ajouté sur la page de l'intégration, le gaz serait compté en euros.",
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
    baseloadNote: "La consommation est relevée entre 3 h et 5 h, quand presque tout est éteint, et les nuits les plus basses sont retenues. Le coût annuel applique cette consommation toute l'année, au prix moyen du kWh, hors abonnement.",
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
    sensorPrices: "prix lus dans un capteur",
    since: "depuis le {date}",
    untilDay: "jusqu'au {date}",
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
    costsFrom: "les coûts commencent le {date}",
    fromTo: "du {start} au {end}",
    noCosts: "Cette période n'a pas de coût. Avant le {date}, le Linky ne donne qu'une valeur par jour. Le prix dépend de l'heure, donc ces jours ne peuvent pas être chiffrés.",
    noData: "Pas de données sur cette période.",
    preparing: "Préparation des calculs… La page se met à jour toute seule.",
    ifItLasts: "Si cela dure, voyez l'état de l'intégration.",
    noContract: "Ajoutez un contrat à l'intégration pour le comparer ici.",
    noMeter: "Sans compteur, cette source montre le contrat en cours, ses prix et les couleurs Tempo, et le chauffage quand ses statistiques sont renseignées. Pour voir les coûts et les comparaisons, reconfigurez la source avec une statistique de consommation.",
    loadFailed: "Le chargement a échoué : {error}",
    liveFailed: "Le prix en direct n'a pas pu être chargé : {error}",
    insightsFailed: "Ces chiffres n'ont pas pu être chargés : {error}",
    retry: "Réessayer",
    actualCost: "Coût réel",
    costPerMonth: "Le coût de chaque mois, abonnement compris.",
    costPerDay: "Le coût de chaque jour, abonnement compris.",
    energyPerMonth: "La consommation de chaque mois.",
    energyPerDay: "La consommation de chaque jour.",
    pricePerMonth: "Le prix moyen du kWh de chaque mois, abonnement compris.",
    pricePerDay: "Le prix moyen du kWh de chaque jour, abonnement compris.",
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
    waitingSensor: "Pas encore comparé : son capteur n'a pas de prix pour le {day}",
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
    withHeating: "Au-dessus de {base}, vous consommez environ {energy} par jour. En dessous, le chauffage consomme en moyenne {slope} de plus par jour et par degré de moins.",
    weatherInfo: "Chaque point est une journée avec sa température extérieure et ce que vous avez consommé.",
    baseFitted: "Votre chauffage démarre sous {base}. Cette température est tirée de vos journées, entre 10 et 20 °C.",
    baseDefault: "Vos journées ne montrent pas à quelle température votre chauffage démarre. Il est compté sous {base}.",
    heatingCurve: "Le chauffage suit une courbe. Un degré de moins coûte {mild} quand il démarre et {cold} vos jours les plus froids.",
    perDegreeBelow: "en moyenne par degré sous {base}",
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
    perDayEnergyAverage: "{energy} par jour en moyenne",
    perDayAverage: "par jour en moyenne",
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
    restOfHome: "Reste de la maison",
    wholeHome: "Consommation sans le détail du chauffage",
    heatingSplitInfo: "Le chauffage et l'eau chaude viennent de leurs statistiques, aux prix de chaque heure ; l'abonnement compte dans le reste de la maison.",
    verdictActual: "Ce que vous avez payé est le plus bas",
    isCheapest: "est le moins cher",
    cheapestBy: "est le moins cher · {amount} de moins que {name}",
    wouldSave: "aurait coûté {amount} de moins ({change})",
    rankingInfo: "Chaque contrat est appliqué à votre consommation réelle, heure par heure, avec ses prix et son abonnement.",
    rankingChoose: "Choisissez un contrat pour voir sa facture fantôme.",
    mineAllIn: "{name}, votre contrat : {price}/kWh abonnement compris.",
    billInfo: "Ce que vous auriez payé avec {name}, sur la même consommation.",
    billActual: "Votre facture réelle : {actual}.",
    billPeriodsInfo: "Une ligne par période de prix : chacune garde les prix en vigueur à ses dates.",
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
.contract-chips { display: inline-flex; gap: 8px; min-width: 0; max-width: 60%; }
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
  min-width: 0;
}
.contract-chip strong { font-weight: 500; overflow: hidden; text-overflow: ellipsis; }
.contract-chip .kva, .contract-chip svg { flex: none; }
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
.method > * + * { margin-top: 10px; }
.uses h3 { margin: 0 0 4px; font-size: 12px; font-weight: 400; color: var(--ec-text-2); }
.uses dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 6px 12px; align-items: center; margin: 0; }
.uses dt { display: inline-flex; align-items: center; gap: 6px; color: var(--ec-text); }
.uses dt svg { width: 16px; height: 16px; flex: none; fill: var(--ec-text-2); }
.uses dd { display: flex; flex-wrap: wrap; gap: 4px; margin: 0; }
.tag { display: inline-flex; align-items: center; min-height: 24px; box-sizing: border-box; padding: 2px 9px; border: 1px solid transparent; border-radius: 12px; background: color-mix(in srgb, var(--tag) 22%, transparent); color: var(--ec-text); font-size: 12px; line-height: 1.3; }
.tag.estimated { border: 1px dashed var(--tag); background: transparent; }
.uses .use-period { align-self: center; color: var(--ec-text-2); font-size: 12px; }
.tag.missing { border-color: var(--ec-warn); background: transparent; color: var(--ec-warn); }
@media (max-width: 480px) { .uses dl { grid-template-columns: minmax(0, 1fr); gap: 2px; } .uses dd { margin-bottom: 6px; } }
.method p.hint { margin-top: 10px; }
.dpe { display: flex; align-items: center; gap: 24px; }
.dpe-letter { width: 64px; height: 64px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 40px; font-weight: 700; }
.dpe-letter.partial { background: var(--ec-wash); color: var(--ec-muted); border: 2px dashed var(--divider-color, var(--ec-axis)); box-sizing: border-box; }
.dpe-scales { flex: 1; min-width: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
.dpe-scale { display: flex; flex-direction: column; gap: 4px; }
.dpe-scale h3 { margin: 0 0 4px; font-size: 13px; font-weight: 400; color: var(--ec-text-2); }
.dpe-row { display: flex; align-items: center; gap: 6px; height: 22px; }
.dpe-row.current { height: 32px; }
.dpe-bar { height: 100%; box-sizing: border-box; border-radius: 0 14px 14px 0; display: flex; align-items: center; justify-content: space-between; gap: 6px; padding: 0 10px; font-size: 11px; white-space: nowrap; opacity: 0.55; }
.dpe-bar b { font-size: 13px; }
.dpe-row.current .dpe-bar { opacity: 1; box-shadow: 0 0 0 2px var(--ec-text); }
.dpe-row.current .dpe-bar b { font-size: 17px; }
.dpe-value { font-size: 15px; font-weight: 500; white-space: nowrap; font-variant-numeric: tabular-nums; }
@media (max-width: 600px) { .dpe { flex-direction: column; align-items: flex-start; } .dpe-scales { width: 100%; } }
@media (max-width: 420px) { .dpe-scales { grid-template-columns: minmax(0, 1fr); } }
.dpe-use { display: inline-flex; align-items: center; gap: 6px; }
.dpe-dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.dpe-table th:first-child, .dpe-table td:first-child { padding-left: 0; }
.dpe-table th:last-child, .dpe-table td:last-child { padding-right: 0; }
.dpe-table tr.total td { border-bottom: none; font-weight: 500; }
.dpe-settings h3 { margin: 0 0 4px; font-size: 12px; font-weight: 400; color: var(--ec-text-2); }
.dpe-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 16px; max-width: 640px; }
@media (max-width: 480px) { .dpe-fields { grid-template-columns: minmax(0, 1fr); } }
.dpe-field { display: flex; flex-direction: column; gap: 4px; }
.dpe-field .row { display: flex; align-items: center; gap: 6px; }
.dpe-field input { font: inherit; font-size: 14px; color: var(--ec-text); background: var(--ec-surface); border: 1px solid var(--divider-color, var(--ec-axis)); border-radius: 8px; padding: 6px 8px; width: 100%; min-height: 36px; box-sizing: border-box; }
.dpe-field input:disabled { background: transparent; color: var(--ec-muted); }
.dpe-field small { font-size: 12px; }
.dpe-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 10px; }
.toggle.primary { background: var(--primary-color, #009ac7); border-color: var(--primary-color, #009ac7); color: var(--text-primary-color, #ffffff); }
.toggle:disabled { opacity: 0.4; cursor: default; }
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
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); padding: 0; overflow: hidden; }
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
.kpi-link { font: inherit; text-align: left; color: inherit; background: transparent; border: 0; cursor: pointer; }
.kpi-link:hover { background: var(--ec-wash); }
.kpi-link .label::after { content: " ›"; }
.heat-split { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr)); gap: 16px 32px; }
.heat-part { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.heat-part h3 { margin: 0; font-size: 13px; font-weight: 400; color: var(--ec-text-2); }
.heater { display: grid; grid-template-columns: minmax(0, 11em) minmax(0, 1fr) 5em; align-items: center; gap: 12px; font-size: 14px; }
.heater .who { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.heater .track { height: 12px; border-radius: 0 4px 4px 0; overflow: hidden; }
.heater .fill { height: 100%; border-radius: 0 4px 4px 0; background: var(--ec-s2); }
.heater .amount { text-align: right; font-variant-numeric: tabular-nums; }
.sim { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 16px 32px; align-items: start; }
.sim-sliders { display: flex; flex-direction: column; gap: 20px; }
.sim-slider { display: flex; flex-direction: column; gap: 6px; }
.sim-label { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-size: 14px; }
.sim-label strong { font-size: 20px; font-weight: 500; font-variant-numeric: tabular-nums; }
.sim-slider input { width: 100%; min-height: 44px; margin: 0; accent-color: var(--ec-s2); }
.sim-scale { display: flex; justify-content: space-between; gap: 8px; color: var(--ec-text-2); font-size: 12px; }
.sim-delta { margin: 10px 0 0; font-size: 13px; }
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
.swatch.hatched-heating { background: repeating-linear-gradient(135deg, var(--ec-s2) 0 2px, transparent 2px 4px); box-shadow: inset 0 0 0 1px var(--ec-s2); }
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

// The order of the lines of "Your data", the same on every card.
const USE_ORDER = ["consumption", "consumptionDays", "heating", "heatingMixed", "dpeHeating", "water", "dpeWater", "auxiliaries", "surface", "chosen", "contract", "contractToday", "otherContract", "colors", "colorsToday", "gasPrice", "outdoor", "indoor", "history"];

const ICONS = {
  meter: "M7,2V13H10V22L17,10H13L17,2H7Z",
  contract: "M6,2A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2H6M6,4H13V9H18V20H6V4M8,12V14H16V12H8M8,16V18H13V16H8Z",
  compare: "M12,3C10.73,3 9.6,3.8 9.18,5H3V7H4.95L2,14C1.53,16 3,17 5.5,17C8,17 9.56,16 9,14L6.05,7H9.17C9.5,7.85 10.15,8.5 11,8.83V20H2V22H22V20H13V8.82C13.85,8.5 14.5,7.85 14.82,7H17.95L15,14C14.53,16 16,17 18.5,17C21,17 22.56,16 22,14L19.05,7H21V5H14.83C14.4,3.8 13.27,3 12,3M12,5A1,1 0 0,1 13,6A1,1 0 0,1 12,7A1,1 0 0,1 11,6A1,1 0 0,1 12,5M5.5,10.25L7,14H4L5.5,10.25M18.5,10.25L20,14H17L18.5,10.25Z",
  colors: "M17.5,12A1.5,1.5 0 0,1 16,10.5A1.5,1.5 0 0,1 17.5,9A1.5,1.5 0 0,1 19,10.5A1.5,1.5 0 0,1 17.5,12M14.5,8A1.5,1.5 0 0,1 13,6.5A1.5,1.5 0 0,1 14.5,5A1.5,1.5 0 0,1 16,6.5A1.5,1.5 0 0,1 14.5,8M9.5,8A1.5,1.5 0 0,1 8,6.5A1.5,1.5 0 0,1 9.5,5A1.5,1.5 0 0,1 11,6.5A1.5,1.5 0 0,1 9.5,8M6.5,12A1.5,1.5 0 0,1 5,10.5A1.5,1.5 0 0,1 6.5,9A1.5,1.5 0 0,1 8,10.5A1.5,1.5 0 0,1 6.5,12M12,3A9,9 0 0,0 3,12A9,9 0 0,0 12,21A1.5,1.5 0 0,0 13.5,19.5C13.5,19.11 13.35,18.76 13.11,18.5C12.88,18.23 12.73,17.88 12.73,17.5A1.5,1.5 0 0,1 14.23,16H16A5,5 0 0,0 21,11C21,6.58 16.97,3 12,3Z",
  history: "M13.5,8H12V13L16.28,15.54L17,14.33L13.5,12.25V8M13,3A9,9 0 0,0 4,12H1L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3",
  radiator: "M7.95,3L6.53,5.19L7.95,7.4H7.94L5.95,10.5L4.22,9.6L5.64,7.39L4.22,5.19L6.22,2.09L7.95,3M13.95,2.89L12.53,5.1L13.95,7.3L13.94,7.31L11.95,10.4L10.22,9.5L11.64,7.3L10.22,5.1L12.22,2L13.95,2.89M20,2.89L18.56,5.1L20,7.3V7.31L18,10.4L16.25,9.5L17.67,7.3L16.25,5.1L18.25,2L20,2.89M2,22V14A2,2 0 0,1 4,12H20A2,2 0 0,1 22,14V22H20V20H4V22H2M6,14A1,1 0 0,0 5,15V17A1,1 0 0,0 6,18A1,1 0 0,0 7,17V15A1,1 0 0,0 6,14M10,14A1,1 0 0,0 9,15V17A1,1 0 0,0 10,18A1,1 0 0,0 11,17V15A1,1 0 0,0 10,14M14,14A1,1 0 0,0 13,15V17A1,1 0 0,0 14,18A1,1 0 0,0 15,17V15A1,1 0 0,0 14,14M18,14A1,1 0 0,0 17,15V17A1,1 0 0,0 18,18A1,1 0 0,0 19,17V15A1,1 0 0,0 18,14Z",
  fire: "M17.66 11.2C17.43 10.9 17.15 10.64 16.89 10.38C16.22 9.78 15.46 9.35 14.82 8.72C13.33 7.26 13 4.85 13.95 3C13 3.23 12.17 3.75 11.46 4.32C8.87 6.4 7.85 10.07 9.07 13.22C9.11 13.32 9.15 13.42 9.15 13.55C9.15 13.77 9 13.97 8.8 14.05C8.57 14.15 8.33 14.09 8.14 13.93C8.08 13.88 8.04 13.83 8 13.76C6.87 12.33 6.69 10.28 7.45 8.64C5.78 10 4.87 12.3 5 14.47C5.06 14.97 5.12 15.47 5.29 15.97C5.43 16.57 5.7 17.17 6 17.7C7.08 19.43 8.95 20.67 10.96 20.92C13.1 21.19 15.39 20.8 17.03 19.32C18.86 17.66 19.5 15 18.56 12.72L18.43 12.46C18.22 12 17.66 11.2 17.66 11.2M14.5 17.5C14.22 17.74 13.76 18 13.4 18.1C12.28 18.5 11.16 17.94 10.5 17.28C11.69 17 12.4 16.12 12.61 15.23C12.78 14.43 12.46 13.77 12.33 13C12.21 12.26 12.23 11.63 12.5 10.94C12.69 11.32 12.89 11.7 13.13 12C13.9 13 15.11 13.44 15.37 14.8C15.41 14.94 15.43 15.08 15.43 15.23C15.46 16.05 15.1 16.95 14.5 17.5H14.5Z",
  boiler: "M8 2C6.89 2 6 2.89 6 4V16C6 17.11 6.89 18 8 18H9V20H6V22H9C10.11 22 11 21.11 11 20V18H13V20C13 21.11 13.89 22 15 22H18V20H15V18H16C17.11 18 18 17.11 18 16V4C18 2.89 17.11 2 16 2H8M12 4.97A2 2 0 0 1 14 6.97A2 2 0 0 1 12 8.97A2 2 0 0 1 10 6.97A2 2 0 0 1 12 4.97M10 14.5H14V16H10V14.5Z",
  euro: "M15 18.5C12.5 18.5 10.32 17.08 9.24 15H15L16 13H8.58C8.53 12.67 8.5 12.34 8.5 12S8.53 11.33 8.58 11H15L16 9H9.24C10.32 6.92 12.5 5.5 15 5.5C16.61 5.5 18.09 6.09 19.23 7.07L21 5.3C19.41 3.87 17.3 3 15 3C11.08 3 7.76 5.5 6.5 9H3L2 11H6.06C6 11.33 6 11.66 6 12S6 12.67 6.06 13H3L2 15H6.5C7.76 18.5 11.08 21 15 21C17.31 21 19.41 20.13 21 18.7L19.22 16.93C18.09 17.91 16.62 18.5 15 18.5Z",
  thermometer: "M15 13V5A3 3 0 0 0 9 5V13A5 5 0 1 0 15 13M12 4A1 1 0 0 1 13 5V8H11V5A1 1 0 0 1 12 4Z",
  cloud: "M12.74,5.47C15.1,6.5 16.35,9.03 15.92,11.46C17.19,12.56 18,14.19 18,16V16.17C18.31,16.06 18.65,16 19,16A3,3 0 0,1 22,19A3,3 0 0,1 19,22H6A4,4 0 0,1 2,18A4,4 0 0,1 6,14H6.27C5,12.45 4.6,10.24 5.5,8.26C6.72,5.5 9.97,4.24 12.74,5.47M11.93,7.3C10.16,6.5 8.09,7.31 7.31,9.07C6.85,10.09 6.93,11.22 7.41,12.13C8.5,10.83 10.16,10 12,10C12.7,10 13.38,10.12 14,10.34C13.94,9.06 13.18,7.86 11.93,7.3M13.55,3.64C13,3.4 12.45,3.23 11.88,3.12L14.37,1.82L15.27,4.71C14.76,4.29 14.19,3.93 13.55,3.64M6.09,4.44C5.6,4.79 5.17,5.19 4.8,5.63L4.91,2.82L7.87,3.5C7.25,3.71 6.65,4.03 6.09,4.44M18,9.71C17.91,9.12 17.78,8.55 17.59,8L19.97,9.5L17.92,11.73C18.03,11.08 18.05,10.4 18,9.71M3.04,11.3C3.11,11.9 3.24,12.47 3.43,13L1.06,11.5L3.1,9.28C3,9.93 2.97,10.61 3.04,11.3M19,18H16V16A4,4 0 0,0 12,12A4,4 0 0,0 8,16H6A2,2 0 0,0 4,18A2,2 0 0,0 6,20H19A1,1 0 0,0 20,19A1,1 0 0,0 19,18Z",
  indoor: "M19 8C20.11 8 21 8.9 21 10V16.76C21.61 17.31 22 18.11 22 19C22 20.66 20.66 22 19 22C17.34 22 16 20.66 16 19C16 18.11 16.39 17.31 17 16.76V10C17 8.9 17.9 8 19 8M19 9C18.45 9 18 9.45 18 10V11H20V10C20 9.45 19.55 9 19 9M12 5.69L7 10.19V18H14.1L14 19L14.1 20H5V12H2L12 3L16.4 6.96C15.89 7.4 15.5 7.97 15.25 8.61L12 5.69Z",
  left: "M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z",
  right: "M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z",
  down: "M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",
  info: "M11,9H13V7H11M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,17H13V11H11V17Z",
  alert: "M12,2L1,21H23M12,6L19.53,19H4.47M11,10V14H13V10M11,16V18H13V16",
  plus: "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",
  fan: "M12,11A1,1 0 0,0 11,12A1,1 0 0,0 12,13A1,1 0 0,0 13,12A1,1 0 0,0 12,11M12.5,2C17,2 17.11,5.57 14.75,6.75C13.76,7.24 13.32,8.29 13.13,9.22C13.61,9.42 14.03,9.73 14.35,10.13C18.05,8.13 22.03,8.92 22.03,12.5C22.03,17 18.46,17.1 17.28,14.73C16.78,13.74 15.72,13.3 14.79,13.11C14.59,13.59 14.28,14 13.88,14.34C15.87,18.03 15.08,22 11.5,22C7,22 6.91,18.42 9.27,17.24C10.25,16.75 10.69,15.71 10.89,14.79C10.4,14.59 9.97,14.27 9.65,13.87C5.96,15.85 2,15.07 2,11.5C2,7 5.56,6.89 6.74,9.26C7.24,10.25 8.29,10.68 9.22,10.87C9.41,10.39 9.73,9.97 10.14,9.65C8.15,5.96 8.94,2 12.5,2Z",
  area: "M3,3H21V21H3V3M5,5V19H19V5H5M7,7H11V9H9V11H7V7M17,17H13V15H15V13H17V17Z",
};

// The classes of the DPE: the upper bound of A to F, and the colors of A to G
// (background, text).
const DPE_LETTERS = ["A", "B", "C", "D", "E", "F", "G"];
const DPE_SCALES = {
  energy: {
    bounds: [70, 110, 180, 250, 330, 420],
    colors: [["#009c6d", "#1a1a1a"], ["#52b153", "#1a1a1a"], ["#a5cc74", "#1a1a1a"], ["#f4e70f", "#1a1a1a"], ["#f0b40f", "#1a1a1a"], ["#eb8235", "#1a1a1a"], ["#d7221f", "#ffffff"]],
  },
  climate: {
    bounds: [6, 11, 30, 50, 70, 100],
    colors: [["#f6edfd", "#1a1a1a"], ["#e4c7fb", "#1a1a1a"], ["#d5aaf6", "#1a1a1a"], ["#cb95f3", "#1a1a1a"], ["#ba72ef", "#1a1a1a"], ["#a74deb", "#ffffff"], ["#8a19df", "#ffffff"]],
  },
};
// A year of data, below which the label tells the days it covers.
const DPE_YEAR_DAYS = 365;

const MEASURES = { cost: "€", energy: "kWh", price: "€/kWh" };
const ALL_TABS = ["follow", "understand", "heating", "compare"];
const TAB_KEYS = { follow: "tabFollow", understand: "tabUnderstand", heating: "tabHeating", compare: "tabCompare" };
// Past this many days, the heating chart shows months.
const HEATING_MAX_DAYS = 62;
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

// The heating of a day `degrees` under the base of a weather fit: on its curve
// up to the coldest day seen, then straight on at its slope there.
function lineHeating(weather, degrees) {
  if (degrees <= 0) return 0;
  const { linear, square, reach } = weather;
  if (degrees <= reach) return linear * degrees + square * degrees * degrees;
  return linear * reach + square * reach * reach + (linear + 2 * square * reach) * (degrees - reach);
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
    this._views = { time: "chart", cumulative: "chart", tranches: "chart", dpe: "chart" };
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
    this._heating = null;
    this._heatingError = null;
    // The energy label, loaded for the Heating tab by entry and end of period;
    // the settings typed and not saved yet, and what the last save said.
    this._dpe = null;
    this._dpeEntry = null;
    this._dpeKey = null;
    this._dpeError = null;
    this._dpeDraft = null;
    this._dpeStatus = null;
    this._dpeSaving = false;
    // What the heating chart shows, and where the setting simulator stands.
    this._heatingMeasure = "cost";
    this._sim = null;
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

  _money(value, digits = 2, signDisplay = "auto") {
    return new Intl.NumberFormat(this._locale, {
      style: "currency",
      currency: (this._hass.config && this._hass.config.currency) || "EUR",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
      signDisplay,
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

  _bucketLabel(day, long, monthly = this._data.group_by === "month") {
    if (monthly) {
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
    await Promise.all([this._loadStatisticNames(), this._load()]);
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
    // A source without a meter may have no days at all: its window ends today.
    const last = entry.last_day || dayString(Date.now());
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
        const first = entry.energy_first_day || entry.first_day;
        return { start: first && first > start ? first : start, end: last };
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
    const meterless = entry && entry.meter === false;
    if (!entry || (!entry.last_day && !meterless) || !entry.contracts.length) {
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
    let heatingError = null;
    try {
      const request = { entry_id: entry.entry_id, start: window.start, end: window.end };
      const [data, insights, heating] = await Promise.all([
        // Without a meter, nothing is costed: the insights still give Tempo.
        meterless ? { meterless: true } : this._hass.callWS({ type: `${DOMAIN}/compare`, ...request }),
        // The page stands without them: their cards tell what went wrong.
        this._hass.callWS({ type: `${DOMAIN}/insights`, ...request }).catch((error) => {
          insightsError = error.message || String(error);
          return null;
        }),
        entry.heating && entry.last_day
          ? this._hass.callWS({ type: `${DOMAIN}/heating`, ...request }).catch((error) => {
              heatingError = error.message || String(error);
              return null;
            })
          : null,
      ]);
      if (count !== this._loadCount) return;
      if (data && data.series) {
        // The time chart also shows the days only known in total; the other
        // charts compare costs.
        data.energySeries = data.series;
        data.series = data.series.filter((bucket) => !bucket.daily);
      }
      this._request = window;
      this._data = data;
      this._insights = insights;
      this._insightsError = insightsError;
      this._heating = heating;
      this._heatingError = heatingError;
      this._sim = null;
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
        this._renderFilters();
        this._renderContent();
      }
      if (focus) this._tabs.querySelector('[aria-selected="true"]').focus();
    };
    const tabs = this._tabList();
    if (!tabs.includes(this._tab)) this._tab = "follow";
    this._tabs.replaceChildren(
      ...tabs.map((tab, index) =>
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
              select(tabs[(index + step + tabs.length) % tabs.length], true);
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
    if (!entry || !entry.last_day || !entry.contracts.length || (entry.meter === false && this._tab !== "heating")) {
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
    const first = entry.energy_first_day || entry.first_day || entry.last_day;
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
    if (data && (data.start !== data.end || data.daily)) {
      const range = this._energyRange();
      const parts = [this._t("windowDays", { window: this._windowText(range), count: this._days(range) })];
      if (data.daily && this._costed()) parts.push(this._t("costsFrom", { date: this._dayLabel(data.start.slice(0, 10)) }));
      children.push(h("div", { class: "window" }, parts.join(" · ")));
    }
    this._filters.replaceChildren(...children);
  }

  // Whether the period has hours costed.
  _costed() {
    return this._data.start !== this._data.end;
  }

  // The period's days with kWh: the costed hours, and before them the days
  // the Linky only gave in total.
  _energyRange() {
    const data = this._data;
    if (!data.daily) return data;
    const first = `${data.daily.first}T00:00:00`;
    const end = `${addDays(data.daily.last, 1)}T00:00:00`;
    if (!this._costed()) return { start: first, end };
    return { start: data.daily.first < data.start.slice(0, 10) ? first : data.start, end: data.end > end ? data.end : end };
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
  // its body. The notes open under the body: how it is computed, the data it
  // uses ("uses", see _uses) and what more data would bring ("hint").
  // `extra` goes in the method below the notes: a card's settings.
  _card(title, body, { info = [], uses = [], hint = null, tools = null, extra = null, rerender = () => this._renderContent() } = {}) {
    const notes = info.filter(Boolean);
    const rows = uses.filter(Boolean);
    const hints = [hint].flat().filter(Boolean);
    const explained = notes.length > 0 || rows.length > 0 || Boolean(extra);
    const open = explained && Boolean(this._open[title]);
    const button = explained
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
      open
        ? h(
            "div",
            { class: "method" },
            notes.map((note) => h("p", {}, note)),
            extra,
            rows.length
              ? h(
                  "div",
                  { class: "uses" },
                  h("h3", {}, this._t("yourData")),
                  h(
                    "dl",
                    {},
                    rows.map((row) => [
                      h("dt", {}, icon(row.path), row.name),
                      h(
                        "dd",
                        { style: { "--tag": row.hue } },
                        row.values.map((value) => h("span", { class: row.state ? `tag ${row.state}` : "tag" }, value)),
                        row.period ? h("span", { class: "use-period" }, row.period) : null,
                      ),
                    ]),
                  ),
                )
              : null,
            hints.map((note) => h("p", { class: "hint" }, note)),
          )
        : null,
    );
  }

  // "Your data" of a card: one line per input it uses, its icon and name, then
  // where it comes from in tags. Each key gives { path, hue, name, values,
  // state }, state "estimated" or "missing" when so, or null when it doesn't apply.
  _uses(...keys) {
    const rank = (key) => USE_ORDER.indexOf(key);
    return keys
      .filter(Boolean)
      .sort((first, second) => rank(first) - rank(second))
      .flatMap((key) => this._use(key))
      .filter(Boolean);
  }

  _use(key) {
    const entry = this._entry;
    if (!entry) return null;
    const inputs = entry.inputs || {};
    const heating = entry.heating;
    const named = (id) => this._statisticName(id);
    // The step of statistics, hourly or daily, once for those that share it.
    const step = (...steps) => [...new Set(steps.filter(Boolean))].map((value) => this._t(value === "day" ? "stepDay" : "stepHour"));
    const steps = (ids) => step(...ids.map((id) => (inputs.steps || {})[id]));
    // hue: the color of its tags, that of the data in the charts when it has one.
    const row = (path, hue, name, values, state = null) => ({ path, hue, name: this._t(name), values: values.filter(Boolean), state });
    // One line per contract, so their tags don't mix.
    const contracts = (path, list, name = "useContract") => list.map((contract) => row(path, "var(--ec-s1)", name, this._contractFacts(contract)));
    const colors = (list) => (list.some((contract) => contract.kind === "tempo") ? row(ICONS.colors, "var(--ec-s5)", "useColors", ["RTE"]) : null);
    switch (key) {
      case "consumption":
        return entry.meter === false ? null : row(ICONS.meter, "var(--ec-money)", "useConsumption", [inputs.meter === "linky" ? "Linky" : this._t("meterTag"), ...step(inputs.meter_step)]);
      case "consumptionDays": {
        // The days the Linky gave in total, then the hours, each with its dates.
        const daily = this._data && this._data.daily;
        if (entry.meter === false || !daily) return this._use("consumption");
        const name = inputs.meter === "linky" ? "Linky" : this._t("meterTag");
        const span = (start, end) => this._t("fromTo", { start: this._dayLabel(start), end: this._dayLabel(end) });
        // The dates follow the tags, in plain text.
        const dated = (step, start, end) => ({ ...row(ICONS.meter, "var(--ec-money)", "useConsumption", [name, this._t(step)]), period: span(start, end) });
        const rows = [dated("stepDay", daily.first, daily.last)];
        if (this._costed()) rows.push(dated("stepHour", this._data.start.slice(0, 10), lastDayOf(this._data.end)));
        return rows;
      }
      case "contract":
        return contracts(ICONS.contract, this._usedContracts());
      case "contractToday":
        return contracts(ICONS.contract, this._contractsToday());
      case "otherContract":
        // The contract in force, beside a chosen one that isn't it.
        return contracts(ICONS.contract, this._usedContracts().filter((contract) => contract.id !== this._billContract));
      case "chosen":
        return contracts(ICONS.compare, entry.contracts.filter((contract) => contract.id === this._billContract), "useChosen");
      case "colorsToday":
        return colors(this._contractsToday());
      case "colors":
        return colors(this._usedContracts());
      case "history":
        return row(ICONS.history, "var(--ec-money)", "useHistory", [this._t("lastYear")]);
      case "heating": {
        if (!heating) return null;
        const path = heating.gas ? ICONS.fire : ICONS.radiator;
        if (!heating.measured) return row(path, "var(--ec-s2)", "useHeating", [this._t("notTracked"), this._t("estimatedTag")], "estimated");
        return row(path, "var(--ec-s2)", "useHeating", [...(inputs.heating || []).map(named), ...steps(inputs.heating || [])]);
      }
      case "water":
        if (!heating || !heating.with_water) return null;
        return inputs.water
          ? row(ICONS.boiler, "var(--ec-s3)", "useHotWater", [named(inputs.water), ...steps([inputs.water])])
          : row(ICONS.boiler, "var(--ec-s3)", "useHotWater", [this._t("notTracked"), this._t("estimatedTag")], "estimated");
      case "heatingMixed": {
        // The heating tab: measured, and before its statistics the Linky's estimate.
        const before = this._heating && this._heating.before;
        const measured = this._use("heating");
        const days = this._heating.days;
        const end = days.length ? days[days.length - 1].date : null;
        if (!before || !measured || !end) return measured;
        const span = (start, stop) => this._t("fromTo", { start: this._dayLabel(start), end: this._dayLabel(stop) });
        return [
          { ...row(ICONS.radiator, "var(--ec-s2)", "useHeating", ["Linky", this._t("estimatedTag")], "estimated"), period: span(before.start, before.end) },
          { ...measured, period: span(addDays(before.end, 1), end) },
        ];
      }
      case "dpeHeating": {
        // Measured heating, and before its statistics the Linky's estimate.
        const estimated = this._dpe && this._dpe.estimated;
        const measured = this._use("heating");
        if (!estimated || !heating || !heating.measured || !measured) return measured;
        const span = (start, end) => this._t("fromTo", { start: this._dayLabel(start), end: this._dayLabel(end) });
        return [
          { ...row(ICONS.radiator, "var(--ec-s2)", "useHeating", ["Linky", this._t("estimatedTag")], "estimated"), period: span(estimated.start, estimated.end) },
          { ...measured, period: span(addDays(estimated.end, 1), this._dpe.end) },
        ];
      }
      case "dpeWater": {
        const water = this._dpe && this._dpe.uses.find((item) => item.use === "water");
        if (!water) return null;
        if (water.source === "measured" && inputs.water) {
          const measured = row(ICONS.boiler, "var(--ec-s3)", "useHotWater", [named(inputs.water), ...steps([inputs.water])]);
          const estimated = this._dpe.estimated;
          if (!estimated) return measured;
          // Before the heating statistics, the water of a measured day on average.
          const span = (start, end) => this._t("fromTo", { start: this._dayLabel(start), end: this._dayLabel(end) });
          return [
            { ...row(ICONS.boiler, "var(--ec-s3)", "useHotWater", [named(inputs.water), this._t("estimatedTag")], "estimated"), period: span(estimated.start, estimated.end) },
            { ...measured, period: span(addDays(estimated.end, 1), this._dpe.end) },
          ];
        }
        return row(ICONS.boiler, "var(--ec-s3)", "useHotWater", [this._t("notTracked"), this._t(water.source === "share" ? "shareTag" : "estimatedTag")], "estimated");
      }
      case "auxiliaries":
        return row(ICONS.fan, "var(--ec-other)", "useAuxiliaries", [this._t("notTracked"), this._t("shareTag")], "estimated");
      case "surface": {
        if (!this._dpe) return null;
        const surface = this._dpe.settings.surface;
        return row(ICONS.area, "var(--ec-s1)", "useSurface", [`${this._number(surface, Number.isInteger(surface) ? 0 : 1)} m²`]);
      }
      case "gasPrice": {
        if (!heating || !heating.gas) return null;
        const price = this._heating && this._heating.simulator ? this._heating.simulator.gas_price : null;
        return price !== null && price !== undefined
          ? row(ICONS.euro, "var(--ec-s4)", "useGasPrice", [`${this._price(price)}/kWh`])
          : row(ICONS.euro, "var(--ec-s4)", "useGasPrice", [this._t("missing")], "missing");
      }
      case "outdoor":
        if (entry.outdoor === "sensor" && entry.outdoor_fill_until) {
          // Open-Meteo gives the days before the sensor's first one.
          const until = entry.outdoor_fill_until;
          return [
            { ...row(ICONS.cloud, "var(--ec-s6)", "useOutdoor", ["Open-Meteo", ...step("hour")]), period: this._t("untilDay", { date: this._dayLabel(addDays(until, -1)) }) },
            { ...row(ICONS.thermometer, "var(--ec-s6)", "useOutdoor", [named(inputs.outdoor), ...steps([inputs.outdoor])]), period: this._t("since", { date: this._dayLabel(until) }) },
          ];
        }
        if (entry.outdoor === "sensor") return row(ICONS.thermometer, "var(--ec-s6)", "useOutdoor", [named(inputs.outdoor), ...steps([inputs.outdoor])]);
        if (entry.outdoor === "open_meteo") return row(ICONS.cloud, "var(--ec-s6)", "useOutdoor", ["Open-Meteo", ...step("hour")]);
        return row(ICONS.thermometer, "var(--ec-s6)", "useOutdoor", [this._t("missing")], "missing");
      case "indoor": {
        const ids = inputs.indoor || [];
        if (!ids.length) return row(ICONS.indoor, "var(--ec-s8)", "useIndoor", [this._t("missing")], "missing");
        return row(ICONS.indoor, "var(--ec-s8)", "useIndoor", [...ids.map(named), ...steps(ids)]);
      }
      default:
        return null;
    }
  }

  // The contracts a card's figures come from: those in force over the period,
  // or today's when nothing is costed.
  _usedContracts() {
    const entry = this._entry;
    const ids = this._data && !this._data.meterless ? this._contractsInForce().map((contract) => contract.id) : this._contractsToday().map((contract) => contract.id);
    return entry.contracts.filter((contract) => ids.includes(contract.id));
  }

  _contractFacts(contract) {
    return [contract.name, contract.kva ? `${contract.kva} kVA` : null, this._t(this._pricingKey(contract))].filter(Boolean);
  }

  // The name of a statistic: its entity's, or the recorder's for one imported.
  _statisticName(id) {
    const state = this._hass && this._hass.states[id];
    return (state && state.attributes.friendly_name) || (this._statisticNames && this._statisticNames[id]) || id;
  }

  // The recorder's names of the statistics the cards list, for those without
  // an entity (a Gazpar import, for example).
  async _loadStatisticNames() {
    const ids = new Set();
    for (const entry of this._entries || []) {
      const inputs = entry.inputs || {};
      for (const id of [...(inputs.heating || []), inputs.water, inputs.outdoor, ...(inputs.indoor || [])]) {
        if (id && !(this._hass.states[id] || (this._statisticNames && id in this._statisticNames))) ids.add(id);
      }
    }
    if (!ids.size) return;
    try {
      const found = await this._hass.callWS({ type: "recorder/get_statistics_metadata", statistic_ids: [...ids] });
      this._statisticNames = { ...this._statisticNames, ...Object.fromEntries(found.filter((item) => item.name).map((item) => [item.statistic_id, item.name])) };
    } catch (error) {
      // The IDs stand in for the names.
    }
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
    } else if (entry.meter !== false && (!entry.last_day || !this._data || (this._data.start === this._data.end && !this._data.daily))) {
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
    this._heatingDaysChart = null;
    this._heatingProfileChart = null;
    this._heatingWeatherChart = null;
    // The heating tab comes and goes with the source.
    this._renderTabs();
    let cards;
    if (this._tab === "compare") {
      cards = this._renderCompare();
    } else if (this._tab === "heating") {
      cards = this._renderHeatingTab();
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
    if (this._data.meterless) {
      return [h("section", { class: "card message" }, this._t("noMeter"))];
    }
    if (!this._data.actual) {
      return [h("section", { class: "card message" }, this._t("noContractInForce"))];
    }
    // Before the first costed hour, only the kWh.
    if (!this._costed()) return [this._renderEvolution()];
    return [this._renderKpis(), this._renderEvolution()];
  }

  _renderUnderstand() {
    const insights = this._insights;
    if (this._insightsError) {
      return [this._errorCard(this._t("tabUnderstand"), this._t("insightsFailed", { error: this._insightsError }), () => this._load())];
    }
    if (insights && !insights.days.length && insights.daily && insights.daily.length) {
      return [this._renderCalendar()];
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
      // With a Heating tab, the weather is there.
      duo(this._renderBaseload(), this._entry.heating ? null : this._renderWeather()),
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
      Object.entries(MEASURES)
        .filter(([measure]) => this._costed() || measure === "energy")
        .map(([measure, label]) =>
        h(
          "button",
          {
            "aria-pressed": String(this._measureNow() === measure),
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
    const heating = this._heating;
    const split = heating && heating.totals && (!heating.gas || (heating.water_split && !heating.water_gas)) && this._measureNow() !== "price";
    return this._card(this._t(`${this._measureNow()}By${by}`), this._timeChart, {
      info: [this._t(`${this._measureNow()}Per${by}`), split ? this._t("heatingSplitInfo") : null],
      uses: this._uses("consumptionDays", "contract", "colors", split ? "heating" : null, split && heating.water_split ? "water" : null, "outdoor"),
      hint: this._entry.outdoor ? null : this._t("hintOutdoor"),
      tools: [measures, this._toggle("time")],
    });
  }

  // What the time chart shows: the kWh alone when nothing is costed.
  _measureNow() {
    return this._costed() ? this._measure : "energy";
  }

  // The buckets of the time chart: with the days only known in total.
  _timeBuckets() {
    return { items: this._data.energySeries || this._data.series, monthly: this._data.group_by === "month" };
  }

  // What the time chart shows of each bucket, and how to write it.
  _measureOf() {
    switch (this._measureNow()) {
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
    const series = this._timeBuckets().items;
    if (this._data.group_by !== "month" || !series.length) return partial;
    const range = this._energyRange();
    if (range.start.slice(8, 10) !== "01") partial.add(0);
    const [year, month, day] = lastDayOf(range.end).split("-").map(Number);
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
    // The consumption also counts the days only known in total.
    const days = this._days(this._energyRange());
    const energy = actual.energy + (this._data.daily ? this._data.daily.energy : 0);
    return h(
      "section",
      { class: "card kpis" },
      tile(this._t("actualCost"), this._money(actual.total_cost, 0), this._t("ofWhichSubscription", { amount: this._money(actual.fixed_cost, 0) })),
      tile(this._t("consumption"), this._kwh(energy), days > 0 ? this._t("perDayEnergy", { energy: this._kwh(energy / days) }) : null),
      actual.energy
        ? tile(
            this._t("averagePrice"),
            [this._average(actual.variable_cost / actual.energy), h("span", { class: "unit" }, "/kWh")],
            this._t("averageSub", { price: this._average(actual.total_cost / actual.energy) }),
          )
        : null,
      this._renderUsage(tile),
      this._renderHeatingTile(),
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
          this._t(this._pricingKey(contract)),
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
    // Without a meter, nothing is compared.
    if (this._data.meterless) return [];
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
      this._drawCalendar(this._calendarChart, this._calendarDetail, this._calendarDays());
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
    if (this._heatingDaysChart) {
      this._drawHeatingDays(this._heatingDaysChart, this._heating);
    }
    if (this._heatingProfileChart) {
      this._drawProfile(this._heatingProfileChart, this._heating.profile, { color: "var(--ec-s2)", offPeak: !this._heating.gas, label: this._t("heatingProfile") });
    }
    if (this._heatingWeatherChart) {
      this._drawWeather(this._heatingWeatherChart, this._heatingWeatherPoints);
    }
  }

  _renderTimeChart() {
    const actual = { id: ACTUAL, name: this._t({ energy: "consumption", price: "averagePrice" }[this._measureNow()] || "actual") };
    const buckets = this._timeBuckets();
    // A day only known in total has no cost: that is not a missing contract.
    const missing = buckets.items.some((bucket) => bucket.actual === null && !bucket.daily);
    const temperatures = this._bucketTemperatures();
    const measure = this._measureOf();
    const partial = this._partialBuckets();
    const split = this._views.time === "chart" ? this._heatingSeries(actual, measure) : null;
    if (this._views.time === "chart") {
      const series = split || [{ ...actual, values: buckets.items.map((bucket) => measure.value(bucket) ?? 0) }];
      const options = { temperatures, axis: measure.axis, format: measure.format, partial, buckets };
      const frame = split
        ? this._drawColumns(this._timeChart, series, { ...options, stacked: true })
        : this._data.group_by === "month"
          ? this._drawColumns(this._timeChart, series, options)
          : this._drawLines(this._timeChart, series, { zero: false, ...options });
      if (temperatures) {
        // Blue beside the orange of the heating.
        frame.temperatureColor = split ? "var(--ec-s1)" : "var(--ec-s2)";
        this._timeChart.append(this._temperatureStrip(frame, temperatures, frame.temperatureColor));
      }
    } else {
      const extra = temperatures && { label: this._t("temperature"), values: temperatures, format: (value) => this._degrees(value) };
      this._timeChart.replaceChildren(this._seriesTable((bucket) => measure.value(bucket), false, [actual], extra, measure.format, buckets.items));
    }
    if (this._views.time === "chart") {
      this._timeChart.append(
        this._keys(
          ...(split || [actual]).map((item) => [h("span", { class: "swatch", style: { background: item.color || "var(--ec-money)" } }), item.name]),
          partial.size ? [h("span", { class: "swatch hatched" }), this._t("partialMonth")] : null,
          temperatures ? [h("span", { class: "line-key", style: { background: split ? "var(--ec-s1)" : "var(--ec-s2)" } }), this._t("temperature")] : null,
        ),
      );
    }
    if (missing && this._measureNow() !== "energy") {
      this._timeChart.append(h("p", { class: "note" }, this._t("partialActual")));
    }
  }

  // The time chart's columns split into heating, hot water and the rest of the
  // home, when they are measured and part of the electricity; null otherwise.
  _heatingSeries(actual, measure) {
    const heating = this._heating;
    if (!heating || !heating.totals || this._measureNow() === "price") return null;
    const cost = this._measureNow() === "cost";
    // Only what the electricity holds: gas is outside it.
    const inside = !heating.gas;
    const water = heating.water_split && !heating.water_gas;
    if (!inside && !water) return null;
    const monthly = this._data.group_by === "month";
    const key = (day) => (monthly ? day.slice(0, 7) : day);
    const parts = new Map();
    for (const day of heating.days) {
      const part = parts.get(key(day.date)) || { heating: 0, water: 0 };
      if (inside) part.heating += (cost ? day.heating_cost : day.heating) || 0;
      if (water) part.water += (cost ? day.water_cost : day.water) || 0;
      parts.set(key(day.date), part);
    }
    const buckets = this._timeBuckets().items.map((bucket) => {
      const total = measure.value(bucket) ?? 0;
      const part = parts.get(key(bucket.start));
      // Before the heating statistics, the heating isn't told apart.
      if (!part) return { heat: 0, hot: 0, rest: 0, whole: total };
      const heat = Math.min(part.heating, total);
      const hot = Math.min(part.water, total - heat);
      return { heat, hot, rest: total - heat - hot, whole: 0 };
    });
    // Nothing to split: the consumption alone.
    if (!buckets.some((bucket) => bucket.heat + bucket.hot + bucket.rest > 0)) return null;
    return [
      inside ? { id: "heating", color: "var(--ec-s2)", name: this._t("heating"), values: buckets.map((bucket) => bucket.heat) } : null,
      water ? { id: "water", color: "var(--ec-s3)", name: this._t("hotWater"), values: buckets.map((bucket) => bucket.hot) } : null,
      { ...actual, name: this._t("restOfHome"), values: buckets.map((bucket) => bucket.rest) },
      buckets.some((bucket) => bucket.whole > 0)
        ? { id: "whole", color: "var(--ec-other)", name: this._t("wholeHome"), values: buckets.map((bucket) => bucket.whole) }
        : null,
    ].filter(Boolean);
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

  // The buckets of the period's series: its days, or its months.
  _periodBuckets() {
    return { items: this._data.series, monthly: this._data.group_by === "month" };
  }

  _frame(container, values, zero, axis = (value, digits) => this._money(value, digits), buckets = this._periodBuckets()) {
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
    const { items, monthly } = buckets;
    const count = items.length;
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
    const step = Math.max(1, Math.ceil((monthly ? 34 : 26) / band));
    items.forEach((bucket, index) => {
      if (index % step !== 0) return;
      let label = this._bucketLabel(bucket.start, false, monthly);
      if (monthly && (index === 0 || bucket.start.slice(5, 7) === "01") && band * step >= 52) {
        label = this._dayLabel(bucket.start, { month: "short", year: "2-digit" });
      }
      grid.append(s("text", { x: x(index), y: height - 8, "text-anchor": "middle" }, label));
    });
    root.append(grid);
    return { root, width, height, margin, plotWidth, plotHeight, x, y, band, count, buckets, monthly };
  }

  // Columns, hatched where a bucket is only partly covered by the data.
  // Columns side by side, or stacked in one column from the first series up.
  _drawColumns(container, series, { temperatures = null, axis, format, partial = new Set(), stacked = false, buckets = this._periodBuckets() } = {}) {
    const items = buckets.items;
    const values = stacked ? items.map((bucket, index) => series.reduce((sum, item) => sum + (item.values[index] || 0), 0)) : series.flatMap((item) => item.values);
    const frame = this._frame(container, values, false, axis, buckets);
    frame.temperatures = temperatures;
    frame.format = format;
    frame.stacked = stacked;
    const { root, margin, plotHeight, x, y, band } = frame;
    const wash = s("rect", { y: margin.top, height: plotHeight, width: band, style: { fill: "var(--ec-wash)", visibility: "hidden" } });
    root.insertBefore(wash, root.firstChild);
    // The series a partial month hatches: the actual cost, or the consumption
    // without the heating detail, each in its own color.
    const number = (this._patterns = (this._patterns || 0) + 1);
    const hatches = { [ACTUAL]: ["var(--ec-money-soft)", "var(--ec-money)"], whole: ["var(--ec-wash)", "var(--ec-other)"], ...Object.fromEntries(series.filter((item) => item.hatch).map((item) => [item.id, item.hatch])) };
    const hatch = (id) => `ec-hatch-${number}-${id}`;
    root.insertBefore(
      s(
        "defs",
        {},
        Object.entries(hatches).map(([id, [soft, strong]]) =>
          s(
            "pattern",
            { id: hatch(id), width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" },
            s("rect", { width: 6, height: 6, style: { fill: soft } }),
            s("rect", { width: 2.5, height: 6, style: { fill: strong } }),
          ),
        ),
      ),
      root.firstChild,
    );
    const gap = 2;
    const group = band * 0.8;
    const columns = stacked ? 1 : series.length;
    const barWidth = Math.max(2, Math.min(24, (group - gap * (columns - 1)) / columns));
    const used = barWidth * columns + gap * (columns - 1);
    const marks = s("g");
    const base = y(0);
    const fill = (item, index) => {
      const color = item.color || this._color(item.id);
      return (item.hatch || partial.has(index)) && item.id in hatches ? { fill: `url(#${hatch(item.id)})`, stroke: color, "stroke-width": "1.5px" } : { fill: color };
    };
    items.forEach((bucket, index) => {
      const left = x(index) - used / 2;
      if (stacked) {
        let bottom = 0;
        const drawn = series.filter((item) => item.values[index] > 0);
        drawn.forEach((item, position) => {
          const top = bottom + item.values[index];
          // Only the top of the stack is rounded; a 1 px gap of surface between layers.
          marks.append(
            position === drawn.length - 1
              ? s("path", { d: columnPath(left, barWidth, y(bottom), y(top)), style: fill(item, index) })
              : s("rect", { x: left, y: y(top), width: barWidth, height: Math.max(0, y(bottom) - y(top) - 1), style: fill(item, index) }),
          );
          bottom = top;
        });
        return;
      }
      series.forEach((item, position) => {
        const value = item.values[index];
        if (!value) return;
        marks.append(s("path", { d: columnPath(left + position * (barWidth + gap), barWidth, base, y(value)), style: fill(item, index) }));
      });
    });
    root.append(marks);
    const tooltip = h("div", { class: "tooltip", hidden: true });
    const hits = s("g");
    items.forEach((bucket, index) => {
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
          "aria-label": this._bucketLabel(bucket.start, true, buckets.monthly),
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

  _drawLines(container, series, { zero, temperatures = null, axis, format, buckets = this._periodBuckets() }) {
    const values = series.flatMap((item) => item.values);
    const frame = this._frame(container, values, zero, axis, buckets);
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
    const bucket = frame.buckets.items[index];
    const format = frame.format || ((amount) => this._money(amount));
    const items = [...series].map((item) => ({ item, value: item.values[index] }));
    // A stack reads from its top; columns side by side from the highest.
    if (frame.stacked) items.reverse();
    else items.sort((first, second) => second.value - first.value);
    const rows = items.map(({ item, value }) =>
      h(
        "div",
        { class: "row" },
        h("span", { class: "line-key", style: { background: item.color || this._color(item.id) } }),
        h("strong", {}, format(value)),
        h("span", {}, item.name),
      ),
    );
    const temperature = frame.temperatures ? frame.temperatures[index] : null;
    if (temperature !== null) {
      rows.push(h("div", { class: "row" }, h("span", { class: "line-key", style: { background: frame.temperatureColor || "var(--ec-s2)" } }), h("strong", {}, this._degrees(temperature)), h("span", {}, this._t("temperature"))));
    }
    const total = frame.stacked ? ` · ${format(items.reduce((sum, { value }) => sum + (value || 0), 0))}` : "";
    tooltip.replaceChildren(h("div", { class: "head" }, `${this._bucketLabel(bucket.start, true, frame.monthly)}${total}`), ...rows);
    tooltip.hidden = false;
    const width = tooltip.offsetWidth;
    const left = anchor + 12 + width > frame.width ? anchor - 12 - width : anchor + 12;
    tooltip.style.left = `${Math.max(0, left)}px`;
    tooltip.style.top = `${frame.margin.top}px`;
  }

  _seriesTable(value, withActual, contracts = this._data.contracts, extra = null, format = (amount) => this._money(amount), buckets = this._data.series) {
    const head = h(
      "tr",
      {},
      h("th", {}, this._t("period")),
      contracts.map((contract) => h("th", {}, contract.name)),
      withActual && this._data.actual ? h("th", {}, this._t("actual")) : null,
      extra ? h("th", {}, extra.label) : null,
    );
    const rows = buckets.map((bucket, index) =>
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
      { info: [this._t("nowInfo")], uses: this._uses("contractToday", "colorsToday"), rerender: () => this._renderHead() },
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
      return this._card(this._t("season", { season: label }), this._tempoMeters(tempo), {
        info: [this._t("tempoLeftInfo")],
        uses: this._uses("contractToday", "colorsToday"),
        rerender: () => this._renderHead(),
      });
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
        uses: this._uses("consumption", "contractToday", "colorsToday", projection ? "history" : null),
        rerender: () => this._renderHead(),
      },
    );
  }

  // The outdoor temperature of each day or month of the time chart.
  _bucketTemperatures() {
    const days = this._insights ? [...this._insights.days, ...(this._insights.daily || [])] : [];
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
    return this._timeBuckets().items.map((bucket) => {
      const sum = sums.get(month ? bucket.start.slice(0, 7) : bucket.start.slice(0, 10));
      return sum ? sum[0] / sum[1] : null;
    });
  }

  // A second chart under the costs, on the same days or months: never two
  // scales on one chart.
  _temperatureStrip(frame, temperatures, color = "var(--ec-s2)") {
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
    root.append(s("path", { d: path, style: { fill: "none", stroke: color, "stroke-width": "2px", "stroke-linejoin": "round", "stroke-linecap": "round" } }));
    temperatures.forEach((value, index) => {
      const alone = (temperatures[index - 1] ?? null) === null && (temperatures[index + 1] ?? null) === null;
      if (value === null || (!frame.monthly && !alone)) return;
      root.append(s("circle", { cx: x(index), cy: y(value), r: 4, style: { fill: color, stroke: "var(--ec-surface)", "stroke-width": "2px" } }));
    });
    return root;
  }

  // The typical day -------------------------------------------------------------

  // The highest hour of a day, and a second one when it comes close and stands
  // apart: the hours around the highest belong to the same peak.
  _peaks(values) {
    const order = values.map((value, hour) => hour).sort((first, second) => values[second] - values[first]);
    const apart = (hour) => Math.min(Math.abs(hour - order[0]), 24 - Math.abs(hour - order[0])) >= 3;
    const second = order.find((hour) => apart(hour));
    return second !== undefined && values[second] >= 0.75 * values[order[0]]
      ? this._t("peaksAt", { first: this._hour(order[0]), second: this._hour(second) })
      : this._t("peakAt", { hour: this._hour(order[0]) });
  }

  // The average hour of the period, with the off-peak hours of the contract in
  // force shaded behind it.
  _renderProfile() {
    const values = this._insights.profile.map((value) => value ?? 0);
    const day = values.reduce((sum, value) => sum + value, 0);
    if (!(day > 0)) return null;
    const share = this._offPeakShare();
    const peaks = this._peaks(values);
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
      { info: [this._t("profileInfo", { days: this._number(this._insights.days.length) })], uses: this._uses("consumption", "contract") },
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

  _drawProfile(container, profile, { color = "var(--ec-money)", offPeak = true, label = this._t("profile") } = {}) {
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
    const root = s("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": label });
    // The off-peak hours, shaded behind the columns and named above them.
    const long = this._t("offPeakBand");
    const short = this._t("offPeakBandShort");
    for (const [start, end] of dayPieces(offPeak ? this._offPeakRanges() : [])) {
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
        root.append(s("path", { d: columnPath(at(hour) + (band - bar) / 2, bar, y(0), y(value)), style: { fill: color } }));
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
      { info: [this._t("peakByColorInfo")], uses: this._uses("consumption", "contract", "colors") },
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
      { info: [this._t("baseloadInfo", { energy: this._kwh(baseload.annual_energy) }), this._t("baseloadNote")], uses: this._uses("consumption", "contract") },
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
          heating ? this._t(weather.base_fitted ? "baseFitted" : "baseDefault", { base }) : null,
          heating ? this._curveNote(weather) : null,
        ],
        uses: this._uses("consumption", "outdoor"),
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
      const model = (value) => Math.max(0, weather.intercept + lineHeating(weather, weather.base - value));
      // Straight above the base, a curve below it: 48 steps draw it smoothly.
      const steps = Array.from({ length: 49 }, (_, index) => low + ((high - low) * index) / 48);
      const knots = [...steps, ...(weather.base > low && weather.base < high ? [weather.base] : [])].sort((a, b) => a - b);
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

  // The calendar's days: with those only known in total, which have no cost.
  _calendarDays() {
    const daily = (this._insights.daily || []).map((day) => ({ ...day, cost: null }));
    return [...daily, ...this._insights.days].sort((first, second) => (first.date < second.date ? -1 : 1));
  }

  _renderCalendar() {
    const days = this._calendarDays();
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
    return this._card(this._t(tempo ? "calendarTempo" : "calendar"), [this._calendarChart, this._calendarDetail], {
      info: [this._t(tempo ? "calendarTempoInfo" : "calendarInfo")],
      uses: this._uses("colors", "consumptionDays", "contract"),
      tools: legend,
    });
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
    const costs = days.map((day) => day.cost).filter((cost) => cost !== null);
    const cheapest = Math.min(...costs);
    const spread = Math.max(...costs) - cheapest || 1;
    const fill = (day) =>
      tempo ? DAY_FILLS[day.color] || "var(--ec-axis)" : day.cost === null ? "var(--ec-axis)" : costFill(30 + 70 * ((day.cost - cheapest) / spread));
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
        day.cost !== null ? h("span", {}, this._money(day.cost)) : null,
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
      { info: [this._t("topDaysInfo")], uses: this._uses("consumption", "contract", "colors", weather ? "outdoor" : null) },
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
      { info: [this._t("spendInfo")], uses: this._uses("consumption", "contract"), tools: this._toggle("tranches") },
    );
  }

  // Comparison ----------------------------------------------------------------

  // Every contract on the period's consumption: a ranking led by its verdict,
  // the bill of the one chosen, and how the gap with it built up.
  _renderCompare() {
    if (!this._costed()) return [this._noCosts()];
    const contracts = [...this._data.contracts].sort((first, second) => first.total_cost - second.total_cost);
    // The contracts are compared with what was paid only when a contract was in
    // force at every hour: the others cost nothing in the actual cost.
    const actual = this._data.saving === null ? null : this._data.actual;
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
      this._data.actual && this._billContract !== mine ? this._renderGap() : null,
    ];
  }

  _noCosts() {
    return h("section", { class: "card message" }, this._t("noCosts", { date: this._dayLabel(this._entry.first_day) }));
  }

  // Who comes first, and by how much.
  _verdict(contracts, actual, mine) {
    const best = contracts[0];
    if (!best) return null;
    if (!actual) return this._lead(best.name, contracts.length > 1 ? this._t("isCheapest") : null);
    const saving = this._data.saving;
    if (saving >= 0.5) {
      // Against the best contract the integration found.
      return this._lead(this._data.best, this._t("wouldSave", { amount: this._money(saving, 0), change: this._percent(-saving / actual.total_cost) }));
    }
    const name = mine && this._data.contracts.find((contract) => contract.id === mine).name;
    const next = contracts.find((contract) => contract.id !== mine && contract.total_cost - actual.total_cost >= 0.5);
    if (!name) return this._lead(this._t("verdictActual"));
    return this._lead(name, next ? this._t("cheapestBy", { amount: this._money(next.total_cost - actual.total_cost, 0), name: next.name }) : this._t("isCheapest"));
  }

  _renderRanking(contracts, actual, mine) {
    const known = Object.fromEntries(this._entry.contracts.map((contract) => [contract.id, contract]));
    const most = Math.max(...contracts.map((contract) => contract.total_cost), 0.01);
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
      const sub = difference === null || Math.abs(difference) < 0.5 ? "" : `${this._money(difference, 0, "exceptZero")} · ${this._percent(difference / actual.total_cost)}`;
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
      uses: this._uses("consumption", "contract"),
    });
  }

  // Where a contract's prices come from, as a translation key.
  _pricingKey(contract) {
    return { official: "regulated", entity: "sensorPrices" }[contract.pricing] || "manualPrices";
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
        if (contract.pricing === "manual" && !contract.prices.length) {
          why = this._t("waitingPrices");
        } else if (waiting) {
          const reason = waiting.reason === "color" ? "waitingColor" : contract.pricing === "entity" ? "waitingSensor" : "waitingPrice";
          why = this._t(reason, { day });
        }
        return h(
          "div",
          { class: "rank pending" },
          h("span", { class: "position" }, "–"),
          h("span", { class: "who" }, h("span", { class: "name" }, contract.name), h("span", { class: "sub" }, why)),
          contract.pricing === "manual"
            ? h("a", { class: "cta", href: `/config/integrations/integration/${DOMAIN}` }, icon(ICONS.plus), this._t("addPrices"))
            : null,
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
      verdict = Math.abs(bill.difference) > 0.005 ? this._t("billVsActual", { amount: this._money(bill.difference, 2, "exceptZero") }) : this._t("same");
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
        uses: this._uses("consumption", "chosen", "otherContract"),
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
      uses: this._uses("consumption", "chosen", "otherContract"),
      tools: this._toggle("cumulative"),
    });
  }

  // Heating ------------------------------------------------------------------------

  // The tabs of the source: Heating only when there is something to show.
  _tabList() {
    const entry = this._entry;
    // Without a meter, only what doesn't need the consumption.
    const meterless = entry && entry.meter === false;
    return ALL_TABS.filter((tab) => (tab === "heating" ? entry && entry.heating : !meterless || tab === "follow"));
  }

  _renderHeatingTab() {
    if (this._heatingError) {
      return [this._errorCard(this._t("tabHeating"), this._t("insightsFailed", { error: this._heatingError }), () => this._load())];
    }
    const heating = this._heating;
    // A source without a meter has no heating days until its statistics have some.
    if (!heating && !this._entry.last_day) return [h("section", { class: "card message" }, this._t("heatingNoData"))];
    if (!heating) return [this._loadingCard()];
    if (!heating.measured) {
      return [this._renderHeatingKpis(heating), h("div", { class: "duo" }, this._renderHeatingWeather(heating), this._renderSimulator(heating)), this._renderDpe()];
    }
    if (!heating.days.length) {
      // Only before the heating statistics: what the Linky's days estimate.
      if (!heating.before) return [h("section", { class: "card message" }, this._t("heatingNoData"))];
      return [this._renderHeatingKpis(heating), this._renderHeatingDays(heating), this._renderDpe()];
    }
    const duo = (...cards) => {
      const present = cards.filter(Boolean);
      return present.length ? h("div", { class: "duo" }, present) : null;
    };
    return [
      this._renderHeatingKpis(heating),
      this._renderHeatingDays(heating),
      this._renderHeatingSplit(heating),
      duo(this._renderHeatingProfile(heating), this._renderHeatingWeather(heating)),
      this._renderSimulator(heating),
      this._renderDpe(),
    ];
  }

  // Energy label --------------------------------------------------------------

  // The label of the 12 months that end with the period. Loaded on its own, for
  // this tab only, and again only when the source or the period's end changes.
  _renderDpe() {
    const entry = this._entry;
    const end = this._request && this._request.end;
    if (!end) return null;
    const key = `${entry.entry_id}|${end}`;
    if (this._dpeKey !== key) this._loadDpe(key, end);
    const title = this._t("dpeTitle");
    if (this._dpeError) {
      return this._errorCard(title, this._t("insightsFailed", { error: this._dpeError }), () => {
        this._dpeKey = null;
        this._renderContent();
      });
    }
    // The label of the previous period stays while the next one loads.
    const dpe = this._dpeEntry === entry.entry_id ? this._dpe : null;
    if (!dpe) return this._loadingCard();
    // Without a living area, the label waits for it: the settings come first.
    if (dpe.missing === "surface") {
      const admin = Boolean(this._hass.user && this._hass.user.is_admin);
      return this._card(title, [h("p", { class: "message" }, this._t(admin ? "dpeSurfaceNeeded" : "dpeSurfaceNeededAdmin")), this._dpeSettings(dpe)]);
    }
    if (!dpe.classes) return h("section", { class: "card message" }, this._t("dpeNoData"));
    const long = { day: "numeric", month: "long", year: "numeric" };
    const partial = dpe.days < DPE_YEAR_DAYS ? this._dpePartial(dpe, long) : null;
    return this._card(title, [this._views.dpe === "table" ? this._dpeTable(dpe) : this._dpeChart(dpe), partial], {
      info: [
        this._t("dpeInfoPeriod", { start: this._dayLabel(dpe.start, long), end: this._dayLabel(dpe.end, long) }),
        this._dpeConventional(dpe),
        this._t("dpeInfoFactors"),
        this._t("dpeInfoClass"),
        this._t("dpeInfoNotOfficial"),
      ],
      extra: this._dpeSettings(dpe),
      uses: this._uses("dpeHeating", "dpeWater", "auxiliaries", "surface", "outdoor", dpe.conventional.source === "thermometers" ? "indoor" : null),
      tools: this._toggle("dpe"),
    });
  }

  // How the heating was moved to the DPE's setpoint, 19 °C by day and 16 °C at
  // night, from the home's.
  _dpeConventional(dpe) {
    const conventional = dpe.conventional;
    if (!conventional.applied) return this._t("dpeConventionalNone");
    const after = dpe.uses.find((item) => item.use === "heating").energy;
    const values = { indoor: `${this._number(conventional.indoor, 1)} °C`, after: this._kwh(after), before: this._kwh(after - conventional.extra) };
    if (conventional.source === "thermometers") return this._t("dpeConventionalMeasured", values);
    return this._t(conventional.shift === 0 ? "dpeConventionalSame" : "dpeConventionalSetting", values);
  }

  async _loadDpe(key, end) {
    const entryId = this._entry.entry_id;
    this._dpeKey = key;
    this._dpeError = null;
    try {
      const dpe = await this._hass.callWS({ type: `${DOMAIN}/dpe`, entry_id: entryId, end });
      if (this._dpeKey !== key) return;
      this._dpe = dpe;
      this._dpeEntry = entryId;
      this._dpeDraft = null;
      // A save reloads the label: what it said stays.
      if (!this._dpeSaving) this._dpeStatus = null;
      this._dpeSaving = false;
    } catch (error) {
      if (this._dpeKey !== key) return;
      this._dpeError = error.message || String(error);
      this._dpeSaving = false;
    }
    if (this._tab === "heating") this._renderContent();
  }

  // The letter, beside the energy and climate scales: the class of each is
  // drawn larger, with the value.
  _dpeChart(dpe) {
    const classes = dpe.classes;
    const scale = (name, value) => {
      const { bounds, colors } = DPE_SCALES[name];
      return h(
        "div",
        { class: "dpe-scale" },
        h("h3", {}, this._t(name === "energy" ? "dpeEnergy" : "dpeClimate")),
        DPE_LETTERS.map((letter, index) => {
          const range = index === 0 ? `≤ ${bounds[0]}` : index === bounds.length ? `> ${bounds[bounds.length - 1]}` : this._t("dpeRange", { from: bounds[index - 1] + 1, to: bounds[index] });
          const current = letter === classes[name];
          return h(
            "div",
            { class: current ? "dpe-row current" : "dpe-row" },
            h("div", { class: "dpe-bar", style: { width: `${38 + index * 8}%`, background: colors[index][0], color: colors[index][1] } }, h("span", {}, range), h("b", {}, letter)),
            current ? h("span", { class: "dpe-value" }, this._number(value, name === "climate" ? 1 : 0)) : null,
          );
        }),
      );
    };
    // The letter takes the colors of the scale that sets it, grey when the year
    // isn't whole: without its winter, the class means little.
    const from = classes.label === classes.energy ? "energy" : "climate";
    const [background, color] = DPE_SCALES[from].colors[DPE_LETTERS.indexOf(classes.label)];
    const partial = dpe.days < DPE_YEAR_DAYS;
    return h(
      "div",
      { class: "dpe" },
      h("div", { class: partial ? "dpe-letter partial" : "dpe-letter", role: "img", "aria-label": this._t("dpeClass", { letter: classes.label }), style: partial ? {} : { background, color } }, classes.label),
      h("div", { class: "dpe-scales" }, scale("energy", dpe.energy), scale("climate", dpe.climate)),
    );
  }

  // Why the label covers less than a year: the data starts later, or the Linky's
  // days before have no outdoor temperature to estimate the heating.
  _dpePartial(dpe, long) {
    const values = { start: this._dayLabel(dpe.start, long), days: dpe.days };
    if (!dpe.unestimated) return h("p", { class: "note" }, this._t("dpePartial", values));
    if (dpe.unestimated.open_meteo) return h("p", { class: "note" }, this._t("dpeNoWeather", values));
    return h(
      "p",
      { class: "note" },
      `${this._t("dpeNoWeather", values)} ${this._t("dpeOpenMeteo")} `,
      h("a", { href: `/config/integrations/integration/${DOMAIN}` }, this._t("weatherOpen")),
    );
  }

  _dpeTable(dpe) {
    const names = { heating: "useHeating", water: "useHotWater", auxiliaries: "useAuxiliaries" };
    const hues = { heating: "var(--ec-s2)", water: "var(--ec-s3)", auxiliaries: "var(--ec-other)" };
    const sum = (key) => dpe.uses.reduce((total, item) => total + item[key], 0);
    const line = (name, item, hue = null, attributes = {}) =>
      h(
        "tr",
        attributes,
        h("td", {}, h("span", { class: "dpe-use" }, hue ? h("span", { class: "dpe-dot", style: { background: hue } }) : null, name)),
        h("td", {}, this._kwh(item.energy)),
        h("td", {}, `${this._number(item.primary)} kWhEP`),
        h("td", {}, `${this._number(item.co2)} kg`),
      );
    return h(
      "div",
      { class: "table-wrap" },
      h(
        "table",
        { class: "dpe-table" },
        h("thead", {}, h("tr", {}, h("th", {}, this._t("dpeUse")), h("th", {}, this._t("dpeFinal")), h("th", {}, this._t("dpePrimary")), h("th", {}, "CO₂"))),
        h(
          "tbody",
          {},
          dpe.uses.map((item) => line(this._t(names[item.use]), item, hues[item.use])),
          line(this._t("dpeTotal"), { energy: sum("energy"), primary: sum("primary"), co2: sum("co2") }, null, { class: "total" }),
        ),
      ),
    );
  }

  // The settings, in the card's method. Typing only updates the buttons, so
  // the field keeps the focus; saving loads the label again.
  _dpeSettings(dpe) {
    const admin = Boolean(this._hass.user && this._hass.user.is_admin);
    if (!this._dpeDraft) this._dpeDraft = { ...dpe.settings };
    const draft = this._dpeDraft;
    const water = dpe.uses.find((item) => item.use === "water");
    const waterUsed = water.source === "share";
    const setpoint = dpe.conventional.applied && dpe.conventional.source === "setting";
    const status = h("span", { class: "dpe-status", role: "status" });
    const save = h("button", { type: "submit", class: "toggle primary" }, this._t("dpeSave"));
    let form = null;
    // An empty field is no value: the living area has none until it's given.
    const number = (value) => (value === null || value === undefined || value === "" ? null : Number(value));
    const refresh = () => {
      const changed = Object.keys(dpe.settings).some((key) => number(draft[key]) !== dpe.settings[key]);
      save.disabled = !changed || !form.checkValidity();
      // What the last save said, until the next keystroke.
      status.textContent = this._dpeStatus || (changed ? this._t("dpeUnsaved") : "");
    };
    const field = (key, label, min, max, unit, help = null) =>
      h(
        "label",
        { class: "dpe-field" },
        label,
        h(
          "span",
          { class: "row" },
          h("input", {
            type: "number",
            name: key,
            min,
            max,
            step: "any",
            required: true,
            value: draft[key] ?? "",
            disabled: !admin,
            oninput: (event) => {
              draft[key] = event.target.value;
              this._dpeStatus = null;
              refresh();
            },
          }),
          unit,
        ),
        help ? h("small", {}, help) : null,
      );
    form = h(
      "form",
      {
        class: "dpe-settings",
        onsubmit: (event) => {
          event.preventDefault();
          this._saveDpe();
        },
      },
      h("h3", {}, this._t("dpeSettings")),
      h(
        "div",
        { class: "dpe-fields" },
        field("surface", this._t("dpeSurface"), 5, 2000, "m²"),
        field("coefficient", this._t("dpeCoefficient"), 1, 3, "kWhEP/kWh"),
        field("auxiliaries", this._t("dpeAuxiliaries"), 0, 30, "%"),
        // Only when the hot water is neither measured nor estimated.
        waterUsed ? field("water", this._t("dpeWaterShare"), 0, 60, "%", this._t("dpeWaterUsed")) : null,
        // The home's setpoint, without thermometers to measure it.
        setpoint ? field("setpoint", this._t("dpeSetpoint"), 10, 26, "°C") : null,
        setpoint ? field("setback", this._t("dpeSetback"), 0, 10, "°C") : null,
      ),
      admin
        ? h(
            "div",
            { class: "dpe-actions" },
            save,
            h(
              "button",
              {
                type: "button",
                class: "toggle",
                onclick: () => {
                  // The living area has no default: the one typed stays.
                  Object.assign(draft, { ...dpe.defaults, surface: dpe.defaults.surface ?? draft.surface });
                  for (const input of form.querySelectorAll("input")) input.value = draft[input.name] ?? "";
                  this._dpeStatus = null;
                  refresh();
                },
              },
              this._t("dpeDefaults"),
            ),
            status,
          )
        : h("p", {}, this._t("dpeReadOnly")),
    );
    refresh();
    return form;
  }

  async _saveDpe() {
    const settings = Object.fromEntries(Object.entries(this._dpeDraft).map(([key, value]) => [key, Number(value)]));
    try {
      await this._hass.callWS({ type: `${DOMAIN}/dpe/save`, entry_id: this._entry.entry_id, ...settings });
    } catch (error) {
      this._dpeStatus = this._t("dpeSaveFailed", { error: error.message || String(error) });
      this._renderContent();
      return;
    }
    this._dpeStatus = this._t("dpeSaved");
    this._dpeSaving = true;
    this._dpeKey = null;
    this._renderContent();
  }

  // The heating of the period: measured, or estimated from the source when no
  // statistic measures it. Null when there is neither.
  _heatingTotals(heating) {
    if (heating.totals) return { totals: heating.totals, days: heating.days.length, estimated: false };
    const estimated = heating.estimated;
    if (!estimated) return null;
    return { totals: { ...estimated, water: 0, water_cost: 0 }, days: heating.weather ? heating.weather.days : 0, estimated: true };
  }

  // The Overview's tile: what heating cost, and a way to its tab.
  _renderHeatingTile() {
    const found = this._heating && this._heatingTotals(this._heating);
    if (!found) return null;
    const heating = this._heating;
    const totals = found.totals;
    const value = totals.heating_cost !== null ? this._money(totals.heating_cost, 0) : this._kwh(totals.heating);
    const sub =
      totals.share !== null ? this._t("heatingTile", { share: this._share(totals.share), of: this._t(heating.gas ? "ofHomeEnergy" : "ofTheElectricity"), energy: this._kwh(totals.heating) }) : this._kwh(totals.heating);
    return h(
      "button",
      {
        class: "kpi kpi-link",
        onclick: () => {
          this._tab = "heating";
          this._renderTabs();
          this._renderContent();
        },
      },
      h("div", { class: "label" }, this._t("heating")),
      h("div", { class: "value" }, value),
      h("div", { class: "sub" }, sub),
    );
  }

  // What a degree colder costs a day: the slope of the weather line, at the
  // average price of the heating. None when the line doesn't rise.
  _perDegree(heating) {
    const weather = heating.weather;
    if (!weather || weather.slope === null || !(weather.slope > 0)) return null;
    const price = heating.average_price;
    return { energy: weather.slope, cost: price !== null ? weather.slope * price : null };
  }

  _renderHeatingKpis(heating) {
    const found = this._heatingTotals(heating);
    if (!found) return null;
    const { totals, days, estimated } = found;
    const tile = (label, value, sub) => h("div", { class: "kpi" }, h("div", { class: "label" }, label), h("div", { class: "value" }, value), sub ? h("div", { class: "sub" }, sub) : null);
    const perDegree = this._perDegree(heating);
    const cost = totals.heating_cost;
    const before = heating.before;
    const costSub = estimated
      ? this._t("fromTheWeather")
      : before && cost !== null
        ? this._t("measuredOnly")
        : cost !== null
          ? this._t(heating.gas ? "atGasPrice" : "atContractPrices")
          : this._t(heating.gas ? "noGasPrice" : "partlyPriced");
    const energy = totals.heating + (before ? before.heating : 0);
    // Without a measured day, nothing is costed: only the estimated kWh show.
    const measured = !before || heating.days.length > 0;
    return h(
      "section",
      { class: "card kpis" },
      measured ? tile(this._t("heatingCost"), cost !== null ? this._money(cost, 0) : "—", costSub) : null,
      tile(
        this._t("consumption"),
        this._kwh(energy),
        !measured ? this._t("estimatedFromLinky") : before ? this._t("ofWhichEstimated", { energy: this._kwh(before.heating) }) : days ? this._t("perDayEnergy", { energy: this._kwh(energy / days) }) : null,
      ),
      totals.share !== null ? tile(this._t("heatingShareLabel"), this._share(totals.share), this._t(heating.gas ? "ofHomeEnergy" : before ? "ofTheElectricityMeasured" : "ofTheElectricity")) : null,
      heating.water_split && measured
        ? tile(this._t("hotWater"), totals.water_cost !== null ? this._money(totals.water_cost, 0) : this._kwh(totals.water), totals.water_cost !== null ? this._kwh(totals.water) : null)
        : null,
      perDegree
        ? tile(
            this._t("perDegreeColder"),
            perDegree.cost !== null ? `+${this._money(perDegree.cost)}` : `+${this._kwh(perDegree.energy)}`,
            perDegree.cost !== null ? this._t("perDayEnergyAverage", { energy: `+${this._kwh(perDegree.energy)}` }) : this._t("perDayAverage"),
          )
        : null,
    );
  }

  // The days of the heating, or its months over a long period.
  _heatingBuckets(heating) {
    // Before the heating statistics, the days estimated from the Linky, in kWh.
    const estimated = (heating.estimated_days || []).map((day) => ({ ...day, isEstimate: true, estimated: day.heating, heating: 0, heating_cost: null, water: 0, water_cost: null }));
    const all = [...estimated, ...heating.days.map((day) => ({ ...day, estimated: 0 }))].sort((first, second) => first.date.localeCompare(second.date));
    const monthly = all.length > HEATING_MAX_DAYS;
    if (!monthly) return { monthly, buckets: all.map((day) => ({ ...day, start: day.date })) };
    const months = new Map();
    for (const day of all) {
      const start = `${day.date.slice(0, 7)}-01`;
      const bucket = months.get(start) || { start, heating: 0, heating_cost: 0, water: 0, water_cost: 0, estimated: 0, measured: 0, temperatures: [] };
      bucket.heating += day.heating;
      bucket.estimated += day.estimated;
      bucket.water += day.water;
      // The estimated days have no cost: a month keeps the cost of its measured days.
      if (!day.isEstimate) {
        bucket.measured += 1;
        bucket.heating_cost = bucket.heating_cost === null || day.heating_cost === null ? null : bucket.heating_cost + day.heating_cost;
        bucket.water_cost = bucket.water_cost === null || day.water_cost === null ? null : bucket.water_cost + day.water_cost;
      }
      if (day.temperature !== null) bucket.temperatures.push(day.temperature);
      months.set(start, bucket);
    }
    const buckets = [...months.values()].map((bucket) => ({
      ...bucket,
      ...(bucket.measured ? {} : { heating_cost: null, water_cost: null }),
      temperature: bucket.temperatures.length ? bucket.temperatures.reduce((sum, value) => sum + value, 0) / bucket.temperatures.length : null,
    }));
    return { monthly, buckets };
  }

  _heatingMeasureShown(heating) {
    if (!heating.days.length) return "energy";
    return heating.totals.heating_cost !== null || heating.days.some((day) => day.heating_cost !== null) ? this._heatingMeasure : "energy";
  }

  _renderHeatingDays(heating) {
    this._heatingDaysChart = h("div", { class: "chart" });
    const priced = this._heatingMeasureShown(heating) !== "energy" || heating.days.some((day) => day.heating_cost !== null);
    const measures = priced
      ? h(
          "div",
          { class: "segmented small", role: "group", "aria-label": this._t("measure") },
          [
            ["cost", "€"],
            ["energy", "kWh"],
          ].map(([measure, label]) =>
            h(
              "button",
              {
                "aria-pressed": String(this._heatingMeasure === measure),
                onclick: () => {
                  if (this._heatingMeasure === measure) return;
                  this._heatingMeasure = measure;
                  this._renderContent();
                },
              },
              label,
            ),
          ),
        )
      : null;
    const { monthly } = this._heatingBuckets(heating);
    return this._card(this._t(monthly ? "heatingByMonth" : "heatingByDay"), this._heatingDaysChart, {
      info: [this._t(heating.gas ? "heatingByDayGasInfo" : "heatingByDayInfo"), this._waterNote(heating), this._heatingBeforeNote(heating)],
      uses: this._uses("heatingMixed", "water", heating.gas ? "gasPrice" : "contract", "outdoor"),
      hint: this._heatingHints(heating, "water", "gasPrice", "outdoor"),
      tools: measures,
    });
  }

  // How an estimated heating is found: without heating statistics, or before them.
  _estimatedNote(heating) {
    return heating.heaters_from ? this._t("heatingBeforeAll", { date: this._dayLabel(heating.heaters_from, { day: "numeric", month: "long", year: "numeric" }) }) : this._t("estimatedHeatingInfo");
  }

  // The heating before its statistics: estimated from the Linky, or not for want
  // of an outdoor temperature.
  _heatingBeforeNote(heating) {
    const span = (part) => ({ start: this._dayLabel(part.start), end: this._dayLabel(part.end) });
    const notes = [];
    if (heating.before) {
      notes.push(this._t("heatingBeforeInfo", span(heating.before)));
      if (heating.before.missing) notes.push(this._t("heatingMissing", { count: heating.before.missing }));
    }
    if (heating.unestimated) {
      notes.push(this._t("heatingNoWeather", span(heating.unestimated)));
      if (!heating.unestimated.open_meteo) notes.push(this._t("dpeOpenMeteo"));
    }
    return notes.length ? notes.join(" ") : null;
  }

  // What more data would bring to a heating card.
  _heatingHints(heating, ...wanted) {
    const entry = this._entry;
    const hints = {
      statistics: !heating.measured ? this._t("hintHeatingStatistics") : null,
      water: heating.water_split && !heating.water_measured ? this._t("hintWaterHeater") : null,
      gasPrice: heating.gas && (!heating.simulator || heating.simulator.gas_price === null) ? this._t("hintGasPrice") : null,
      outdoor: entry.outdoor ? null : this._t("hintOutdoor"),
    };
    return wanted.map((key) => hints[key]);
  }

  // How the hot water is told apart from the heating, when it is.
  _waterNote(heating) {
    if (!heating.water_split) return null;
    if (heating.water_measured) return this._t("waterMeasuredInfo");
    return this._t("waterEstimatedInfo", { energy: this._kwh(heating.water_per_day), base: `${this._number(heating.water_warm_from)} °C` });
  }

  _drawHeatingDays(container, heating) {
    const measure = this._heatingMeasureShown(heating);
    const { monthly, buckets } = this._heatingBuckets(heating);
    const cost = measure === "cost";
    // The measured layers, when a day is measured.
    const layers = heating.days.length ? [{ key: "heating", color: "var(--ec-s2)", name: this._t("heating") }] : [];
    if (heating.water_split && heating.days.length) layers.push({ key: "water", color: "var(--ec-s3)", name: this._t("hotWater") });
    // In kWh only: the estimated heating has no price.
    if (heating.estimated_days && heating.estimated_days.length && !cost) {
      layers.push({ key: "estimated", color: "var(--ec-s2)", name: this._t("heatingEstimated"), hatch: ["var(--ec-wash)", "var(--ec-s2)"] });
    }
    // A day without a price stays empty, and reads as such in the tooltip.
    const series = layers.map((layer) => ({ id: layer.key, color: layer.color, name: layer.name, hatch: layer.hatch, values: buckets.map((bucket) => bucket[cost ? `${layer.key}_cost` : layer.key] ?? null) }));
    const temperatures = buckets.map((bucket) => bucket.temperature ?? null);
    const known = temperatures.some((value) => value !== null);
    const frame = this._drawColumns(container, series, {
      stacked: true,
      buckets: { items: buckets, monthly },
      temperatures: known ? temperatures : null,
      format: (value) => (value === null || value === undefined ? "—" : cost ? this._money(value) : this._kwh(value)),
      axis: cost ? (value, digits) => this._money(value, digits) : (value, digits) => `${this._number(value, digits)} kWh`,
    });
    frame.root.setAttribute("aria-label", this._t(monthly ? "heatingByMonth" : "heatingByDay"));
    frame.temperatureColor = "var(--ec-s1)";
    if (known) container.append(this._temperatureStrip(frame, temperatures, frame.temperatureColor));
    container.append(
      this._keys(
        ...layers.map((layer) => [h("span", { class: layer.hatch ? "swatch hatched-heating" : "swatch", style: layer.hatch ? {} : { background: layer.color } }), layer.name]),
        known ? [h("span", { class: "line-key", style: { background: frame.temperatureColor } }), this._t("temperature")] : null,
      ),
    );
  }

  // Where the heating goes: by heater and by tranche, or for gas, the share of
  // each energy of the home.
  _renderHeatingSplit(heating) {
    if (heating.gas) return this._renderHomeEnergy(heating);
    const parts = [];
    const statistics = heating.statistics.filter((item) => item.energy > 0);
    if (statistics.length > 1) {
      const most = Math.max(...statistics.map((item) => item.energy));
      parts.push(
        h(
          "div",
          { class: "heat-part" },
          h("h3", {}, this._t("byHeater")),
          [...statistics]
            .sort((first, second) => second.energy - first.energy)
            .map((item) =>
              h(
                "div",
                { class: "heater" },
                h("span", { class: "who" }, item.name, item.area ? h("span", { class: "sub" }, ` ${item.area}`) : null),
                h("div", { class: "track", role: "img", "aria-label": `${item.name}: ${this._kwh(item.energy)}` }, h("div", { class: "fill", style: { width: `${(item.energy / most) * 100}%` } })),
                h("span", { class: "amount" }, this._kwh(item.energy)),
              ),
            ),
        ),
      );
    }
    const tranches = Object.entries(heating.tranches || {}).filter(([, item]) => item.energy > 0);
    if (tranches.length > 1) {
      const names = TRANCHES[this._language];
      const energy = tranches.reduce((sum, [, item]) => sum + item.energy, 0);
      const offPeak = tranches.filter(([tranche]) => tranche === "hc" || tranche.endsWith("_hc")).reduce((sum, [, item]) => sum + item.energy, 0) / energy;
      const segment = (fill, ink, part, text) =>
        part > 0 ? h("div", { class: "segment", style: { "flex-grow": String(part), "flex-basis": "0", background: fill, color: ink } }, part >= 0.12 ? text : "") : null;
      parts.push(
        h(
          "div",
          { class: "heat-part" },
          h("h3", {}, this._t("byTranche")),
          h(
            "div",
            { class: "segments", role: "img", "aria-label": `${this._t("peakShort")} ${this._share(1 - offPeak)}, ${this._t("offPeakShort")} ${this._share(offPeak)}` },
            segment(...TRANCHE_FILLS.blue_hp, 1 - offPeak, `${this._t("peakShort")} ${this._share(1 - offPeak)}`),
            segment(...TRANCHE_FILLS.blue_hc, offPeak, `${this._t("offPeakShort")} ${this._share(offPeak)}`),
          ),
          h(
            "div",
            { class: "table-wrap" },
            h(
              "table",
              {},
              h(
                "tbody",
                {},
                tranches.map(([tranche, item]) =>
                  h(
                    "tr",
                    {},
                    h("td", {}, h("span", { class: "swatch", style: { background: (TRANCHE_FILLS[tranche] || ["#898781"])[0] } }), names[tranche] || tranche),
                    h("td", { class: "sub" }, this._kwh(item.energy)),
                    h("td", {}, h("strong", {}, this._money(item.cost, 0))),
                  ),
                ),
              ),
            ),
          ),
        ),
      );
    }
    if (!parts.length) return null;
    return this._card(this._t("whereHeatingGoes"), h("div", { class: "heat-split" }, parts), {
      info: [this._t("whereHeatingInfo")],
      uses: this._uses("heating", "contract"),
    });
  }

  _renderHomeEnergy(heating) {
    // Without a meter, the rest of the home is unknown.
    if (this._entry.meter === false) return null;
    const totals = heating.totals;
    const euros = totals.heating_cost !== null && (!heating.water_split || totals.water_cost !== null);
    const water = heating.water_split ? (euros ? totals.water_cost : totals.water) : 0;
    // An electric water heater is part of the electricity: shown apart from it.
    const electricity = (euros ? totals.house_cost : totals.house) - (heating.water_gas ? 0 : water);
    const items = [
      { name: this._t("heating"), color: "var(--ec-s2)", ink: "#2a1206", value: euros ? totals.heating_cost : totals.heating },
      heating.water_split ? { name: this._t("hotWater"), color: "var(--ec-s3)", ink: "#06262d", value: water } : null,
      { name: this._t("electricity"), color: "var(--ec-money)", ink: "#ffffff", value: Math.max(0, electricity) },
    ].filter((item) => item && item.value > 0);
    const all = items.reduce((sum, item) => sum + item.value, 0);
    if (!(all > 0)) return null;
    const format = (value) => (euros ? this._money(value, 0) : this._kwh(value));
    return this._card(
      this._t("homeEnergy"),
      [
        this._lead(format(all), items.map((item) => `${item.name} ${this._share(item.value / all)}`).join(" · ")),
        h(
          "div",
          { class: "segments", role: "img", "aria-label": items.map((item) => `${item.name} ${format(item.value)}`).join(", ") },
          items.map((item) =>
            h("div", { class: "segment", style: { "flex-grow": String(item.value), "flex-basis": "0", background: item.color, color: item.ink } }, item.value / all >= 0.15 ? format(item.value) : ""),
          ),
        ),
        this._keys(...items.map((item) => [h("span", { class: "swatch", style: { background: item.color } }), `${item.name} · ${format(item.value)}`])),
      ],
      {
        info: [this._t("homeEnergyInfo"), euros ? null : this._t("homeEnergyKwh"), this._waterNote(heating)],
        uses: this._uses("consumption", "contract", "heating", "water", "gasPrice"),
        hint: this._heatingHints(heating, "water", "gasPrice"),
      },
    );
  }

  _renderHeatingProfile(heating) {
    if (!heating.profile) return null;
    const values = heating.profile.map((value) => value ?? 0);
    const day = values.reduce((sum, value) => sum + value, 0);
    if (!(day > 0)) return null;
    const peaks = this._peaks(values);
    const tranches = Object.entries(heating.tranches || {});
    const energy = tranches.reduce((sum, [, item]) => sum + item.energy, 0);
    const offPeak =
      !heating.gas && energy > 0 ? tranches.filter(([tranche]) => tranche === "hc" || tranche.endsWith("_hc")).reduce((sum, [, item]) => sum + item.energy, 0) / energy : null;
    this._heatingProfileChart = h("div", { class: "chart" });
    const hourly = heating.days.filter((item) => item.heating > 0).length;
    return this._card(
      this._t("heatingProfile"),
      [
        offPeak !== null ? this._lead(this._share(offPeak), `${this._t("offPeakLead")} · ${peaks}`) : this._lead(this._kwh(day), `${this._t("aDay")} · ${peaks}`),
        this._heatingProfileChart,
        this._keys(
          [h("span", { class: "swatch", style: { background: "var(--ec-s2)" } }), this._t("hourlyKwh")],
          !heating.gas && this._offPeakRanges().length ? [h("span", { class: "swatch", style: { background: "var(--ec-wash)", "box-shadow": "inset 0 0 0 1px var(--ec-axis)" } }), capitalize(this._t("offPeakBand"), this._locale)] : null,
        ),
      ],
      {
        info: [this._t("heatingProfileInfo", { days: this._number(hourly) }), this._waterNote(heating)],
        uses: this._uses("heating", "water", heating.gas ? null : "contract"),
        hint: this._heatingHints(heating, "water"),
      },
    );
  }

  // The weather in the Heating tab: the heating statistics against the outdoor
  // temperature, or the whole consumption when there are none.
  _renderHeatingWeather(heating) {
    const weather = heating.weather;
    if (!heating.has_outdoor || !weather) {
      return this._card(this._t("weather"), [
        h("p", { class: "message" }, this._t("weatherSetup")),
        h("a", { class: "toggle", href: `/config/integrations/integration/${DOMAIN}` }, this._t("weatherOpen")),
      ]);
    }
    if (!weather.days) {
      return this._card(this._t("weather"), h("p", { class: "message" }, this._t("weatherNoData")));
    }
    const days = heating.measured
      ? heating.days.map((day) => ({ date: day.date, color: day.color, temperature: day.temperature, energy: day.heating + (heating.water_split && !heating.water_measured ? day.water : 0) }))
      : (this._insights && this._insights.days) || [];
    const points = days.filter((day) => day.temperature !== null);
    this._heatingWeatherPoints = { weather, days: points };
    this._heatingWeatherChart = points.length ? h("div", { class: "chart" }) : null;
    const base = `${this._number(weather.base)} °C`;
    const perDegree = this._perDegree(heating);
    let lead;
    if (perDegree) {
      const figure = perDegree.cost !== null ? `+${this._kwh(perDegree.energy)} · +${this._money(perDegree.cost)}` : `+${this._kwh(perDegree.energy)}`;
      const context = [this._t("perDegreeBelow", { base }), !heating.measured && weather.heating_share !== null ? this._t("ofTheConsumption", { share: this._share(weather.heating_share) }) : null];
      lead = this._lead(figure, context.filter(Boolean).join(" · "));
    } else {
      lead = h("p", { class: "message" }, this._t(weather.slope === null ? "weatherFewDays" : "noHeating"));
    }
    return this._card(
      this._t("weather"),
      [
        lead,
        this._heatingWeatherChart,
        this._keys(
          [h("span", { class: "dot-key" }), this._t("oneDayKey")],
          perDegree ? [h("span", { class: "line-key", style: { background: "var(--ec-text)" } }), this._t("trend")] : null,
        ),
      ],
      {
        info: [
          perDegree && heating.measured
            ? this._t("heatingWeatherInfo", { base, slope: this._kwh(perDegree.energy), cost: perDegree.cost !== null ? this._money(perDegree.cost) : "—" })
            : this._t("weatherInfo"),
          perDegree ? this._t(weather.base_fitted ? "baseFitted" : "baseDefault", { base }) : null,
          perDegree ? this._curveNote(weather) : null,
          heating.measured ? this._waterNote(heating) : this._estimatedNote(heating),
        ],
        uses: this._uses("outdoor", "heating", heating.measured ? null : "consumption", "water", heating.gas ? "gasPrice" : "contract"),
        hint: this._heatingHints(heating, "statistics", "water"),
      },
    );
  }

  // What a degree costs where the heating starts and on the coldest day seen
  // (the curve's slope there), when the curve makes them differ by a tenth or more.
  _curveNote(weather) {
    const mild = weather.linear;
    const cold = weather.linear + 2 * weather.square * weather.reach;
    if (!(weather.reach > 0) || Math.abs(cold - mild) < 0.1 * Math.max(mild, cold)) return null;
    return this._t("heatingCurve", { mild: this._kwh(mild), cold: this._kwh(cold) });
  }

  // The kWh of heating a day at an outdoor and an indoor temperature, from the
  // weather line: a degree warmer inside counts as a degree colder outside.
  _simEnergy(heating, outdoor, indoor) {
    const weather = heating.weather;
    // The line's flat part is the heating itself, less the hot water estimated
    // inside it; without heating statistics it is the rest of the home.
    const water = heating.water_split && !heating.water_measured ? heating.water_per_day : 0;
    const flat = heating.measured ? weather.intercept - water : 0;
    return Math.max(0, flat + lineHeating(weather, weather.base + (indoor - heating.simulator.indoor) - outdoor));
  }

  _renderSimulator(heating) {
    const sim = heating.simulator;
    const title = this._t("simulator");
    const options = h("a", { class: "toggle", href: `/config/integrations/integration/${DOMAIN}` }, this._t("weatherOpen"));
    let message = null;
    if (!heating.has_outdoor || !heating.weather) message = [this._t("weatherSetup"), options];
    else if (!heating.has_indoor) message = [this._t("simNoIndoor"), options];
    else if (sim.indoor === null) message = [this._t("simNoIndoorData")];
    else if (!this._perDegree(heating)) message = [this._t("simFewDays")];
    if (message) {
      return this._card(title, [h("p", { class: "message" }, message[0]), message[1] || null], {
        info: [this._t("simAbout")],
        uses: this._uses("outdoor", "heating", heating.measured ? null : "consumption", "indoor"),
      });
    }
    // Tenths, so the sliders start on the measured temperatures.
    const tenth = (value) => Math.round(value * 10) / 10;
    if (!this._sim) this._sim = { outdoor: tenth(sim.outdoor ?? 10), indoor: tenth(sim.indoor) };
    const results = h("div", { class: "sim-results", "aria-live": "polite" });
    const update = () => results.replaceChildren(...this._simResults(heating));
    const slider = (key, label, min, max, note) => {
      const output = h("strong", {}, this._degrees(this._sim[key]));
      const id = `sim-${key}`;
      return h(
        "div",
        { class: "sim-slider" },
        h("div", { class: "sim-label" }, h("label", { for: id }, label), output),
        h("input", {
          id,
          type: "range",
          min,
          max,
          step: 0.1,
          value: this._sim[key],
          oninput: (event) => {
            this._sim[key] = Number(event.target.value);
            output.textContent = this._degrees(this._sim[key]);
            update();
          },
        }),
        h("div", { class: "sim-scale" }, h("span", {}, this._degrees(min)), h("span", {}, note), h("span", {}, this._degrees(max))),
      );
    };
    update();
    const low = Math.min(...heating.days.concat(this._insights ? this._insights.days : []).map((day) => day.temperature).filter((value) => value !== null && value !== undefined));
    const highest = Math.max(...heating.days.concat(this._insights ? this._insights.days : []).map((day) => day.temperature).filter((value) => value !== null && value !== undefined));
    return this._card(
      title,
      h(
        "div",
        { class: "sim" },
        h(
          "div",
          { class: "sim-sliders" },
          slider("outdoor", this._t("simOutdoor"), -5, 20, sim.outdoor !== null ? this._t("simPeriodMean", { value: this._degrees(sim.outdoor) }) : ""),
          slider("indoor", this._t("simIndoor"), 15, 23, this._t("simYourIndoor", { value: this._degrees(sim.indoor) })),
        ),
        results,
      ),
      {
        info: [
          this._t("simInfo", { indoor: this._degrees(sim.indoor) }),
          sim.off_peak_share !== null && !heating.gas
            ? this._t("simInfoPrices", { source: this._t(heating.measured ? "simSourceHeating" : "simSourceHome"), share: this._share(sim.off_peak_share) })
            : null,
          Number.isFinite(low) && Number.isFinite(highest) ? this._t("simInfoRange", { low: this._degrees(low), high: this._degrees(highest) }) : null,
          heating.measured ? null : this._estimatedNote(heating),
        ],
        uses: this._uses("outdoor", "indoor", "heating", heating.measured ? null : "consumption", "water", heating.gas ? "gasPrice" : "contract"),
        hint: this._heatingHints(heating, "statistics"),
      },
    );
  }

  // The figures of the simulator for its current temperatures.
  _simResults(heating) {
    const sim = heating.simulator;
    const { outdoor, indoor } = this._sim;
    const energy = this._simEnergy(heating, outdoor, indoor);
    const before = this._simEnergy(heating, outdoor, sim.indoor);
    const share = sim.off_peak_share ?? 0;
    const rows = [];
    if (heating.gas) {
      rows.push({ name: this._t("heating"), energy, cost: sim.gas_price !== null ? energy * sim.gas_price : null });
      if (heating.water_split) {
        const water = heating.water_measured && heating.days.length ? heating.totals.water / heating.days.length : heating.water_per_day;
        rows.push({ name: this._t("hotWater"), energy: water, cost: sim.gas_price !== null ? water * sim.gas_price : null });
      }
    } else if (sim.prices && sim.kind === "tempo") {
      const names = COLORS[this._language];
      for (const color of ["blue", "white", "red"]) {
        const peak = energy * (1 - share) * sim.prices[`${color}_hp`];
        const offPeak = energy * share * sim.prices[`${color}_hc`];
        rows.push({ name: this._t("simDay", { color: names[color].toLowerCase() }), swatch: DAY_FILLS[color], peak, offPeak, cost: peak + offPeak });
      }
    } else if (sim.prices && sim.kind === "hphc") {
      const peak = energy * (1 - share) * sim.prices.hp;
      const offPeak = energy * share * sim.prices.hc;
      rows.push({ name: KINDS[this._language].hphc, peak, offPeak, cost: peak + offPeak });
    } else if (sim.prices && sim.prices.base !== undefined) {
      rows.push({ name: KINDS[this._language].base, cost: energy * sim.prices.base });
    }
    const split = rows.some((row) => row.peak !== undefined);
    const priced = rows.some((row) => row.cost !== null && row.cost !== undefined);
    const lead = this._lead(this._kwh(energy), this._t("simHeatPerDay"));
    const table = rows.length
      ? h(
          "div",
          { class: "table-wrap" },
          h(
            "table",
            {},
            h(
              "thead",
              {},
              h(
                "tr",
                {},
                h("th", {}, ""),
                heating.gas ? h("th", {}, "kWh") : null,
                split ? h("th", {}, this._t("peakShort")) : null,
                split ? h("th", {}, this._t("offPeakShort")) : null,
                priced ? h("th", {}, this._t("simPerDay")) : null,
                priced ? h("th", {}, this._t("simMonth")) : null,
              ),
            ),
            h(
              "tbody",
              {},
              rows.map((row) =>
                h(
                  "tr",
                  {},
                  h("td", {}, row.swatch ? h("span", { class: "swatch", style: { background: row.swatch } }) : null, row.name),
                  heating.gas ? h("td", { class: "sub" }, this._number(row.energy, 1)) : null,
                  split ? h("td", { class: "sub" }, this._money(row.peak)) : null,
                  split ? h("td", { class: "sub" }, this._money(row.offPeak)) : null,
                  priced ? h("td", {}, row.cost !== null ? h("strong", {}, this._money(row.cost)) : "—") : null,
                  priced ? h("td", { class: "sub" }, row.cost !== null ? this._money(row.cost * 30, 0) : "—") : null,
                ),
              ),
            ),
          ),
        )
      : null;
    const change = energy - before;
    let delta;
    if (Math.abs(indoor - sim.indoor) < 0.01) {
      delta = this._t("simCurrent");
    } else {
      const sign = change >= 0 ? "+" : "−";
      const first = rows[0];
      const ratio = first && first.cost !== null && first.cost !== undefined && energy > 0 ? first.cost / energy : null;
      delta =
        ratio !== null
          ? this._t("simDelta", { cost: `${sign}${this._money(Math.abs(change) * ratio)}`, temperature: this._degrees(sim.indoor), energy: `${sign}${this._kwh(Math.abs(change))}` })
          : this._t("simDeltaEnergy", { energy: `${sign}${this._kwh(Math.abs(change))}`, temperature: this._degrees(sim.indoor) });
    }
    return [lead, table, h("p", { class: "sub sim-delta" }, delta)];
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
