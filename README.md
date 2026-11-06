# Electricity Contracts

A Home Assistant integration that costs your hourly electricity consumption under several French contracts at once: what you actually pay, and what you would have paid with another offer.

It reads the hourly consumption already in Home Assistant (for example the `linky:…` statistic the [Linky app](https://github.com/bokub/ha-linky) imports) and values every hour under each contract you add:

- **Base**, **HP/HC** with your own off-peak ranges (to the half hour, weekends off-peak or not) and **Tempo**;
- with the **regulated prices** (Tarif Bleu) and their history, downloaded from data.gouv.fr, or with **prices you set yourself**, period by period;
- with the dates each contract was in force, so the actual cost follows your real contract history.

The calculation is done by the [elec-tariffs](https://github.com/damou8/elec-tariffs) library.

> **Status: in development.** This version sets up the sources, contracts and prices, and keeps the regulated prices and the Tempo calendar up to date. The cost statistics, comparisons and sensors come in the next versions.

## Installation

1. In HACS, open the menu → **Custom repositories**, add `https://github.com/damou8/electricity_contracts` with the type **Integration**.
2. Install **Electricity Contracts**, then restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → Electricity Contracts**.

Home Assistant 2026.10 or later. The integration needs the recorder.

## Configuration

### Consumption source

Choose the hourly energy statistic of your meter. It must be an energy (Wh, kWh…) with a running total and some data, like the statistic the Linky app imports.

You can change it later with **Reconfigure**, for example after a meter change.

### Contracts

From the entry's menu, **Add contract**:

| Field | Meaning |
| --- | --- |
| Name | Free text, like "Tempo" or "Offer X". |
| Kind | Base, HP/HC or Tempo. |
| Prices | Regulated prices (downloaded with their history), or prices you set yourself. |
| Subscribed power | For regulated prices: the kVA of the contract. |
| Off-peak hours | For HP/HC: one range per line, like `22:00-06:00` or `12:30-14:00`, on whole or half hours. |
| Weekends are off-peak | For HP/HC offers where Saturdays and Sundays are off-peak all day. |
| In force from / until | The days you were billed under this contract. Leave empty for a contract you only want to compare. Two contracts can't be in force on the same day. |

### Price periods

For a contract priced by hand, **Add price period** for each period of prices: first and last day (empty if still in force), the yearly subscription and the price of each tranche per kWh, taxes included. Periods of one contract can't overlap. Deleting a contract deletes its price periods.

### RTE account (optional)

Tempo colors come from RTE's public calendar, which needs no account. If it stops working, the integration can use RTE's official API instead. In the integration's **Configure** dialog, enter the client ID and secret of an application created for free:

1. Create an account on [data.rte-france.com](https://data.rte-france.com).
2. Open the [Tempo Like Supply Contract](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1) API and choose **S'abonner à l'API**: this creates an application.
3. Copy its client ID and secret.

The credentials are checked when you save them. Leave both fields empty to use the public calendar only.

## How the data is updated

The integration checks its sources every hour and downloads only what is missing:

- **Regulated prices**: once a day, for each contract kind and power in use.
- **Tempo colors**: at the first setup, every season since the first hour of consumption; then tomorrow's color once RTE publishes it (around 11:00), retried every hour until it is out. Past colors are kept and never asked again.

Nothing is downloaded for a kind of contract you haven't added.

## Privacy

- The consumption never leaves Home Assistant. The integration only downloads public prices and Tempo colors.
- Diagnostics hide the statistic ID and the entry title (they contain the meter number) and the RTE credentials.

## Known limitations

- Hours are split into two half hours with the same consumption, so an off-peak range starting on a half hour is followed only approximately within that hour.
- Dynamic (spot) prices, offers indexed on the regulated prices and special days of other offers (Zen Flex…) aren't supported yet.
- The official RTE API client hasn't been tested against the live API yet.

## Troubleshooting

- **Setup keeps retrying**: the prices or the Tempo colors a contract needs couldn't be downloaded at all. The integration tries again on its own; check the logs for the error.
- **Repair "Tempo colors can't be updated"**: RTE's public calendar has failed for two days. Add RTE credentials (see above) so the official API takes over.
- **Repair "RTE refuses the credentials"**: check the application on data.rte-france.com and enter the credentials again, or clear them.
- Debug logs: enable them from the integration's menu; they include the `elec_tariffs` library.

## Removal

1. **Settings → Devices & services → Electricity Contracts**, open the entry's menu and choose **Delete**. Its cache and repairs are deleted with it.
2. To remove the code too, uninstall it in HACS and restart Home Assistant.

## License

[MIT](LICENSE)
