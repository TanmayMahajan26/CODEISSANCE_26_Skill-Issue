"""
Nexus360 — Tests for Normalization Utilities.
"""

import pytest
from datetime import date

from app.utils.normalization import (
    normalize_name,
    normalize_mobile,
    normalize_email,
    normalize_pan,
    normalize_city,
    normalize_dob,
)


# ── normalize_name ───────────────────────────────────────────────

class TestNormalizeName:
    def test_basic(self):
        assert normalize_name("Rohita Raghavan") == "rohita raghavan"

    def test_with_initial(self):
        assert normalize_name("Rohita P. Raghavan") == "rohita p raghavan"

    def test_initial_only(self):
        assert normalize_name("R. Raghavan") == "r raghavan"

    def test_extra_spaces(self):
        assert normalize_name("  Rohita   Raghavan  ") == "rohita raghavan"

    def test_punctuation(self):
        assert normalize_name("SHARMA, Ankit") == "sharma ankit"

    def test_none(self):
        assert normalize_name(None) is None

    def test_empty(self):
        assert normalize_name("") is None

    def test_whitespace_only(self):
        assert normalize_name("   ") is None

    def test_uppercase(self):
        assert normalize_name("ROHITA RAGHAVAN") == "rohita raghavan"

    def test_title_removal(self):
        assert normalize_name("Mr. Rohita P. Raghavan") == "rohita p raghavan"
        assert normalize_name("Dr. Ankit Sharma") == "ankit sharma"
        assert normalize_name("Shri Rajesh Kumar") == "rajesh kumar"


# ── normalize_mobile ────────────────────────────────────────────

class TestNormalizeMobile:
    def test_plain_10_digit(self):
        assert normalize_mobile("9876543210") == "9876543210"

    def test_with_country_code(self):
        assert normalize_mobile("+91 98765 43210") == "9876543210"

    def test_with_dashes(self):
        assert normalize_mobile("98765-43210") == "9876543210"

    def test_with_91_prefix(self):
        assert normalize_mobile("919876543210") == "9876543210"

    def test_with_0091_prefix(self):
        assert normalize_mobile("00919876543210") == "9876543210"

    def test_with_zero_prefix(self):
        assert normalize_mobile("09876543210") == "9876543210"

    def test_none(self):
        assert normalize_mobile(None) is None

    def test_empty(self):
        assert normalize_mobile("") is None


# ── normalize_email ──────────────────────────────────────────────

class TestNormalizeEmail:
    def test_basic(self):
        assert normalize_email("rohita@gmail.com") == "rohita@gmail.com"

    def test_uppercase(self):
        assert normalize_email("ROHITA@Gmail.COM") == "rohita@gmail.com"

    def test_whitespace(self):
        assert normalize_email("  rohita@gmail.com  ") == "rohita@gmail.com"

    def test_none(self):
        assert normalize_email(None) is None

    def test_empty(self):
        assert normalize_email("") is None


# ── normalize_pan ────────────────────────────────────────────────

class TestNormalizePan:
    def test_basic(self):
        assert normalize_pan("ABCDE1234F") == "ABCDE1234F"

    def test_lowercase(self):
        assert normalize_pan("abcde1234f") == "ABCDE1234F"

    def test_with_spaces(self):
        assert normalize_pan("ABCDE 1234F") == "ABCDE1234F"

    def test_none(self):
        assert normalize_pan(None) is None

    def test_empty(self):
        assert normalize_pan("") is None


# ── normalize_city ───────────────────────────────────────────────

class TestNormalizeCity:
    def test_basic(self):
        assert normalize_city("Mumbai") == "mumbai"

    def test_alias_bombay(self):
        assert normalize_city("Bombay") == "mumbai"

    def test_alias_bangalore(self):
        assert normalize_city("Bangalore") == "bengaluru"

    def test_alias_madras(self):
        assert normalize_city("Madras") == "chennai"

    def test_alias_calcutta(self):
        assert normalize_city("Calcutta") == "kolkata"

    def test_whitespace(self):
        assert normalize_city("  BANGALORE ") == "bengaluru"

    def test_unknown_city(self):
        assert normalize_city("Jaipur") == "jaipur"

    def test_none(self):
        assert normalize_city(None) is None


# ── normalize_dob ────────────────────────────────────────────────

class TestNormalizeDob:
    def test_iso_format(self):
        assert normalize_dob("1988-06-12") == date(1988, 6, 12)

    def test_dd_mm_yyyy_slash(self):
        assert normalize_dob("12/06/1988") == date(1988, 6, 12)

    def test_dd_mm_yyyy_dash(self):
        assert normalize_dob("12-06-1988") == date(1988, 6, 12)

    def test_date_object(self):
        d = date(1988, 6, 12)
        assert normalize_dob(d) == d

    def test_none(self):
        assert normalize_dob(None) is None

    def test_empty(self):
        assert normalize_dob("") is None

    def test_invalid(self):
        assert normalize_dob("not-a-date") is None
