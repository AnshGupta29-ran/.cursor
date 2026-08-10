import re
import random
from datetime import datetime

# Sample receipt texts (canned)
_SAMPLE_TEXTS = [
    """MERCY MART
    123 MAIN ST
    DATE: 03/04/2025
    TOTAL $12.34
    THANK YOU""",
    """Café Paris
    45 Rue de la République
    04.03.2025
    TOTAL €8,90
    Merci!""",
    """Fuel Station
    DATE 2025-03-04
    AMOUNT DUE $45.67
    VAT $3.21""",
    """Gadget Shop
    Receipt #12345
    2025/03/04
    GRAND TOTAL $123.45
    Warranty: 12 months""",
    """Restaurant XYZ
    2025-03-04
    Subtotal $23.00
    TAX $2.30
    TOTAL $25.30
    Cash"""
]

def _stub_ocr(file_bytes: bytes) -> str:
    """Deterministic stub OCR: pick a sample based on hash of bytes."""
    idx = sum(file_bytes) % len(_SAMPLE_TEXTS)
    return _SAMPLE_TEXTS[idx]

# Preset configurations
_PRESETS = {
    "us_corner_store": {
        "currency": "$",
        "date_order": "MDY",
        "decimal": ".",
        "strict": False,
    },
    "eu_bistro": {
        "currency": "€",
        "date_order": "DMY",
        "decimal": ",",
        "strict": False,
    },
    "strict_audit": {
        "currency": None,  # any
        "date_order": None,
        "decimal": ".",
        "strict": True,
    },
}

def _parse_date(text: str, order: str) -> (str, list):
    issues = []
    # common date regexes
    patterns = [
        r"(?P<m>\d{1,2})[\./-](?P<d>\d{1,2})[\./-](?P<y>\d{4})",  # MDY or DMY
        r"(?P<y>\d{4})[\./-](?P<m>\d{1,2})[\./-](?P<d>\d{1,2})",  # YMD
        r"(?P<d>\d{1,2})[\./-](?P<m>\d{1,2})[\./-](?P<y>\d{4})",  # DMY
        r"(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?P<d>\d{1,2})\s+(?P<y>\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                month = int(m.group('m')) if m.groupdict().get('m') else None
                day = int(m.group('d'))
                year = int(m.group('y'))
                # Resolve ambiguous order if needed
                if order == "MDY" and month and month > 12:
                    # swapped
                    month, day = day, month
                elif order == "DMY" and month and month > 12:
                    month, day = day, month
                date_iso = f"{year:04d}-{month:02d}-{day:02d}"
                return date_iso, []
            except Exception:
                issues.append("failed to parse date components")
    issues.append("date not found")
    return None, issues

def _parse_total(text: str, currency_symbol: str, decimal: str) -> (float, list):
    issues = []
    # find lines with TOTAL or AMOUNT DUE etc.
    pat = r"(?i)(total|amount due|grand total)[:\s]*([\$€]?)([0-9]+[{}]?[0-9]*)".format(re.escape(decimal))
    m = re.search(pat, text)
    if m:
        amt_str = m.group(3).replace(decimal, ".")
        try:
            return float(amt_str), []
        except ValueError:
            issues.append("cannot convert total to float")
    issues.append("total not found")
    return None, issues

def extract(text: str, preset: str = "us_corner_store") -> dict:
    cfg = _PRESETS.get(preset, _PRESETS["us_corner_store"])
    currency = cfg["currency"]
    date_order = cfg["date_order"]
    decimal = cfg["decimal"]
    strict = cfg["strict"]

    issues = []
    # merchant heuristic: first non-empty line not containing only symbols
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    merchant = lines[0] if lines else None
    if not merchant:
        issues.append("merchant not found")

    # date
    date_iso, date_issues = _parse_date(text, date_order) if date_order else (None, [])
    issues.extend(date_issues)
    if not date_iso and strict:
        issues.append("strict mode: missing date")

    # total
    total_val, total_issues = _parse_total(text, currency, decimal)
    issues.extend(total_issues)
    if total_val is None and strict:
        issues.append("strict mode: missing total")

    # confidence per field (simple heuristic)
    confidence = {
        "merchant": 0.9 if merchant else 0.0,
        "date": 0.8 if date_iso else 0.0,
        "total": 0.8 if total_val is not None else 0.0,
        "currency": 0.7 if currency else 0.0,
    }

    result = {
        "merchant": merchant,
        "date": date_iso,
        "total": total_val,
        "currency": currency if currency else ("€" if "€" in text else "$"),
        "confidence": confidence,
        "issues": issues,
        "preset": preset,
    }
    return result
