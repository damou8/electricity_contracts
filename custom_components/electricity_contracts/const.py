"""Constants of the Electricity Contracts integration."""

from datetime import time
from typing import Final
from zoneinfo import ZoneInfo

from elec_tariffs import ContractKind

DOMAIN: Final = "electricity_contracts"

CONF_STATISTIC_ID: Final = "statistic_id"
CONF_RTE_CLIENT_ID: Final = "rte_client_id"
CONF_RTE_CLIENT_SECRET: Final = "rte_client_secret"  # noqa: S105 - a key
CONF_TEMPERATURE: Final = "temperature"
# The options' collapsed section of the RTE credentials.
SECTION_RTE: Final = "rte"

SERVICE_RECOMPUTE: Final = "recompute"
SERVICE_COMPARE: Final = "compare"

SUBENTRY_CONTRACT: Final = "contract"
SUBENTRY_PRICE_PERIOD: Final = "price_period"
# Removed in 0.2: comparisons are made on the Contracts page.
SUBENTRY_COMPARISON: Final = "comparison"

CONF_UID: Final = "uid"
CONF_KIND: Final = "kind"
CONF_PRICING: Final = "pricing"
CONF_KVA: Final = "kva"
CONF_OFF_PEAK: Final = "off_peak"
CONF_WEEKEND_OFF_PEAK: Final = "weekend_off_peak"
CONF_ACTIVE_FROM: Final = "active_from"
CONF_ACTIVE_TO: Final = "active_to"
# The contract form's section of the days it was in force.
SECTION_ACTIVE: Final = "active_period"

CONF_CONTRACT: Final = "contract"
CONF_START: Final = "start"
CONF_END: Final = "end"
CONF_FIXED_PER_YEAR: Final = "fixed_per_year"
CONF_PRICES: Final = "prices"


PRICING_OFFICIAL: Final = "official"
PRICING_MANUAL: Final = "manual"

DEFAULT_KVA: Final = 6
# The off-peak hours meters most often have, offered in a list; the others are
# typed in.
OFF_PEAK_PRESETS: Final = {
    "22_06": ["22:00-06:00"],
    "23_07": ["23:00-07:00"],
    "2230_0630": ["22:30-06:30"],
}
OFF_PEAK_OTHER: Final = "other"

# Subscribed powers each regulated offer has had (data.gouv.fr, November 2026).
OFFERED_KVA: Final[dict[ContractKind, tuple[int, ...]]] = {
    ContractKind.BASE: (3, 6, 9, 12, 15),
    ContractKind.HPHC: (3, 6, 9, 12, 15, 18, 24, 30, 36),
    ContractKind.TEMPO: (6, 9, 12, 15, 18, 24, 30, 36),
}

# Off-peak hours, Tempo days, price changes and RTE's publication times are French
# local time, whatever the server's time zone.
FRANCE_TIME_ZONE: Final = ZoneInfo("Europe/Paris")
# RTE publishes tomorrow's color around 10:40; ask a little later.
TOMORROW_PUBLISHED: Final = time(11)
TOMORROW_JITTER_MINUTES: Final = 20

PRICES_MAX_AGE_HOURS: Final = 24
SEASON_RETRY_HOURS: Final = 6
TOMORROW_RETRY_MINUTES: Final = 55
SOURCE_ISSUE_AFTER_HOURS: Final = 48

STORAGE_VERSION: Final = 1
