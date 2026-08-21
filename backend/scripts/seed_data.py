"""
Nexus360 — Seed Data Generator.

Generates 100+ synthetic customer records spread across all 5 source
systems with intentional inconsistencies for testing the identity
resolution pipeline.

Usage:
    python -m scripts.seed_data

This creates CSV files in scripts/data/ that can be ingested via the API.
"""

import csv
import os
import random
import string
from datetime import date, timedelta
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "data"
SYSTEMS = ["EQUITY", "MUTUAL_FUND", "INSURANCE", "LOAN", "WEALTH"]
NUM_BASE_CUSTOMERS = 30

# ── Name components ──────────────────────────────────────────────
FIRST_NAMES = [
    "Rohita", "Ankit", "Priya", "Vijay", "Sneha",
    "Rajesh", "Kavitha", "Arjun", "Divya", "Suresh",
    "Meera", "Ravi", "Lakshmi", "Arun", "Deepa",
    "Sanjay", "Nisha", "Manoj", "Pooja", "Vikram",
    "Asha", "Kiran", "Sunita", "Ganesh", "Rekha",
    "Amit", "Swati", "Prakash", "Jyoti", "Ramesh",
]

MIDDLE_NAMES = [
    "P.", "K.", "R.", "S.", "V.", "M.", "N.", "A.", "D.", "B.",
    "Prasad", "Kumar", "Rao", "Shankar", "Venkat",
]

LAST_NAMES = [
    "Raghavan", "Sharma", "Patel", "Iyer", "Reddy",
    "Nair", "Gupta", "Singh", "Joshi", "Menon",
    "Chauhan", "Verma", "Das", "Pillai", "Kulkarni",
    "Desai", "Mehta", "Bhat", "Rao", "Agarwal",
    "Mishra", "Srinivasan", "Chakraborty", "Banerjee", "Mukherjee",
    "Deshpande", "Patil", "Kaur", "Choudhury", "Tiwari",
]

CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
    "Bombay", "Bengaluru", "Calcutta", "Madras", "Poona",
]

CITY_VARIANTS = {
    "Mumbai": ["Mumbai", "Bombay", "mumbai", "MUMBAI"],
    "Bangalore": ["Bangalore", "Bengaluru", "bangalore", "BENGALURU"],
    "Chennai": ["Chennai", "Madras", "chennai", "CHENNAI"],
    "Kolkata": ["Kolkata", "Calcutta", "kolkata", "KOLKATA"],
    "Pune": ["Pune", "Poona", "pune", "PUNE"],
}

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "company.co.in"]


def generate_pan() -> str:
    """Generate a realistic-looking PAN (AAAAA9999A)."""
    letters = "".join(random.choices(string.ascii_uppercase, k=5))
    digits = "".join(random.choices(string.digits, k=4))
    last = random.choice(string.ascii_uppercase)
    return f"{letters}{digits}{last}"


def generate_mobile() -> str:
    """Generate Indian mobile number registered with Twilio WhatsApp."""
    return "9920602745"


def format_mobile_variant(mobile: str) -> str:
    """Apply random formatting to a mobile number."""
    variant = random.choice([
        mobile,
        f"+91 {mobile[:5]} {mobile[5:]}",
        f"+91-{mobile}",
        f"{mobile[:5]}-{mobile[5:]}",
        f"91{mobile}",
        f"0{mobile}",
        f"+91{mobile}",
    ])
    return variant


