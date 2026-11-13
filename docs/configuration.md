# Configuration

*[English below](#english)*

## Source de consommation

Choisissez la statistique horaire d'énergie de votre compteur. Il faut une énergie (Wh, kWh…) avec un total cumulé et des données, comme la statistique qu'importe l'App Linky.

Vous pouvez la changer plus tard avec **Reconfigurer**, par exemple après un changement de compteur. Toutes les statistiques sont alors recalculées.

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
- **Température extérieure** (facultatif) : un capteur de température qui garde des statistiques. Il relie la consommation à la météo dans l'onglet Comprendre, et ajoute la température au graphique d'évolution.
- **Secours Tempo : API officielle RTE** (section repliée) : voir ci-dessous.

## Compte RTE (facultatif)

Les couleurs Tempo viennent du calendrier public de RTE, sans compte. S'il ne fonctionne plus, l'intégration peut utiliser l'API officielle de RTE. Dans la fenêtre **Configurer** de l'intégration, section **Secours Tempo : API officielle RTE**, saisissez l'ID client et le secret d'une application créée gratuitement :

1. Créez un compte sur [data.rte-france.com](https://data.rte-france.com).
2. Ouvrez l'API [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) et choisissez **S'abonner à l'API** : cela crée une application.
3. Copiez son ID client et son secret.

Les identifiants sont vérifiés à l'enregistrement. Laissez les deux champs vides pour n'utiliser que le calendrier public.

---

## English

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
