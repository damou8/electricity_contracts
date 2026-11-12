# Electricity Contracts

*[English version below](#english)*

Une intégration Home Assistant qui valorise votre consommation électrique heure par heure selon plusieurs contrats français à la fois : ce que vous payez vraiment, ce qui pèse sur la facture, et ce que vous auriez payé avec une autre offre. Tout se lit dans la page **Contrats** du menu latéral.

Elle lit la consommation horaire déjà présente dans Home Assistant, par exemple la statistique `linky:…` qu'importe l'[App Linky](https://github.com/bokub/ha-linky). Elle valorise ensuite chaque heure selon chacun des contrats que vous ajoutez :

- **Base**, **HP/HC** avec vos propres plages d'heures creuses (à la demi-heure, week-end en heures creuses ou non) et **Tempo** ;
- aux **tarifs réglementés** (Tarif Bleu), avec leur historique téléchargé depuis data.gouv.fr, ou à des **prix que vous fixez vous-même**, période par période ;
- avec les dates où chaque contrat était en vigueur, pour que le coût réel suive votre véritable historique de contrats.

Le calcul est fait par la bibliothèque [elec-tariffs](https://github.com/damou8/elec-tariffs).

> **État : en développement.** La page Contrats remplace les comparaisons et les capteurs de la version 0.1 : voir [Mise à niveau depuis la 0.1](#mise-à-niveau-depuis-la-01).

## Installation

1. Dans HACS, ouvrez le menu → **Dépôts personnalisés** et ajoutez `https://github.com/damou8/electricity_contracts` avec le type **Intégration**.
2. Installez **Electricity Contracts**, puis redémarrez Home Assistant.
3. Allez dans **Paramètres → Appareils et services → Ajouter une intégration → Electricity Contracts**.

Home Assistant 2026.10 ou plus récent. L'intégration a besoin du recorder.

## La page Contrats

L'intégration ajoute la page **Contrats** au menu latéral. Si vous avez plusieurs sources de consommation, choisissez celle à afficher en haut de la page. Les chiffres portent sur la période choisie : le mois, la saison (de septembre à août), l'année, les 12 derniers mois ou des dates.

- **Suivi** :
  - le contrat en cours, ses prix et leurs hausses passées ;
  - le prix du kWh maintenant et sur les prochaines 24 h, avec le moment le moins cher ;
  - ce que demain devrait coûter et, pour Tempo, sa couleur ;
  - le budget de la saison : ce qui est dépensé, ce qui reste prévu jusqu'au 31 août et, pour Tempo, les jours rouges et blancs restants ;
  - sur la période : le coût réel, la consommation, le prix moyen du kWh, la part des heures pleines rouges pour Tempo, et l'évolution mois par mois avec la température extérieure.
- **Comprendre** : la journée type, la part des heures pleines selon la couleur Tempo, le talon (ce qui tourne en permanence), la consommation selon la température, le calendrier des jours, les jours les plus chers et la part de chaque tranche dans les kWh et dans les euros.
- **Comparer** : chaque contrat appliqué à votre consommation réelle, sur les mêmes heures, du moins cher au plus cher, puis la facture détaillée du contrat choisi. Un contrat à vos prix qui n'en a pas encore attend en bas du classement, avec un lien pour les ajouter.

Le budget de la saison et le coût de demain sont des estimations, d'après vos jours passés. Rien d'estimé n'est écrit dans les statistiques.

## Configuration

### Source de consommation

Choisissez la statistique horaire d'énergie de votre compteur. Il faut une énergie (Wh, kWh…) avec un total cumulé et des données, comme la statistique qu'importe l'App Linky.

Vous pouvez la changer plus tard avec **Reconfigurer**, par exemple après un changement de compteur. Toutes les statistiques sont alors recalculées.

### Contrats

Sur la page de l'intégration, **Ajouter un contrat**, en deux étapes :

| Champ | Signification |
| --- | --- |
| Type de contrat | Base (un seul prix), heures pleines – heures creuses (deux prix selon l'heure) ou Tempo (six prix selon l'heure et la couleur du jour). |
| Prix | Les tarifs réglementés, téléchargés avec leur historique et suivis à chaque hausse, ou vos propres prix, saisis ensuite en périodes de prix. |
| Puissance souscrite | Écrite sur votre facture ; 6 kVA par défaut. Refusée si ce type de contrat n'a pas de tarif réglementé à cette puissance. |
| Nom | Proposé d'après le type et la puissance, modifiable. Deux contrats ne peuvent pas porter le même nom. |
| Heures creuses | Pour HP/HC : 22 h – 6 h, 23 h – 7 h, 22 h 30 – 6 h 30, ou **Autres plages…** pour saisir les vôtres, une par case, à l'heure ou à la demi-heure (`01:00-07:00`, `12:30-14:30`). Elles figurent sur votre facture et dans votre espace Enedis. |
| Heures creuses tout le week-end | Pour les offres HP/HC où samedis et dimanches sont facturés en heures creuses toute la journée. |
| Période d'activité | Facultative : le premier et le dernier jour facturés avec ce contrat, le dernier vide s'il est toujours en vigueur. Laissez-la vide pour un contrat qui sert seulement à comparer. Deux contrats ne peuvent pas être en vigueur le même jour. |

**Modifier le contrat** change tout sauf le type : pour un autre type, ajoutez un autre contrat.

### Périodes de prix

Pour un contrat à vos prix, **Ajouter une période de prix** pour chaque période tarifaire :
- le premier et le dernier jour (vide si les prix sont toujours en vigueur) ;
- l'abonnement annuel ;
- le prix au kWh de chaque tranche, TTC.

Le contrat est comparé dès que ses prix couvrent les jours mesurés. Pour comparer une offre sur tout votre historique, sa première période peut commencer avant que l'offre existe. Les périodes d'un même contrat ne peuvent pas se chevaucher. Supprimer un contrat supprime ses périodes de prix.

### Options

Dans la fenêtre **Configurer** de l'intégration :
- **Température extérieure** (facultatif) : un capteur de température qui garde des statistiques. Il relie la consommation à la météo dans l'onglet Comprendre, et ajoute la température au graphique d'évolution.
- **Secours Tempo : API officielle RTE** (section repliée) : voir ci-dessous.

### Compte RTE (facultatif)

Les couleurs Tempo viennent du calendrier public de RTE, sans compte. S'il ne fonctionne plus, l'intégration peut utiliser l'API officielle de RTE. Dans la fenêtre **Configurer** de l'intégration, section **Secours Tempo : API officielle RTE**, saisissez l'ID client et le secret d'une application créée gratuitement :

1. Créez un compte sur [data.rte-france.com](https://data.rte-france.com).
2. Ouvrez l'API [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) et choisissez **S'abonner à l'API** : cela crée une application.
3. Copiez son ID client et son secret.

Les identifiants sont vérifiés à l'enregistrement. Laissez les deux champs vides pour n'utiliser que le calendrier public.

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

## Statistiques

Pour chaque contrat, l'intégration écrit des statistiques horaires :

| Statistique | Contenu |
| --- | --- |
| `<contrat> énergie <tranche>` | kWh consommés dans chaque tranche (Bleu HC, Rouge HP, HP…). |
| `<contrat> coût <tranche>` | Coût de cette énergie. |
| `<contrat> abonnement` | Part fixe annuelle, répartie sur chaque heure de l'année. |
| `<contrat> coût total` | Énergie et abonnement. |

Si au moins un contrat a une période de vigueur, deux statistiques suivent votre contrat réel jour par jour :
- **Coût réel** : la part variable ;
- **Abonnement réel** : la part fixe.

Elles commencent à la première heure de consommation et suivent la source au fil des imports. Les noms sont dans la langue du serveur.

### Tableau de bord Énergie

Dans la configuration du tableau de bord Énergie, ouvrez votre consommation électrique. Choisissez de suivre les coûts avec une entité ou une statistique de coût total, puis sélectionnez la statistique **Coût réel**.

Préférez-la au capteur Prix actuel : la consommation Linky arrive le lendemain, et le tableau la valoriserait au prix du moment de l'import.

### Comparer des contrats sur un graphique

Une carte `statistics-graph` avec les coûts totaux de vos contrats montre, pour la période choisie avec le sélecteur de dates du tableau Énergie, ce qu'aurait coûté chaque contrat :

```yaml
type: statistics-graph
title: Coût selon le contrat
chart_type: bar
period: month
stat_types: [change]
energy_date_selection: true
entities:
  - electricity_contracts:linky_…_xxxxxxxx_cost
  - electricity_contracts:linky_…_yyyyyyyy_cost
```

Dans l'éditeur de la carte, cherchez les statistiques par leur nom (« Tempo coût total »…).

### Quand les statistiques sont recalculées

Les statistiques ne font que s'allonger, heure par heure. Celles d'un contrat sont effacées et recalculées depuis la première heure quand :
- ses réglages ou ses prix changent ;
- un nouveau tarif réglementé est publié.

Le coût réel est recalculé quand une période de vigueur change. Tout est recalculé quand :
- la source change ;
- l'App Linky réimporte un historique différent.

Une heure dont la couleur Tempo ou le prix n'est pas encore connu attend : le calcul reprend dès qu'ils arrivent.

L'action **Electricity Contracts : Recalculer** (`electricity_contracts.recompute`, champ `config_entry_id`) efface et recalcule toutes les statistiques d'une source.

### Action Comparer

L'action `electricity_contracts.compare` renvoie le détail d'une période quelconque, tranche par tranche. Par exemple, dans un script :

```yaml
- action: electricity_contracts.compare
  data:
    config_entry_id: <id de l'entrée>
    start: "2026-04-01"
    end: "2026-04-30"
    contracts: [Tempo, Base]  # facultatif : tous par défaut
  response_variable: comparaison
```

La réponse contient, pour chaque contrat, les kWh et le coût de chaque tranche, la part énergie, l'abonnement, le total et le prix au kWh. Elle donne aussi le coût réel, le meilleur contrat et l'économie possible.

## Mise à jour des données

L'intégration vérifie ses sources toutes les heures et ne télécharge que ce qui manque :

- **Tarifs réglementés** : une fois par jour, pour chaque type de contrat et puissance utilisés.
- **Couleurs Tempo** :
  - au premier démarrage, toutes les saisons depuis la première heure de consommation ;
  - puis la couleur du lendemain dès que RTE la publie (vers 11 h), redemandée toutes les heures jusqu'à sa parution ;
  - les couleurs passées sont gardées et jamais redemandées.

Rien n'est téléchargé pour un type de contrat que vous n'avez pas ajouté.

Les heures sont valorisées à chaque vérification, donc au plus une heure après l'import de l'App Linky.

## Confidentialité

- La consommation ne quitte jamais Home Assistant. L'intégration ne télécharge que des tarifs et des couleurs Tempo publics.
- Les diagnostics masquent l'identifiant de la statistique et le titre de l'entrée, qui contiennent le numéro du compteur, ainsi que les identifiants RTE.

## Historique quotidien

Sans courbe de charge, le Linky ne remonte qu'une consommation par jour. L'App Linky l'enregistre en une ligne à minuit, et c'est souvent le cas de l'historique antérieur à l'activation de la courbe de charge.

Ces totaux quotidiens ne sont pas valorisés : on ne sait pas comment ils se répartissent entre heures creuses et heures pleines, et l'intégration ne fait pas d'estimation. Les statistiques commencent à la première heure mesurée. Une heure qui manque dans la source reste vide.

Une statistique qui n'a que des valeurs quotidiennes est refusée à la configuration. Activez la courbe de charge (consommation horaire) dans votre espace Enedis et dans l'App Linky.

## Limites connues

- Chaque heure est partagée en deux demi-heures de même consommation. Une plage d'heures creuses qui commence à la demi-heure n'est donc suivie qu'approximativement dans cette heure.
- Les prix dynamiques (spot), les offres indexées sur le tarif réglementé et les jours spéciaux d'autres offres (Zen Flex…) ne sont pas encore pris en charge.
- Le client de l'API officielle de RTE n'a pas encore été testé sur l'API réelle.
- La page Contrats est en français ou en anglais, selon la langue de votre profil.

## Dépannage

- **La configuration réessaie sans cesse** : les tarifs ou les couleurs Tempo dont un contrat a besoin n'ont jamais pu être téléchargés. L'intégration réessaie toute seule ; l'erreur figure dans les journaux.
- **Réparation « Les couleurs Tempo ne se mettent plus à jour »** : le calendrier public de RTE échoue depuis deux jours. Ajoutez des identifiants RTE (voir plus haut) pour que l'API officielle prenne le relais.
- **Réparation « RTE refuse les identifiants »** : vérifiez l'application sur data.rte-france.com et saisissez à nouveau les identifiants, ou effacez-les.
- **La page affiche « Préparation des calculs… »** : la source se recharge, au démarrage ou après un changement de contrat. Valoriser un nouveau contrat sur tout l'historique prend parfois quelques minutes ; la page se met à jour toute seule. Si cela dure, la page de l'intégration indique l'erreur.
- **Réparation « *contrat* n'a pas de prix pour le … »** : aucune période de prix de ce contrat ne couvre ce jour. Ajoutez la période qui manque.
- **Un contrat s'arrête à une date** : les comparaisons s'arrêtent avec lui. Ses diagnostics indiquent s'il attend une couleur ou un prix.
- **Journaux de débogage** : activez-les depuis le menu de l'intégration ; ils incluent la bibliothèque `elec_tariffs`.

## Désinstallation

1. **Paramètres → Appareils et services → Electricity Contracts**, ouvrez le menu de l'entrée et choisissez **Supprimer**. Ses statistiques, son cache et ses réparations sont supprimés avec elle, et la page Contrats quitte le menu avec la dernière source.
2. Pour retirer aussi le code, désinstallez-la dans HACS et redémarrez Home Assistant.

## Licence

[MIT](LICENSE)

---

## English

A Home Assistant integration that costs your hourly electricity consumption under several French contracts at once: what you actually pay, what weighs on the bill, and what you would have paid with another offer. It all shows on the **Contracts** page of the sidebar.

It reads the hourly consumption already in Home Assistant, for example the `linky:…` statistic the [Linky app](https://github.com/bokub/ha-linky) imports. It then values every hour under each contract you add:

- **Base**, **HP/HC** with your own off-peak ranges (to the half hour, weekends off-peak or not) and **Tempo**;
- with the **regulated prices** (Tarif Bleu) and their history, downloaded from data.gouv.fr, or with **prices you set yourself**, period by period;
- with the dates each contract was in force, so the actual cost follows your real contract history.

The calculation is done by the [elec-tariffs](https://github.com/damou8/elec-tariffs) library.

> **Status: in development.** The Contracts page replaces the comparisons and the sensors of version 0.1: see [Upgrading from 0.1](#upgrading-from-01).

### Installation

1. In HACS, open the menu → **Custom repositories** and add `https://github.com/damou8/electricity_contracts` with the type **Integration**.
2. Install **Electricity Contracts**, then restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → Electricity Contracts**.

Home Assistant 2026.10 or later. The integration needs the recorder.

### The Contracts page

The integration adds the **Contracts** page to the sidebar. With several consumption sources, pick one at the top of the page. Figures cover the chosen period: the month, the season (September to August), the year, the last 12 months or dates of your choice.

- **Overview**:
  - the contract in force, its prices and their past rises;
  - the price of a kWh now and over the next 24 hours, with the cheapest time;
  - what tomorrow should cost and, for Tempo, its color;
  - the season budget: what is spent, what is still expected until 31 August and, for Tempo, the red and white days left;
  - over the period: the actual cost, the consumption, the average price of a kWh, the share of red peak hours for Tempo, and the month-by-month trend with the outdoor temperature.
- **Understand**: the typical day, the share of peak hours by Tempo color, the baseload (what runs all the time), consumption against temperature, the calendar of days, the most expensive days, and each tranche's share of kWh and of euros.
- **Compare**: each contract applied to your actual consumption, over the same hours, from cheapest to dearest, then the detailed bill of the chosen contract. A contract with your own prices that has none yet waits at the bottom of the ranking, with a link to add them.

The season budget and tomorrow's cost are estimates, from your past days. Nothing estimated is written to the statistics.

### Configuration

**Consumption source**: choose the hourly energy statistic of your meter. It must be an energy (Wh, kWh…) with a running total and some data, like the statistic the Linky app imports. **Reconfigure** changes it later, for example after a meter change. Every statistic is then computed again.

**Contracts**: on the integration's page, **Add contract**, in two steps.

| Field | Meaning |
| --- | --- |
| Kind of contract | Base (one price), peak and off-peak hours (two prices, by the hour) or Tempo (six prices, by the hour and the color of the day). |
| Prices | The regulated prices, downloaded with their history and followed at each change, or your own prices, entered afterwards as price periods. |
| Subscribed power | Written on your bill; 6 kVA by default. Refused when this kind of contract has no regulated price at that power. |
| Name | Suggested from the kind and the power, and can be changed. Two contracts can't have the same name. |
| Off-peak hours | For HP/HC: 22:00 – 6:00, 23:00 – 7:00, 22:30 – 6:30, or **Other hours…** to type yours, one per field, on whole or half hours (`01:00-07:00`, `12:30-14:30`). They are on your bill and in your Enedis account. |
| Off-peak all weekend | For HP/HC offers where Saturdays and Sundays are billed off-peak all day. |
| Days in force | Optional: the first and last day you were billed under this contract, the last one empty while it is in force. Leave them empty for a contract you only want to compare. Two contracts can't be in force on the same day. |

**Change contract** changes everything but the kind: for another kind, add another contract.

**Price periods**: for a contract with your own prices, **Add price period** for each period of prices:
- the first and last day (empty if still in force);
- the yearly subscription;
- the price of each tranche per kWh, taxes included.

The contract is compared once its prices cover the measured days. To compare an offer over your whole history, its first period can start before the offer existed. Periods of one contract can't overlap. Deleting a contract deletes its price periods.

**Options**, in the integration's **Configure** dialog:
- **Outdoor temperature** (optional): a temperature sensor that keeps statistics. It relates the consumption to the weather in the Understand tab, and adds the temperature to the trend chart.
- **Tempo backup: RTE's official API** (a collapsed section): see below.

**RTE account (optional)**: Tempo colors come from RTE's public calendar, which needs no account. If it stops working, the integration can use RTE's official API instead. In the integration's **Configure** dialog, section **Tempo backup: RTE's official API**, enter the client ID and secret of an application created for free:
1. Create an account on [data.rte-france.com](https://data.rte-france.com).
2. Open the [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) API and choose **S'abonner à l'API**: this creates an application.
3. Copy its client ID and secret.

The credentials are checked when saved.

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

### Compare action

The action `electricity_contracts.compare` (`config_entry_id`, `start`, `end`, optional `contracts`) compares the contracts over any period and returns, for each one, the kWh and cost of each tranche, the energy part, the subscription, the total and the price per kWh. The response also gives the actual cost, the best contract and the possible saving.

### Statistics

For each contract the integration writes hourly statistics:
- `<contract> energy <tranche>` (kWh);
- `<contract> cost <tranche>`;
- `<contract> subscription`: the yearly fixed part spread over every hour of the year;
- `<contract> total cost`.

If at least one contract has an activity period, two statistics follow your actual contract day by day:
- **Actual cost**: the variable part;
- **Actual subscription**: the fixed part.

Names follow the server language.

- **Energy dashboard**: in the settings of your grid consumption, track the costs with a total cost entity or statistic and pick **Actual cost**. Prefer it to the Current price sensor: Linky consumption arrives the next day, and the dashboard would cost it at the price of the time of the import.
- **Comparing contracts**: a `statistics-graph` card with the total costs of your contracts, `stat_types: [change]` and `energy_date_selection: true`, shows what each contract would have cost over the period chosen in the Energy date picker.
- **Recomputing**: statistics only grow, hour by hour. A contract's statistics are cleared and written again when:
  - its settings or prices change;
  - a new regulated price is published.

  The actual cost is written again when an activity period changes. Everything is written again when:
  - the source changes;
  - the Linky app imports a different history.

  An hour whose Tempo color or price isn't known yet waits. The action `electricity_contracts.recompute` (field `config_entry_id`) writes every statistic of a source again.

### Data updates

The integration checks its sources every hour and downloads only what is missing:
- **regulated prices**: once a day per contract kind and power in use;
- **Tempo colors**: at the first setup, every season since the first hour of consumption; then tomorrow's color once RTE publishes it (around 11:00), retried hourly until it is out;
- past colors are kept and never asked again.

Hours are costed at each check, at most an hour after the Linky import.

### Daily history

Without a load curve, a Linky meter only reports one value a day. The Linky app writes it as one row at midnight, which is often the case for the history older than the load curve.

Daily totals aren't costed: how they split between off-peak and peak hours isn't known, and the integration doesn't estimate it. Statistics start at the first measured hour. An hour missing from the source stays empty.

A statistic with only daily values is refused at setup: enable the load curve (hourly consumption) in your Enedis account and in the Linky app.

### Privacy, limitations, troubleshooting, removal

- The consumption never leaves Home Assistant. Diagnostics hide the statistic ID, the entry title (both contain the meter number) and the RTE credentials.
- Hours are split into two half hours with the same consumption. Spot prices, offers indexed on the regulated prices and special days of other offers aren't supported yet. The official RTE API client hasn't been tested against the live API yet. The Contracts page is in French or English, following your profile's language.
- **Repairs**:
  - "Tempo colors can't be updated": add RTE credentials;
  - "RTE refuses the credentials": enter them again or clear them;
  - "*contract* has no price for …": no price period of this contract covers that day; add the missing one.

  A contract that stops at a date stops the comparisons with it: its diagnostics tell whether it waits for a color or a price.
- **"Preparing the figures…"** on the page: the source is reloading, at startup or after a change of contract. Costing a new contract over the whole history can take a few minutes; the page updates by itself. If it lasts, the integration's page shows the error.
- **Removal**: delete the entry from **Settings → Devices & services → Electricity Contracts**. Its statistics, cache and repairs go with it, and the Contracts page leaves the sidebar with the last source. Then uninstall it in HACS and restart.

License: [MIT](LICENSE)