def generate_dob() -> date:
    """Generate a random DOB between 1960 and 2000."""
    start = date(1960, 1, 1)
    end = date(2000, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def format_dob_variant(d: date) -> str:
    """Return a random date format."""
    fmt = random.choice([
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ])
    return d.strftime(fmt)


def name_variant(first: str, middle: str | None, last: str) -> str:
    """Produce a name variation."""
    variant_type = random.choice([
        "full",
        "no_middle",
        "initial_first",
        "initial_middle",
        "typo",
        "caps",
    ])
    if variant_type == "full" and middle:
        return f"{first} {middle} {last}"
    elif variant_type == "no_middle":
        return f"{first} {last}"
    elif variant_type == "initial_first":
        return f"{first[0]}. {last}"
    elif variant_type == "initial_middle" and middle:
        return f"{first} {middle[0]}. {last}"
    elif variant_type == "typo":
        # Insert a typo in the first name
        if len(first) > 3:
            pos = random.randint(1, len(first) - 2)
            typo_char = random.choice(string.ascii_lowercase)
            return f"{first[:pos]}{typo_char}{first[pos+1:]} {last}"
        return f"{first} {last}"
    elif variant_type == "caps":
        full = f"{first} {last}"
        return random.choice([full.upper(), full.lower(), full.title()])
    return f"{first} {last}"


def email_variant(first: str, last: str) -> str:
    """Generate email variations."""
    domain = random.choice(EMAIL_DOMAINS)
    variant_type = random.choice([
        "standard",
        "uppercase",
        "with_dots",
        "with_numbers",
        "short",
    ])
    if variant_type == "standard":
        return f"{first.lower()}.{last.lower()}@{domain}"
    elif variant_type == "uppercase":
        return f"{first.upper()}@{domain}"
    elif variant_type == "with_dots":
        return f"{first.lower()}.{last.lower()[0]}@{domain}"
    elif variant_type == "with_numbers":
        return f"{first.lower()}{random.randint(1, 99)}@{domain}"
    elif variant_type == "short":
        return f"{first.lower()[0]}{last.lower()}@{domain}"
    return f"{first.lower()}@{domain}"


def generate_base_customers():
    """Generate base customer profiles."""
    customers = []
    used_pans = set()

    for i in range(NUM_BASE_CUSTOMERS):
        first = random.choice(FIRST_NAMES)
        middle = random.choice(MIDDLE_NAMES) if random.random() > 0.3 else None
        last = random.choice(LAST_NAMES)
        pan = generate_pan()
        while pan in used_pans:
            pan = generate_pan()
        used_pans.add(pan)

        mobile = generate_mobile()
        dob = generate_dob()
        city = random.choice(list(CITY_VARIANTS.keys()) + CITIES[:5])
        email = f"{first.lower()}.{last.lower()}@{random.choice(EMAIL_DOMAINS)}"
        segment = random.choice(["RETAIL", "AFFLUENT", "HNI", "ULTRA_HNI"])

        customers.append({
            "first": first,
            "middle": middle,
            "last": last,
            "pan": pan,
            "mobile": mobile,
            "dob": dob,
            "city": city,
            "email": email,
            "segment": segment,
        })

    return customers


def generate_records_for_system(
    system: str,
    base_customers: list,
    records_per_system: int,
) -> list[dict]:
    """
    Generate records for a specific source system.

    Each record is a variation of a base customer to simulate
    real-world data inconsistencies.
    """
    records = []
    selected = random.sample(
        base_customers,
        k=min(records_per_system, len(base_customers)),
    )

    for idx, cust in enumerate(selected):
        record = {"source_record_id": f"{system}-{idx+1:04d}"}

        # Name variation
        record["name"] = name_variant(cust["first"], cust["middle"], cust["last"])

        # PAN — sometimes missing
        if random.random() > 0.2:
            pan = cust["pan"]
            # Occasionally add formatting noise
            if random.random() > 0.9:
                pan = f"{pan[:5]} {pan[5:]}"  # space in PAN
            record["pan"] = pan
        else:
            record["pan"] = ""

        # Mobile — different formats
        record["mobile"] = format_mobile_variant(cust["mobile"])

        # Email — case and format variations
        if random.random() > 0.15:
            record["email"] = email_variant(cust["first"], cust["last"])
        else:
            record["email"] = ""

        # DOB — different formats, sometimes missing
        if random.random() > 0.2:
            record["dob"] = format_dob_variant(cust["dob"])
        else:
            record["dob"] = ""

        # City — aliases and capitalization
        city = cust["city"]
        if city in CITY_VARIANTS:
            record["city"] = random.choice(CITY_VARIANTS[city])
        else:
            record["city"] = random.choice([city, city.upper(), city.lower()])

        # Business & Financial attributes
        record["segment"] = cust.get("segment", random.choice(["RETAIL", "AFFLUENT", "HNI", "ULTRA_HNI"]))
        record["product_type"] = f"{system.title()} Account"
        bal = random.randint(25000, 2500000)
        record["balance_aum"] = str(bal)
        record["relationship_value"] = str(int(bal * random.uniform(1.1, 2.5)))
        record["last_activity_date"] = (date.today() - timedelta(days=random.randint(1, 180))).isoformat()
        record["rm_id"] = f"RM00{random.randint(1, 3)}"

        records.append(record)

    # Add a few extra unique records (not in base)
    for i in range(random.randint(2, 5)):
        extra_first = random.choice(FIRST_NAMES)
        extra_last = random.choice(LAST_NAMES)
        extra_bal = random.randint(10000, 1000000)
        records.append({
            "source_record_id": f"{system}-EXTRA-{i+1:04d}",
            "name": f"{extra_first} {extra_last}",
            "pan": generate_pan() if random.random() > 0.3 else "",
            "mobile": format_mobile_variant(generate_mobile()),
            "email": email_variant(extra_first, extra_last),
            "dob": format_dob_variant(generate_dob()) if random.random() > 0.2 else "",
            "city": random.choice(CITIES),
            "segment": random.choice(["RETAIL", "AFFLUENT", "HNI"]),
            "product_type": f"{system.title()} Standard",
            "balance_aum": str(extra_bal),
            "relationship_value": str(int(extra_bal * 1.5)),
            "last_activity_date": (date.today() - timedelta(days=random.randint(1, 90))).isoformat(),
            "rm_id": f"RM00{random.randint(1, 3)}",
        })

    return records


def generate_conflict_records() -> dict[str, list[dict]]:
    """
    Generate specific conflict scenarios for testing REVIEW logic.

    Returns a dict mapping system → list of records.
    """
    conflicts: dict[str, list[dict]] = {s: [] for s in SYSTEMS}

    # Scenario 1: Same name & mobile, different PAN → REVIEW
    conflicts["EQUITY"].append({
        "source_record_id": "EQ-CONFLICT-001",
        "name": "Vikram Mehta",
        "pan": "BBBBB1111B",
        "mobile": "9999988888",
        "email": "vikram.mehta@gmail.com",
        "dob": "1985-03-15",
        "city": "Mumbai",
    })
    conflicts["LOAN"].append({
        "source_record_id": "LN-CONFLICT-001",
        "name": "Vikram Mehta",
        "pan": "CCCCC2222C",
        "mobile": "9999988888",
        "email": "vikram.mehta@gmail.com",
        "dob": "1985-03-15",
        "city": "Bombay",
    })

    # Scenario 2: Same PAN but very different names → REVIEW
    conflicts["INSURANCE"].append({
        "source_record_id": "INS-CONFLICT-002",
        "name": "Aarav Singhania",
        "pan": "DDDDD3333D",
        "mobile": "8888877777",
        "email": "aarav.s@yahoo.com",
        "dob": "1990-07-20",
        "city": "Delhi",
    })
    conflicts["WEALTH"].append({
        "source_record_id": "WM-CONFLICT-002",
        "name": "Completely Different Person",
        "pan": "DDDDD3333D",
        "mobile": "7777766666",
        "email": "different@gmail.com",
        "dob": "1975-01-10",
        "city": "Kolkata",
    })

    # Scenario 3: Known match — exact data across systems
    for system in ["EQUITY", "MUTUAL_FUND", "WEALTH"]:
        conflicts[system].append({
            "source_record_id": f"{system[:2].upper()}-MATCH-003",
            "name": "Rohita Raghavan",
            "pan": "ABCDE1234F",
            "mobile": "+91 98765 43210",
            "email": "rohita@gmail.com",
            "dob": "1988-06-12",
            "city": "Bangalore",
        })

    # Variations of the same person
    conflicts["INSURANCE"].append({
        "source_record_id": "INS-MATCH-003",
        "name": "Rohita P. Raghavan",
        "pan": "",
        "mobile": "9876543210",
        "email": "ROHITA@gmail.com",
        "dob": "12/06/1988",
        "city": "Bengaluru",
    })
    conflicts["LOAN"].append({
        "source_record_id": "LN-MATCH-003",
        "name": "R. Raghavan",
        "pan": "ABCDE1234F",
        "mobile": "98765-43210",
        "email": "rohita@Gmail.COM",
        "dob": "1988-06-12",
        "city": "bangalore",
    })

    return conflicts


def write_csv(system: str, records: list[dict]):
    """Write records to a CSV file for a given system."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / f"{system.lower()}_records.csv"

    fieldnames = [
        "source_record_id", "name", "pan", "mobile", "email", "dob", "city",
        "segment", "product_type", "balance_aum", "relationship_value",
        "last_activity_date", "rm_id"
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)

    print(f"  [OK] {filepath.name}: {len(records)} records")


def main():
    """Generate all seed data CSV files."""
    print("=" * 60)
    print("Nexus360 — Seed Data Generator")
    print("=" * 60)

    # Generate base customer pool
    base_customers = generate_base_customers()
    print(f"\nGenerated {len(base_customers)} base customer profiles")

    # Generate conflict/test scenarios
    conflict_records = generate_conflict_records()

    # Generate records for each system
    all_records: dict[str, list[dict]] = {}
    records_per_system = max(20, NUM_BASE_CUSTOMERS - 5)

    print(f"\nGenerating ~{records_per_system} records per system...\n")

    for system in SYSTEMS:
        system_records = generate_records_for_system(
            system, base_customers, records_per_system
        )
        # Add conflict records
        system_records.extend(conflict_records.get(system, []))
        all_records[system] = system_records
        write_csv(system, system_records)

    total = sum(len(recs) for recs in all_records.values())
    print(f"\n{'=' * 60}")
    print(f"Total records generated: {total}")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")
    print(f"{'=' * 60}")
    print("\nTo ingest, use:")
    print("  curl -X POST http://localhost:8000/api/v1/ingest \\")
    print("       -F 'source_system=EQUITY' \\")
    print("       -F 'file=@scripts/data/equity_records.csv'")


if __name__ == "__main__":
    main()
