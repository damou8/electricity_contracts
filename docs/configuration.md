# Configuration

*[English below](#english)*

## Source de consommation

Choisissez la statistique horaire d'énergie de votre compteur. Il faut une énergie (Wh, kWh…) avec un total cumulé et des données, comme la statistique qu'importe l'App Linky.

Vous pouvez la changer plus tard avec **Reconfigurer**, par exemple après un changement de compteur. Toutes les statistiques sont alors recalculées.

**Sans compteur**, laissez le champ vide : la source s'appelle « Sans compteur » (une seule possible). Rien n'est valorisé, mais la page Contrats montre le contrat en cours, le prix du kWh maintenant et sur 24 h, la couleur Tempo de demain et les jours rouges et blancs restants. Avec des statistiques de chauffage (un compteur de gaz, des radiateurs), l'onglet Chauffage fonctionne aussi, sans la part dans la maison ; sa période suit ces statistiques. Les onglets Comprendre et Comparer ont besoin du compteur. Reconfigurer avec une statistique les fait apparaître.

## Contrats

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

## Périodes de prix

Pour un contrat à vos prix, **Ajouter une période de prix** pour chaque période tarifaire :
- le premier et le dernier jour (vide si les prix sont toujours en vigueur) ;
- l'abonnement annuel ;
- le prix au kWh de chaque tranche, TTC.

Le contrat est comparé dès que ses prix couvrent les jours mesurés. Pour comparer une offre sur tout votre historique, sa première période peut commencer avant que l'offre existe. Les périodes d'un même contrat ne peuvent pas se chevaucher. Supprimer un contrat supprime ses périodes de prix.

## Options

Dans la fenêtre **Configurer** de l'intégration :
- **Température extérieure** (facultatif) : un capteur de température qui garde des statistiques. Il relie la consommation à la météo, ajoute la température au graphique d'évolution et fait apparaître l'onglet Chauffage.
- **Utiliser la météo Open-Meteo** (facultatif, désactivé par défaut) : sans capteur extérieur, la température vient d'[Open-Meteo](https://open-meteo.com/), gratuit et sans compte, heure par heure depuis le premier jour de consommation. La position de la maison (Paramètres > Système > Général), arrondie à 0,1° (environ 10 km), est envoyée à Open-Meteo. La température est enregistrée comme statistique de l'entrée (« Température extérieure (Open-Meteo) »), et les derniers jours sont redemandés à chaque mise à jour, car Open-Meteo les corrige quelques jours plus tard. Un capteur choisi passe avant. Décocher l'option efface la statistique. Données sous licence CC BY 4.0.
- **Chauffage et eau chaude** : voir ci-dessous.
- **Secours Tempo : API officielle RTE** (section repliée) : voir plus bas.

## Chauffage et eau chaude (facultatif)

Sans rien de plus que la température extérieure, l'onglet Chauffage estime le chauffage à partir de la consommation de la source et de la météo. Pour le mesurer, renseignez dans la section **Chauffage et eau chaude** :
- **Statistiques de consommation du chauffage** : un ou plusieurs totaux d'énergie en kWh (un par radiateur, ou le compteur de gaz), additionnés. Des statistiques relevées une fois par jour sont acceptées : ces jours-là sont comptés en kWh, sans journée type.
- **Énergie** : électricité, déjà comptée dans la source et valorisée aux prix du contrat en vigueur, heure par heure ; ou gaz, hors facture d'électricité.
- **Ce qu'elles mesurent** : le chauffage, ou le chauffage et l'eau chaude. Dans ce cas, l'eau chaude de chaque jour est estimée à ce que ces statistiques consomment un jour sans chauffage : la médiane des jours à 18 °C ou plus dehors sur les 12 derniers mois, s'il y en a au moins 7.
- **Ballon d'eau chaude** (facultatif) : sa propre statistique, s'il est suivi à part, et son énergie. L'eau chaude est alors mesurée ; si elle est aussi dans les statistiques du chauffage, elle en est retirée, et le ballon doit avoir la même énergie qu'elles.
- **Thermomètres intérieurs** (facultatif) : une ou plusieurs températures, moyennées. Le simulateur de réglage part de cette température ; sans elle, il est désactivé.

Pour le gaz, **Ajouter un prix du gaz** pour chaque prix : le prix du kWh TTC, le premier et le dernier jour (vide s'il est toujours en vigueur). Sans prix, le gaz est compté en kWh seulement. Les prix ne peuvent pas se chevaucher.

## Compte RTE (facultatif)

Les couleurs Tempo viennent du calendrier public de RTE, sans compte. S'il ne fonctionne plus, l'intégration peut utiliser l'API officielle de RTE. Dans la fenêtre **Configurer** de l'intégration, section **Secours Tempo : API officielle RTE**, saisissez l'ID client et le secret d'une application créée gratuitement :

1. Créez un compte sur [data.rte-france.com](https://data.rte-france.com).
2. Ouvrez l'API [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) et choisissez **S'abonner à l'API** : cela crée une application.
3. Copiez son ID client et son secret.

Les identifiants sont vérifiés à l'enregistrement. Laissez les deux champs vides pour n'utiliser que le calendrier public.

---

## English

**Consumption source**: choose the hourly energy statistic of your meter. It must be an energy (Wh, kWh…) with a running total and some data, like the statistic the Linky app imports. **Reconfigure** changes it later, for example after a meter change. Every statistic is then computed again.

**Without a meter**, leave the field empty: the source is called "No meter" (only one). Nothing is costed, but the Contracts page shows the contract in force, the price of a kWh now and over 24 hours, tomorrow's Tempo color and the red and white days left. With heating statistics (a gas meter, heaters), the Heating tab works too, without the share of the home; its period follows those statistics. The Understand and Compare tabs need the meter. Reconfiguring with a statistic brings them.

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
- **Outdoor temperature** (optional): a temperature sensor that keeps statistics. It relates the consumption to the weather, adds the temperature to the trend chart and brings the Heating tab.
- **Use Open-Meteo weather** (optional, off by default): without an outdoor sensor, the temperature comes from [Open-Meteo](https://open-meteo.com/), free and without an account, hour by hour from the first day of consumption. The home's location (Settings > System > General), rounded to 0.1° (about 10 km), is sent to Open-Meteo. The temperature is recorded as a statistic of the entry ("Outdoor temperature (Open-Meteo)"), and the last days are asked again at each update, since Open-Meteo corrects them a few days later. A chosen sensor comes first. Unticking the option clears the statistic. Data under CC BY 4.0.
- **Heating and hot water**: see below.
- **Tempo backup: RTE's official API** (a collapsed section): see further down.

**Heating and hot water (optional)**: with nothing but the outdoor temperature, the Heating tab estimates the heating from the source's consumption and the weather. To measure it, fill the **Heating and hot water** section:
- **Heating consumption statistics**: one or several energy totals in kWh (one per heater, or the gas meter), summed. Statistics read once a day are accepted: those days are counted in kWh, without a typical day.
- **Energy**: electricity, already part of the source and costed at the prices of the contract in force, hour by hour; or gas, outside the electricity bill.
- **What they measure**: the heating, or the heating and the hot water. Then each day's hot water is estimated as what these statistics use on a day without heating: the median of the days at 18 °C or more outside over the last 12 months, when there are at least 7.
- **Water heater** (optional): its own statistic, if it is tracked separately, and its energy. Hot water is then measured; if the heating statistics hold it too, it is taken out of them, and the water heater must use the same energy.
- **Indoor thermometers** (optional): one or several temperatures, averaged. The setting simulator starts from this temperature; without it, the simulator is off.

For gas, **Add a gas price** for each price: the price per kWh with taxes, the first and last day (empty while in force). Without a price, gas is counted in kWh only. Prices can't overlap.

**RTE account (optional)**: Tempo colors come from RTE's public calendar, which needs no account. If it stops working, the integration can use RTE's official API instead. In the integration's **Configure** dialog, section **Tempo backup: RTE's official API**, enter the client ID and secret of an application created for free:
1. Create an account on [data.rte-france.com](https://data.rte-france.com).
2. Open the [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) API and choose **S'abonner à l'API**: this creates an application.
3. Copy its client ID and secret.

The credentials are checked when saved.
