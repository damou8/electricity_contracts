# Electricity Contracts

*[English version below](#english)*

Une intégration Home Assistant qui valorise votre consommation électrique heure par heure selon plusieurs contrats français à la fois : ce que vous payez vraiment, et ce que vous auriez payé avec une autre offre.

Elle lit la consommation horaire déjà présente dans Home Assistant, par exemple la statistique `linky:…` qu'importe l'[App Linky](https://github.com/bokub/ha-linky). Elle valorise ensuite chaque heure selon chacun des contrats que vous ajoutez :

- **Base**, **HP/HC** avec vos propres plages d'heures creuses (à la demi-heure, week-end en heures creuses ou non) et **Tempo** ;
- aux **tarifs réglementés** (Tarif Bleu), avec leur historique téléchargé depuis data.gouv.fr, ou à des **prix que vous fixez vous-même**, période par période ;
- avec les dates où chaque contrat était en vigueur, pour que le coût réel suive votre véritable historique de contrats.

Le calcul est fait par la bibliothèque [elec-tariffs](https://github.com/damou8/elec-tariffs).

> **État : en développement.** Les statistiques de coût sont écrites. Les capteurs, les comparaisons sur une période et la projection arrivent dans les prochaines versions.

## Installation

1. Dans HACS, ouvrez le menu → **Dépôts personnalisés** et ajoutez `https://github.com/damou8/electricity_contracts` avec le type **Intégration**.
2. Installez **Electricity Contracts**, puis redémarrez Home Assistant.
3. Allez dans **Paramètres → Appareils et services → Ajouter une intégration → Electricity Contracts**.

Home Assistant 2026.10 ou plus récent. L'intégration a besoin du recorder.

## Configuration

### Source de consommation

Choisissez la statistique horaire d'énergie de votre compteur. Il faut une énergie (Wh, kWh…) avec un total cumulé et des données, comme la statistique qu'importe l'App Linky.

Vous pouvez la changer plus tard avec **Reconfigurer**, par exemple après un changement de compteur. Toutes les statistiques sont alors recalculées.

### Contrats

Depuis le menu de l'entrée, **Ajouter un contrat** :

| Champ | Signification |
| --- | --- |
| Nom | Texte libre, comme « Tempo » ou « Offre X ». |
| Type | Base, HP/HC ou Tempo. |
| Prix | Tarifs réglementés (téléchargés avec leur historique), ou prix que vous fixez vous-même. |
| Puissance souscrite | Pour les tarifs réglementés : les kVA du contrat. |
| Heures creuses | Pour HP/HC : une plage par ligne, comme `22:00-06:00` ou `12:30-14:00`, à l'heure ou à la demi-heure. |
| Week-end en heures creuses | Pour les offres HP/HC où samedis et dimanches sont en heures creuses toute la journée. |
| En vigueur du / jusqu'au | Les jours facturés avec ce contrat. Laissez vide pour un contrat qui sert seulement à comparer. Deux contrats ne peuvent pas être en vigueur le même jour. |

### Périodes de prix

Pour un contrat dont vous fixez les prix, ajoutez une **période de prix** par période tarifaire :
- le premier et le dernier jour (vide si les prix sont toujours en vigueur) ;
- l'abonnement annuel ;
- le prix au kWh de chaque tranche, TTC.

Les périodes d'un même contrat ne peuvent pas se chevaucher. Supprimer un contrat supprime ses périodes de prix.

### Compte RTE (facultatif)

Les couleurs Tempo viennent du calendrier public de RTE, sans compte. S'il ne fonctionne plus, l'intégration peut utiliser l'API officielle de RTE. Dans la fenêtre **Configurer** de l'intégration, saisissez l'ID client et le secret d'une application créée gratuitement :

1. Créez un compte sur [data.rte-france.com](https://data.rte-france.com).
2. Ouvrez l'API [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) et choisissez **S'abonner à l'API** : cela crée une application.
3. Copiez son ID client et son secret.

Les identifiants sont vérifiés à l'enregistrement. Laissez les deux champs vides pour n'utiliser que le calendrier public.

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

## Dépannage

- **La configuration réessaie sans cesse** : les tarifs ou les couleurs Tempo dont un contrat a besoin n'ont jamais pu être téléchargés. L'intégration réessaie toute seule ; l'erreur figure dans les journaux.
- **Réparation « Les couleurs Tempo ne se mettent plus à jour »** : le calendrier public de RTE échoue depuis deux jours. Ajoutez des identifiants RTE (voir plus haut) pour que l'API officielle prenne le relais.
- **Réparation « RTE refuse les identifiants »** : vérifiez l'application sur data.rte-france.com et saisissez à nouveau les identifiants, ou effacez-les.
- **Un contrat s'arrête à une date** : ses diagnostics indiquent s'il attend une couleur ou un prix. Pour un contrat à prix manuels, ajoutez la période de prix qui manque.
- **Journaux de débogage** : activez-les depuis le menu de l'intégration ; ils incluent la bibliothèque `elec_tariffs`.

## Désinstallation

1. **Paramètres → Appareils et services → Electricity Contracts**, ouvrez le menu de l'entrée et choisissez **Supprimer**. Ses statistiques, son cache et ses réparations sont supprimés avec elle.
2. Pour retirer aussi le code, désinstallez-la dans HACS et redémarrez Home Assistant.

## Licence

[MIT](LICENSE)

---

## English

A Home Assistant integration that costs your hourly electricity consumption under several French contracts at once: what you actually pay, and what you would have paid with another offer.

It reads the hourly consumption already in Home Assistant, for example the `linky:…` statistic the [Linky app](https://github.com/bokub/ha-linky) imports. It then values every hour under each contract you add:

- **Base**, **HP/HC** with your own off-peak ranges (to the half hour, weekends off-peak or not) and **Tempo**;
- with the **regulated prices** (Tarif Bleu) and their history, downloaded from data.gouv.fr, or with **prices you set yourself**, period by period;
- with the dates each contract was in force, so the actual cost follows your real contract history.

The calculation is done by the [elec-tariffs](https://github.com/damou8/elec-tariffs) library.

> **Status: in development.** The cost statistics are written. Sensors, comparisons over a period and the projection come in the next versions.

### Installation

1. In HACS, open the menu → **Custom repositories** and add `https://github.com/damou8/electricity_contracts` with the type **Integration**.
2. Install **Electricity Contracts**, then restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → Electricity Contracts**.

Home Assistant 2026.10 or later. The integration needs the recorder.

### Configuration

**Consumption source**: choose the hourly energy statistic of your meter. It must be an energy (Wh, kWh…) with a running total and some data, like the statistic the Linky app imports. **Reconfigure** changes it later, for example after a meter change. Every statistic is then computed again.

**Contracts**: from the entry's menu, **Add contract**.

| Field | Meaning |
| --- | --- |
| Name | Free text, like "Tempo" or "Offer X". |
| Kind | Base, HP/HC or Tempo. |
| Prices | Regulated prices (downloaded with their history), or prices you set yourself. |
| Subscribed power | For regulated prices: the kVA of the contract. |
| Off-peak hours | For HP/HC: one range per line, like `22:00-06:00` or `12:30-14:00`, on whole or half hours. |
| Weekends are off-peak | For HP/HC offers where Saturdays and Sundays are off-peak all day. |
| In force from / until | The days you were billed under this contract. Leave empty for a contract you only want to compare. Two contracts can't be in force on the same day. |

**Price periods**: for a contract priced by hand, add a price period for each period of prices:
- the first and last day (empty if still in force);
- the yearly subscription;
- the price of each tranche per kWh, taxes included.

Periods of one contract can't overlap. Deleting a contract deletes its price periods.

**RTE account (optional)**: Tempo colors come from RTE's public calendar, which needs no account. If it stops working, the integration can use RTE's official API instead. In the integration's **Configure** dialog, enter the client ID and secret of an application created for free:
1. Create an account on [data.rte-france.com](https://data.rte-france.com).
2. Open the [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) API and choose **S'abonner à l'API**: this creates an application.
3. Copy its client ID and secret.

The credentials are checked when saved.

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

- **Energy dashboard**: in the settings of your grid consumption, track the costs with a total cost entity or statistic and pick **Actual cost**.
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
- Hours are split into two half hours with the same consumption. Spot prices, offers indexed on the regulated prices and special days of other offers aren't supported yet. The official RTE API client hasn't been tested against the live API yet.
- **Repairs**:
  - "Tempo colors can't be updated": add RTE credentials;
  - "RTE refuses the credentials": enter them again or clear them.

  A contract that stops at a date is waiting for a color or a price: see its diagnostics.
- **Removal**: delete the entry from **Settings → Devices & services → Electricity Contracts**. Its statistics, cache and repairs go with it. Then uninstall it in HACS and restart.

License: [MIT](LICENSE)
