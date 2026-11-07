# Electricity Contracts

Home Assistant custom integration (HACS) that costs the hourly Linky statistic under several contracts. The logic lives in the `elec-tariffs` library (damou8/elec-tariffs); this repository maps it onto Home Assistant. Follow Home Assistant's conventions and the [Integration Quality Scale](https://contributors.home-assistant.io/core/quality-scale/rules/); `quality_scale.yaml` tracks the rules.

## Commands

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/python scripts/manifest_requirements.py | .venv/bin/pip install -r /dev/stdin
.venv/bin/ruff check && .venv/bin/ruff format --check && .venv/bin/mypy
.venv/bin/pytest --cov          # fails under 95 % coverage
podman run --rm -v "$PWD:/github/workspace:ro,Z" ghcr.io/home-assistant/hassfest
scripts/develop                 # throwaway Home Assistant on :8123
```

To test against an unreleased library, `pip install -e ../../elec-tariffs --no-deps` in the venv.

## Conventions

- Minimum Home Assistant: `hacs.json` (2026.10.0). `requirements_test.txt` pins the matching phacc. Don't use APIs newer than the minimum (`visible` form fields, `config_entry_id` on issues and `async_unload_platforms_or_raise` are 2026.11).
- The release tag `vX.Y.Z` is written in `manifest.json` by the release workflow; keep `0.0.0` in the repository.
- Every change of options or subentries reloads the entry through the update listener: use `async_update_and_abort`, never the reloading variants, in flows.
- Translations: `en.json` and `fr.json` together. French uses "vous". No `<…>` in strings (hassfest reads them as HTML).
- Tests mock the library classes where the integration imports them (`tests/conftest.py`, `sources` fixture) and run at a frozen time (7 November 2026, 10:00 in Paris; the test time zone is US/Pacific).

## Statistics

- `costing.py` is pure (runs in the executor): it keeps the source rows that hold one hour and costs them. Daily Linky rows (no load curve) are never costed and missing hours never filled: the user doesn't want estimated consumption.
- `statistics.py` reads where each series stopped, clears what is out of date (fingerprints in the `<entry_id>.statistics` store) and appends rows. Bump `COSTING_VERSION` when the way costs are computed changes, so every statistic is written again.
- Comparisons and sensors read the statistics back (`comparison.py`): the coordinator first waits until the recorder has committed what was queued (`async_wait_for_recorder`, built on `async_get_commit_future`). Every compared contract is narrowed to the same hours.
- Scheduled coordinator refreshes run as background tasks: tests driven by `async_fire_time_changed` need `hass.async_block_till_done(wait_background_tasks=True)`.
- Recorder jobs run on the recorder's own executor: in tests, `await async_wait_recording_done(hass)` before reading statistics or asserting on a refresh triggered by time.

## Privacy

The Linky statistic ID and the entry title contain the meter's PRM number. Never commit real statistics or diagnostics; tests use `linky:00000000000000`. Diagnostics redact the statistic ID, the title and the RTE credentials.
