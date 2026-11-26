# Configuration

*[English below](#english)*

La page de l'intégration a deux boutons : **Ajouter un contrat d'électricité** et **Ajouter un contrat de gaz**. Chaque contrat dit son énergie sous son nom. Le crayon d'un contrat le modifie, et la roue dentée **Configurer** règle les températures, le chauffage et le secours Tempo.

## Source de consommation

Choisissez la statistique horaire d'énergie de votre compteur. Il faut une énergie (Wh, kWh…) avec un total cumulé et des données, comme la statistique qu'importe l'App Linky.

Vous pouvez la changer plus tard avec **Reconfigurer**, par exemple après un changement de compteur. Toutes les statistiques sont alors recalculées.

**Sans compteur**, laissez le champ vide : la source s'appelle « Sans compteur » (une seule possible). Rien n'est valorisé, mais la page Contrats montre le contrat en cours, le prix du kWh maintenant et sur 24 h, la couleur Tempo de demain et les jours rouges et blancs restants. Avec des statistiques de chauffage (un compteur de gaz, des radiateurs), l'onglet Chauffage fonctionne aussi, sans la part dans la maison ; sa période suit ces statistiques. Les onglets Comprendre et Comparer ont besoin du compteur. Reconfigurer avec une statistique les fait apparaître.

## Contrats d'électricité

**Ajouter un contrat d'électricité** demande d'abord ce qu'est le contrat, puis son nom et ses dates, puis ses premiers prix s'ils sont saisis à la main, ou son capteur.

| Champ | Signification |
| --- | --- |
| Type de contrat | Base (un seul prix), heures pleines – heures creuses (deux prix selon l'heure) ou Tempo (six prix selon l'heure et la couleur du jour). |
| Prix | Les **tarifs réglementés**, téléchargés avec leur historique et suivis à chaque hausse. **Mes propres prix**, saisis par périodes. Ou le **prix d'un capteur**, lu heure par heure (voir plus bas). |
| Puissance souscrite | Écrite sur votre facture ; 6 kVA par défaut. Elle est refusée si ce type de contrat n'a pas de tarif réglementé à cette puissance. |
| Nom | Proposé d'après le type et la puissance, modifiable. Deux contrats d'électricité ne peuvent pas porter le même nom. |
| Heures creuses | Pour HP/HC : 22 h – 6 h, 23 h – 7 h, 22 h 30 – 6 h 30, ou **Autres plages…** pour saisir les vôtres, une par case, à l'heure ou à la demi-heure (`01:00-07:00`, `12:30-14:30`). Elles figurent sur votre facture et dans votre espace Enedis. |
| Heures creuses tout le week-end | Pour les offres HP/HC où samedis et dimanches sont facturés en heures creuses toute la journée. |
| Période d'activité | Facultative : le premier et le dernier jour facturés avec ce contrat, le dernier vide s'il est toujours en vigueur. Laissez-la vide pour un contrat qui sert seulement à comparer. Deux contrats d'électricité ne peuvent pas être en vigueur le même jour. |

**Mes propres prix** : la dernière étape demande la première période de prix. Elle a un premier et un dernier jour (vide si les prix sont toujours en vigueur), l'abonnement annuel et le prix TTC du kWh de chaque tranche. Le premier jour proposé est celui du contrat.

Le crayon d'un contrat à vos prix ouvre son menu :
- **Le contrat** change tout sauf le type. Pour un autre type, ajoutez un autre contrat.
- Chaque période de prix (« Prix du 1er janvier 2025 au 31 juillet 2026 », « Prix depuis le 1er août 2026 ») s'ouvre pour être corrigée.
- **Ajouter une période de prix** sert quand les prix changent. Si la période en cours est encore ouverte, elle se termine la veille de la nouvelle.
- **Supprimer une période de prix** apparaît dès que le contrat en a deux.

Le contrat est comparé dès que ses prix couvrent les jours mesurés. Pour comparer une offre sur tout votre historique, sa première période peut commencer avant que l'offre existe. Les périodes d'un même contrat ne peuvent pas se chevaucher.

Le crayon d'un contrat aux tarifs réglementés ou au prix d'un capteur ouvre directement le contrat.

### Prix d'un capteur

Pour une offre dont le prix change souvent, choisissez un capteur qui donne le prix du kWh. Son unité doit être `€/kWh` ou `EUR/kWh`, et il doit garder des statistiques (classe d'état `measurement`). L'intégration compte chaque heure au prix moyen que le capteur a affiché pendant cette heure, pour toutes les tranches du contrat ; l'abonnement annuel se saisit à côté. Le contrat n'est comparé qu'à partir du premier prix du capteur : les comparaisons qui le comprennent commencent à cette heure-là. S'il est le contrat en vigueur, le coût réel ne compte rien avant. Une heure sans prix, quand Home Assistant était arrêté, prend le prix de l'heure d'avant. Les heures qui suivent le dernier prix attendent le suivant. Le prix du moment, les prévisions et le simulateur prennent la valeur actuelle du capteur.

## Contrats de gaz

Un contrat de gaz donne en euros le gaz du chauffage et de l'eau chaude, dans l'onglet Chauffage. Il ne valorise pas de compteur de gaz à part : il faut des statistiques de chauffage au gaz (voir plus bas).

**Ajouter un contrat de gaz** demande :

| Champ | Signification |
| --- | --- |
| Prix | Le **prix repère de la CRE**, l'abonnement et le prix moyen du kWh TTC que la CRE publie chaque mois pour le réseau GRDF depuis juin 2023, téléchargés avec leur historique. **Mes propres prix**, saisis par périodes comme pour l'électricité, avec l'abonnement annuel et le prix du kWh TTC. Ou le **prix d'un capteur**. |
| Profil du prix repère | **Chauffage** si le gaz chauffe la maison (environ 11 000 kWh par an), ou **Cuisson et eau chaude** (environ 1 500 kWh par an). Il ne compte qu'avec le prix repère. |
| Nom | Proposé d'après les prix (« Gaz · prix repère chauffage »), modifiable. |
| Période d'activité | Facultative. Vide, le contrat est en vigueur tous les jours. Deux contrats de gaz ne peuvent pas être en vigueur le même jour. |

Chaque jour, le gaz est compté au prix du contrat de gaz en vigueur, abonnement compris : chaque jour porte sa part de l'abonnement annuel. L'abonnement va avec le chauffage quand il est au gaz, sinon avec l'eau chaude au gaz. Un jour sans contrat de gaz, ou sans prix connu, le gaz est compté en kWh seulement.

Le prix repère est téléchargé une fois par jour sur le site de la CRE, avec le mois à venir dès qu'il est publié. S'il ne peut plus l'être pendant 48 heures, une alerte apparaît dans les réparations ; les prix déjà connus restent.

## Options

La roue dentée **Configurer** ouvre un menu de quatre pages. Chacune s'enregistre seule et garde ce que règlent les autres.

### Température extérieure

- **Thermomètre extérieur** (facultatif) : un capteur de température qui garde des statistiques. Il relie la consommation à la météo, ajoute la température au graphique d'évolution et fait apparaître l'onglet Chauffage.
- **Utiliser la météo Open-Meteo** (facultatif, désactivé par défaut) : la température vient d'[Open-Meteo](https://open-meteo.com/), gratuit et sans compte, heure par heure depuis le premier jour de consommation. La position de la maison (Paramètres > Système > Général), arrondie à 0,1° (environ 10 km), est envoyée à Open-Meteo. La température est enregistrée comme statistique de l'entrée (« Température extérieure (Open-Meteo) »), et les derniers jours sont redemandés à chaque mise à jour, car Open-Meteo les corrige quelques jours plus tard. Avec un capteur extérieur, Open-Meteo ne donne que les jours d'avant le premier jour du capteur. C'est utile pour l'historique quotidien du Linky. Les onglets lisent les deux sources. Décocher l'option efface la statistique. Données sous licence CC BY 4.0.

### Température intérieure

**Thermomètres intérieurs** (facultatif) : une ou plusieurs températures, moyennées. Le simulateur de réglage de l'onglet Chauffage part de leur moyenne les jours où le logement a été chauffé. Sans thermomètre, il est désactivé.

### Chauffage et eau chaude

Sans rien de plus que la température extérieure, l'onglet Chauffage estime le chauffage à partir de la consommation de la source et de la météo. Pour le mesurer, renseignez :
- **Statistiques de consommation du chauffage** : un ou plusieurs totaux d'énergie en kWh (un par radiateur, ou le compteur de gaz), additionnés. Des statistiques relevées une fois par jour sont acceptées : ces jours-là sont comptés sans journée type.
- **Énergie du chauffage** : électricité, déjà comptée dans la source et valorisée aux prix du contrat d'électricité en vigueur, heure par heure ; ou gaz, valorisé au contrat de gaz en vigueur.
- **Ce que mesurent ces statistiques** : le chauffage, ou le chauffage et l'eau chaude. Dans ce cas, l'eau chaude de chaque jour est estimée à ce que ces statistiques consomment un jour sans chauffage : la médiane des jours à 18 °C ou plus dehors sur les 12 derniers mois, s'il y en a au moins 7.
- **Eau chaude** (facultatif) : sa propre statistique, si elle est suivie à part, et son énergie. L'eau chaude est alors mesurée ; si elle est aussi dans les statistiques du chauffage, elle en est retirée, et elle doit avoir la même énergie qu'elles.

### Secours Tempo : API officielle de RTE

Les couleurs Tempo viennent du calendrier public de RTE, sans compte. S'il ne fonctionne plus, l'intégration peut utiliser l'API officielle de RTE. Saisissez sur cette page l'ID client et le secret d'une application créée gratuitement :

1. Créez un compte sur [data.rte-france.com](https://data.rte-france.com).
2. Ouvrez l'API [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) et choisissez **S'abonner à l'API** : cela crée une application.
3. Copiez son ID client et son secret.

Les identifiants sont vérifiés à l'enregistrement. Videz les deux champs pour n'utiliser que le calendrier public.

## Mise à jour depuis la 0.6

Les anciennes lignes « Période de prix » vont toutes seules dans leur contrat d'électricité. Les anciens « Prix du gaz » deviennent un contrat de gaz « Gaz · mes prix », en vigueur tous les jours, sans abonnement : ajoutez-le dans ses périodes de prix si vous voulez le compter. Les thermomètres intérieurs passent sur leur propre page d'options. Les statistiques déjà écrites ne changent pas.

---

## English

The integration's page has two buttons: **Add an electricity contract** and **Add a gas contract**. Each contract tells its energy under its name. A contract's pencil changes it, and the **Configure** cog sets the temperatures, the heating and the Tempo backup.

**Consumption source**: choose the hourly energy statistic of your meter. It must be an energy (Wh, kWh…) with a running total and some data, like the statistic the Linky app imports. **Reconfigure** changes it later, for example after a meter change. Every statistic is then computed again.

**Without a meter**, leave the field empty: the source is called "No meter" (only one). Nothing is costed, but the Contracts page shows the contract in force, the price of a kWh now and over 24 hours, tomorrow's Tempo color and the red and white days left. With heating statistics (a gas meter, heaters), the Heating tab works too, without the share of the home; its period follows those statistics. The Understand and Compare tabs need the meter. Reconfiguring with a statistic brings them.

**Electricity contracts**: **Add an electricity contract** asks what the contract is, then its name and dates, then its first prices when you enter them, or its sensor.

| Field | Meaning |
| --- | --- |
| Kind of contract | Base (one price), peak and off-peak hours (two prices, by the hour) or Tempo (six prices, by the hour and the color of the day). |
| Prices | The **regulated prices**, downloaded with their history and followed at each change. **My own prices**, entered by periods. Or the **price from a sensor**, read hour by hour (see below). |
| Subscribed power | Written on your bill; 6 kVA by default. It is refused when this kind of contract has no regulated price at that power. |
| Name | Suggested from the kind and the power, and can be changed. Two electricity contracts can't have the same name. |
| Off-peak hours | For HP/HC: 22:00 – 6:00, 23:00 – 7:00, 22:30 – 6:30, or **Other hours…** to type yours, one per field, on whole or half hours (`01:00-07:00`, `12:30-14:30`). They are on your bill and in your Enedis account. |
| Off-peak all weekend | For HP/HC offers where Saturdays and Sundays are billed off-peak all day. |
| Days in force | Optional: the first and last day you were billed under this contract, the last one empty while it is in force. Leave them empty for a contract you only want to compare. Two electricity contracts can't be in force on the same day. |

**My own prices**: the last step asks for the first price period. It has a first and a last day (empty while the prices are in force), the yearly subscription and the price of a kWh of each tranche, with taxes. The first day suggested is the contract's.

The pencil of a contract with your own prices opens its menu:
- **The contract** changes everything but the kind. For another kind, add another contract.
- Each price period ("Prices from 1 January 2025 to 31 July 2026", "Prices since 1 August 2026") opens to be corrected.
- **Add a price period** is for when the prices change. If the current period is still open, it ends the day before the new one.
- **Remove a price period** shows once the contract has two.

The contract is compared once its prices cover the measured days. To compare an offer over your whole history, its first period can start before the offer existed. Periods of one contract can't overlap.

The pencil of a contract at regulated prices or at a sensor's price opens the contract itself.

**Price from a sensor**: for an offer whose price changes often, choose a sensor that gives the price of a kWh. Its unit must be `€/kWh` or `EUR/kWh`, and it must keep statistics (`measurement` state class). The integration counts each hour at the mean price the sensor showed during that hour, for every tranche of the contract; the yearly subscription is entered next to it. The contract is only compared from the sensor's first price: comparisons that include it start at that hour. When it is the contract in force, the actual cost counts nothing before it. An hour without a price, while Home Assistant was off, takes the price of the hour before. The hours after the last price wait for the next one. The price now, the outlook and the simulator take the sensor's current value.

**Gas contracts**: a gas contract gives the gas of the heating and the hot water in euros, in the Heating tab. It doesn't cost a separate gas meter: it needs gas heating statistics (see below). **Add a gas contract** asks:

| Field | Meaning |
| --- | --- |
| Prices | The **CRE reference price**: the subscription and the average price of a kWh with taxes that the CRE publishes every month for the GRDF network since June 2023, downloaded with their history. **My own prices**, entered by periods like for electricity, with the yearly subscription and the price of a kWh with taxes. Or the **price from a sensor**. |
| Profile of the reference price | **Heating** if gas heats the home (about 11,000 kWh a year), or **Cooking and hot water** (about 1,500 kWh a year). It only counts with the reference price. |
| Name | Suggested from the prices ("Gas · reference price, heating"), and can be changed. |
| Days in force | Optional. Empty, the contract is in force every day. Two gas contracts can't be in force on the same day. |

Each day, the gas is counted at the price of the gas contract in force, subscription included: each day carries its share of the yearly subscription. The subscription goes with the heating when it is gas, else with the gas hot water. On a day without a gas contract, or without a known price, the gas is counted in kWh only.

The reference price is downloaded once a day from the CRE's website, with the month to come as soon as it is published. If it can't be for 48 hours, a repair issue shows; the prices already known stay.

**Options**: the **Configure** cog opens a menu of four pages. Each one is saved on its own and keeps what the others set.

- **Outdoor temperature**: an **outdoor thermometer** (optional), a temperature sensor that keeps statistics. It relates the consumption to the weather, adds the temperature to the trend chart and brings the Heating tab. **Use Open-Meteo weather** (optional, off by default): the temperature comes from [Open-Meteo](https://open-meteo.com/), free and without an account, hour by hour from the first day of consumption. The home's location (Settings > System > General), rounded to 0.1° (about 10 km), is sent to Open-Meteo. The temperature is recorded as a statistic of the entry ("Outdoor temperature (Open-Meteo)"), and the last days are asked again at each update, since Open-Meteo corrects them a few days later. With an outdoor sensor, Open-Meteo only gives the days before the sensor's first day. This helps with the daily Linky history. The tabs read both sources. Unticking the option clears the statistic. Data under CC BY 4.0.
- **Indoor temperature**: **indoor thermometers** (optional), one or several temperatures, averaged. The setting simulator of the Heating tab starts from their average on the days the home was heated. Without a thermometer, the simulator is off.
- **Heating and hot water**: with nothing but the outdoor temperature, the Heating tab estimates the heating from the source's consumption and the weather. To measure it:
  - **Heating consumption statistics**: one or several energy totals in kWh (one per heater, or the gas meter), summed. Statistics read once a day are accepted: those days are counted without a typical day.
  - **Energy of the heating**: electricity, already part of the source and costed at the prices of the electricity contract in force, hour by hour; or gas, costed at the gas contract in force.
  - **What these statistics measure**: the heating, or the heating and the hot water. Then each day's hot water is estimated as what these statistics use on a day without heating: the median of the days at 18 °C or more outside over the last 12 months, when there are at least 7.
  - **Hot water** (optional): its own statistic, if it is measured on its own, and its energy. The hot water is then measured; if the heating statistics hold it too, it is taken out of them, and it must use the same energy.
- **Tempo backup: RTE's official API**: Tempo colors come from RTE's public calendar, which needs no account. If it stops working, the integration can use RTE's official API instead. Enter on this page the client ID and secret of an application created for free:
  1. Create an account on [data.rte-france.com](https://data.rte-france.com).
  2. Open the [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) API and choose **S'abonner à l'API**: this creates an application.
  3. Copy its client ID and secret.

  The credentials are checked when saved. Clear both fields to use the public calendar only.

**Upgrading from 0.6**: the old "Price period" rows move into their electricity contract on their own. The old "Gas price" rows become a gas contract "Gas · my prices", in force every day, without a subscription: add it to its price periods if you want it counted. The indoor thermometers move to an options page of their own. The statistics already written don't change.
