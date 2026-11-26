# Electricity Contracts

*[English version below](#english)*

Une intégration Home Assistant qui valorise votre consommation électrique heure par heure selon plusieurs contrats français à la fois : ce que vous payez vraiment, ce qui pèse sur la facture, et ce que vous auriez payé avec une autre offre.

- **Base**, **HP/HC** (vos plages, à la demi-heure) et **Tempo**, aux **tarifs réglementés** avec leur historique ou à **vos propres prix** ;
- le **coût réel** suit les dates de vos contrats, sur la consommation horaire déjà dans Home Assistant (par exemple la statistique de l'[App Linky](https://github.com/bokub/ha-linky)) ;
- tout se lit dans la page **Contrats** du menu latéral.

![La page Contrats, onglet Suivi](https://raw.githubusercontent.com/damou8/electricity_contracts/main/docs/images/overview.webp)

*Captures faites sur des données de démonstration.*

## Installation

1. Dans HACS, ouvrez le menu → **Dépôts personnalisés** et ajoutez `https://github.com/damou8/electricity_contracts` avec le type **Intégration**.
2. Installez **Electricity Contracts**, puis redémarrez Home Assistant.
3. Allez dans **Paramètres → Appareils et services → Ajouter une intégration → Electricity Contracts**.

Home Assistant 2026.10 ou plus récent. L'intégration a besoin du recorder.

Ensuite :
1. choisissez la statistique horaire de votre compteur, ou laissez vide sans compteur (prix, Tempo et chauffage seulement) ;
2. sur la page de l'intégration, **Ajouter un contrat** pour chacun de vos contrats, passés ou à comparer ;
3. ouvrez **Contrats** dans le menu latéral.

Le détail des champs et des options est dans [Configuration](docs/configuration.md).

## La page Contrats

Choisissez la période en haut de chaque onglet : mois, saison (septembre à août), année, 12 derniers mois ou dates.

- **Suivi** : le contrat en cours et ses prix, le prix du kWh maintenant et sur 24 h, ce que demain devrait coûter, le budget de la saison (avec les jours Tempo rouges et blancs restants), puis le coût réel, la consommation et le prix moyen de la période, mois par mois avec la température extérieure, et la part du chauffage et de l'eau chaude quand leurs statistiques électriques sont renseignées.
- **Comprendre** : journée type, heures pleines selon la couleur Tempo, talon, consommation selon la température, calendrier, jours les plus chers, part de chaque tranche dans les kWh et les euros.
- **Chauffage** (avec une température extérieure, d'un capteur ou d'Open-Meteo, ou des statistiques de chauffage) : coût et consommation du chauffage, sa part dans la maison, ce que coûte un degré de moins, chauffage par jour avec la température, répartition par radiateur et par tranche, journée type, lien avec la météo, et un simulateur de réglage (température dehors et dedans) qui donne le prix d'une journée à chaque tranche du contrat. Une étiquette dans le style du DPE classe le logement de A à G, en énergie et en climat, d'après ce que le chauffage, l'eau chaude et les auxiliaires ont consommé sur les 12 derniers mois, ramené à la consigne du DPE (19 °C le jour, 16 °C la nuit) d'après vos thermomètres intérieurs ou votre consigne. Avant vos statistiques de chauffage, un chauffage électrique est estimé à partir des jours du Linky et de la température extérieure ; la surface, le coefficient de l'électricité, les parts estimées et la consigne se règlent dans son (i). Électricité ou gaz, avec ou sans eau chaude. La carte météo de l'onglet Comprendre y est déplacée.
- **Comparer** : chaque contrat appliqué à votre consommation réelle, sur les mêmes heures, du moins cher au plus cher, et la facture détaillée du contrat choisi.

| Comprendre | Comparer | Sur mobile |
| --- | --- | --- |
| ![Onglet Comprendre](https://raw.githubusercontent.com/damou8/electricity_contracts/main/docs/images/understand.webp) | ![Onglet Comparer](https://raw.githubusercontent.com/damou8/electricity_contracts/main/docs/images/compare.webp) | ![Onglet Suivi sur mobile](https://raw.githubusercontent.com/damou8/electricity_contracts/main/docs/images/mobile.webp) |

Le budget de la saison et le coût de demain sont des estimations, d'après vos jours passés. Dans l'onglet Chauffage, le chauffage est estimé sans statistiques de chauffage, et l'eau chaude quand elle est comptée avec lui. Quand la période commence avant vos statistiques de chauffage électrique, les jours d'avant sont estimés en kWh d'après le Linky et la température extérieure, et hachurés dans les graphiques ; les coûts, les radiateurs, les tranches et la journée type restent mesurés. Une période entièrement avant vos statistiques est estimée comme un logement qui n'en a pas. Dans l'étiquette, les auxiliaires sont toujours une part estimée, et l'eau chaude aussi quand elle n'est ni mesurée ni estimée. Rien d'estimé n'est écrit dans les statistiques.

## Capteurs

L'appareil **Contrats d'électricité** a deux capteurs, pour vos automatisations :

| Capteur | Valeur |
| --- | --- |
| Prix actuel | Le prix du kWh à cet instant selon le contrat en vigueur, hors abonnement, en €/kWh. |
| Tranche actuelle | `base`, `hp` ou `hc`, et pour Tempo la couleur avec la tranche : `blue_hc`, `white_hp`, `red_hp`… |

Ils changent à l'heure ou à la demi-heure où la tranche change. Ils sont inconnus sans contrat en vigueur, ou si la couleur Tempo du jour n'est pas connue.

Par exemple, pour couper le chauffe-eau en heures pleines rouges :

```yaml
triggers:
  - trigger: state
    entity_id: sensor.contrats_d_electricite_tranche_actuelle
    to: red_hp
actions:
  - action: switch.turn_off
    target:
      entity_id: switch.chauffe_eau
```

## Mise à niveau depuis la 0.1

Les comparaisons, leurs capteurs et les capteurs de la source (coût réel du dernier jour, prix réel du mois, contrat actuel, dernière heure de données) sont supprimés à la mise à niveau : la page Contrats les remplace. Les statistiques restent. Dans vos automatisations, utilisez les deux capteurs ci-dessus ou l'action `electricity_contracts.compare`.

## Documentation

- [Configuration](docs/configuration.md) : source, contrats, périodes de prix, options, compte RTE.
- [Statistiques et actions](docs/statistics.md) : statistiques écrites, tableau Énergie, graphiques, recalculs, action `compare`, mise à jour des données, historique quotidien.
- [Limites, dépannage et désinstallation](docs/troubleshooting.md).

## Confidentialité

La consommation ne quitte jamais Home Assistant : l'intégration ne télécharge que des tarifs et des couleurs Tempo publics, et la météo d'Open-Meteo si vous l'activez (elle reçoit alors la position de la maison, arrondie à environ 10 km). Les diagnostics masquent le numéro du compteur et les identifiants RTE.

## Licence

[MIT](LICENSE)

---

## English

A Home Assistant integration that costs your hourly electricity consumption under several French contracts at once: what you actually pay, what weighs on the bill, and what you would have paid with another offer.

- **Base**, **HP/HC** (your own ranges, to the half hour) and **Tempo**, at the **regulated prices** with their history or at **your own prices**;
- the **actual cost** follows your contracts' dates, on the hourly consumption already in Home Assistant (for example the [Linky app](https://github.com/bokub/ha-linky)'s statistic);
- it all shows on the **Contracts** page of the sidebar (screenshots above, in French, on demo data).

### Installation

1. In HACS, open the menu → **Custom repositories** and add `https://github.com/damou8/electricity_contracts` with the type **Integration**.
2. Install **Electricity Contracts**, then restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → Electricity Contracts**.

Home Assistant 2026.10 or later. The integration needs the recorder.

Then:
1. choose the hourly statistic of your meter, or leave it empty without a meter (prices, Tempo and heating only);
2. on the integration's page, **Add contract** for each of your contracts, past ones or ones to compare;
3. open **Contracts** in the sidebar.

Every field and option is described in [Configuration](docs/configuration.md#english).

### The Contracts page

Pick the period at the top of each tab: month, season (September to August), year, last 12 months or dates.

- **Overview**: the contract in force and its prices, the price of a kWh now and over 24 hours, what tomorrow should cost, the season budget (with the red and white Tempo days left), then the period's actual cost, consumption and average price, month by month with the outdoor temperature, and the share of heating and hot water when their electric statistics are set.
- **Understand**: typical day, peak hours by Tempo color, baseload, consumption against temperature, calendar, most expensive days, each tranche's share of kWh and euros.
- **Heating** (with an outdoor temperature, from a sensor or Open-Meteo, or heating statistics): what heating cost and used, its share of the home, what a degree colder costs, heating by day with the temperature, split by heater and by tranche, typical day, link with the weather, and a setting simulator (outdoor and indoor temperature) giving the price of a day at each tranche of the contract. A label in the style of the French DPE rates the home from A to G, in energy and climate, from what heating, hot water and auxiliaries used over the last 12 months, moved to the DPE's setpoint (19 °C by day, 16 °C at night) from your indoor thermometers or your setpoint. Before your heating statistics, electric heating is estimated from the Linky's days and the outdoor temperature; the living area, the electricity coefficient, the estimated shares and the setpoint are set in its (i). Electricity or gas, with or without hot water. The Understand tab's weather card moves there.
- **Compare**: each contract applied to your actual consumption, over the same hours, from cheapest to dearest, and the detailed bill of the chosen one.

The season budget and tomorrow's cost are estimates, from your past days. In the Heating tab, heating is estimated without heating statistics, and hot water when it is counted with the heating. When the period starts before your electric heating statistics, the days before are estimated in kWh from the Linky and the outdoor temperature, and hatched in the charts; costs, heaters, tranches and the typical day stay measured. A period wholly before your statistics is estimated like a home without them. In the label, the auxiliaries are always an estimated share, and so is hot water when it is neither measured nor estimated. Nothing estimated is written to the statistics.

### Sensors

The **Electricity contracts** device has two sensors, for your automations:
- **Current price**: the price of a kWh right now under the contract in force, subscription excluded, in €/kWh;
- **Current tranche**: `base`, `hp` or `hc`, and for Tempo the color with the tranche: `blue_hc`, `white_hp`, `red_hp`…

They change on the hour or half hour when the tranche does. They are unknown without a contract in force, or when the day's Tempo color isn't known.

For example, to turn the water heater off during red peak hours:

```yaml
triggers:
  - trigger: state
    entity_id: sensor.electricity_contracts_current_tranche
    to: red_hp
actions:
  - action: switch.turn_off
    target:
      entity_id: switch.water_heater
```

### Upgrading from 0.1

The comparisons, their sensors and the source's sensors (actual cost of the last day, actual price this month, current contract, last hour of data) are removed by the upgrade: the Contracts page replaces them. The statistics stay. In your automations, use the two sensors above or the `electricity_contracts.compare` action.

### Documentation

- [Configuration](docs/configuration.md#english): source, contracts, price periods, options, RTE account.
- [Statistics and actions](docs/statistics.md#english): statistics written, Energy dashboard, charts, recomputing, `compare` action, data updates, daily history.
- [Limitations, troubleshooting and removal](docs/troubleshooting.md#english).

### Privacy

The consumption never leaves Home Assistant: the integration only downloads public prices and Tempo colors, and Open-Meteo weather if you turn it on (Open-Meteo then gets the home's location, rounded to about 10 km). Diagnostics hide the meter number and the RTE credentials.

License: [MIT](LICENSE)
