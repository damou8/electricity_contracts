# Statistiques et actions

*[English below](#english)*

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

## Action Comparer

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

## Historique quotidien

Sans courbe de charge, le Linky ne remonte qu'une consommation par jour. L'App Linky l'enregistre en une ligne à minuit, et c'est souvent le cas de l'historique antérieur à l'activation de la courbe de charge.

Ces totaux quotidiens ne sont pas valorisés : on ne sait pas comment ils se répartissent entre heures creuses et heures pleines, et l'intégration ne fait pas d'estimation. Les statistiques commencent à la première heure mesurée. Une heure qui manque dans la source reste vide.

Une statistique qui n'a que des valeurs quotidiennes est refusée à la configuration. Activez la courbe de charge (consommation horaire) dans votre espace Enedis et dans l'App Linky.

---

## English

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
