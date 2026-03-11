import csv
import re
from datetime import datetime
from typing import Any


def normalize(text):
    return re.sub(r"\s+", " ", text.strip()).lower()


def clean_text(text):
    return re.sub(r"\s+", " ", text.strip())


def parse_int(value):

    value = value.strip()
    if not value:
        return 0
    try:
        n = int(float(value))
    except (ValueError, OverflowError):
        return 0
    return n if n > 0 else 0


# Date formats we try, in order of preference
_DATE_FORMATS = [
    "%Y-%m-%d",     # 2022-01-15
    "%d/%m/%Y",     # 15/01/2022
    "%m/%d/%Y",     # 01/15/2022
    "%Y/%m/%d",     # 2022/01/15
    "%d-%m-%Y",     # 15-01-2022
    "%m-%d-%Y",     # 01-15-2022
    "%B %d, %Y",    # January 15, 2022
    "%b %d, %Y",    # Jan 15, 2022
    "%d %B %Y",     # 15 January 2022
    "%d %b %Y",     # 15 Jan 2022
    "%Y.%m.%d",     # 2022.01.15
    "%d.%m.%Y",     # 15.01.2022
]


def parse_date(value):
    """
    Try to parse *value* as a date. Return 'YYYY-MM-DD' on success,
    or 'Unknown' for anything invalid / unparseable.
    """
    value = value.strip()
    if not value:
        return "Unknown"
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            # Reject nonsensical years
            if dt.year < 1800 or dt.year > 2100:
                continue
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return "Unknown"








