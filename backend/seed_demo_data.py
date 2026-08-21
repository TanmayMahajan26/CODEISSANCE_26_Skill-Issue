import sys
import os
import random
from datetime import datetime, date

# Add backend directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, engine
from app.db.models.base import Base
from app.db.models.source_record import SourceRecord
from app.db.models.golden_record import GoldenRecord
from app.db.models.identity_edge import IdentityEdge
from app.db.models.opportunity import Opportunity
from app.db.models.audit import AuditLog
from app.db.models.review_queue import ReviewQueueItem
from app.db.models.config_rule import ConfigRule
from app.db.models.user import User, UserRole
from app.core.security import get_password_hash

from app.services.matching.deterministic import run_deterministic_matching
from app.services.matching.probabilistic import run_probabilistic_matching
from app.services.matching.semantic import run_semantic_matching
from app.services.matching.graph_clustering import run_graph_clustering
from app.services.golden_record_builder import build_golden_records
from app.services.opportunity_engine import generate_opportunities

# ──────────────────────────────────────────────
# Helper data pools for realistic generation
# ──────────────────────────────────────────────
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Ananya", "Diya", "Myra", "Sara", "Aarohi", "Anika", "Kavya", "Riya", "Isha", "Prisha",
    "Rahul", "Amit", "Suresh", "Vikram", "Deepak", "Manish", "Nitin", "Pradeep", "Gaurav", "Sachin",
    "Priya", "Neha", "Pooja", "Divya", "Swati", "Anjali", "Meera", "Sunita", "Rekha", "Lakshmi",
    "Karan", "Rohan", "Mohit", "Akash", "Harsh", "Yash", "Dev", "Raj", "Kunal", "Varun",
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Joshi", "Mehta", "Shah", "Reddy",
    "Nair", "Iyer", "Rao", "Das", "Bose", "Chakraborty", "Malhotra", "Kapoor", "Agarwal", "Bansal",
    "Khanna", "Saxena", "Tiwari", "Pandey", "Mishra", "Sinha", "Mukherjee", "Ghosh", "Chatterjee", "Roy",
]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Indore", "Kochi", "Nagpur", "Vadodara"]
SEGMENTS = ["RETAIL", "HNI", "SME", "CORPORATE"]
SYSTEMS = ["CORE_BANKING", "CRM", "LOAN_ORIGINATION", "INSURANCE", "WEALTH"]
PRODUCTS_POOL = [
    ["SAVINGS"], ["SAVINGS", "FIXED_DEPOSIT"], ["CURRENT"], ["SALARY_ACCOUNT"],
    ["Equity"], ["Mutual Fund"], ["Equity", "Mutual Fund"], ["TERM_LIFE"],
    ["HOME_LOAN"], ["AUTO_LOAN"], ["PERSONAL_LOAN"], ["SAVINGS", "Equity"],
    ["SAVINGS", "FIXED_DEPOSIT", "Equity", "Mutual Fund"], ["SAVINGS", "Mutual Fund", "TERM_LIFE"],
]


def generate_pan():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    return ''.join(random.choices(chars, k=5)) + ''.join(random.choices(digits, k=4)) + random.choice(chars)


def generate_mobile():
    return str(random.choice([9, 8, 7])) + ''.join(str(random.randint(0, 9)) for _ in range(9))


def generate_email(first, last):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "corporate.in", "example.com"]
    sep = random.choice([".", "_", ""])
    return f"{first.lower()}{sep}{last.lower()[:3]}@{random.choice(domains)}"


def random_dob():
    year = random.randint(1960, 2000)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


def clear_db(db):
    print("Clearing existing data...")
    db.query(Opportunity).delete()
    db.query(ReviewQueueItem).delete()
    db.query(IdentityEdge).delete()
    # Null out FKs on source_records BEFORE deleting golden records
    db.query(SourceRecord).update({SourceRecord.golden_record_id: None})
    db.query(SourceRecord).delete()
    db.query(GoldenRecord).delete()
    db.query(AuditLog).delete()
    db.query(User).delete()
    db.query(ConfigRule).delete()
    db.commit()


def seed_data(db):
    print("Seeding demo data...")

    # 0. Seed Users
    hashed_pw = get_password_hash("strongpassword")
    admin = User(email="admin@kovi.in", password_hash=hashed_pw, full_name="Admin User", role=UserRole.ADMIN)
    manager = User(email="manager@kovi.in", password_hash=hashed_pw, full_name="Ravi Kapoor", role=UserRole.MANAGER, team_id="WEST_01")
    rm1 = User(email="rm1@kovi.in", password_hash=hashed_pw, full_name="Priya Nair", role=UserRole.RM, team_id="WEST_01")
    rm2 = User(email="rm2@kovi.in", password_hash=hashed_pw, full_name="Rahul Sharma", role=UserRole.RM, team_id="WEST_01")
    db.add_all([admin, manager, rm1, rm2])
    db.commit()
    db.refresh(rm1)
    db.refresh(rm2)
    db.refresh(manager)
    db.refresh(admin)

    # Helper function to get an RM id
    def get_rm():
        return random.choice([rm1.id, rm2.id])


    all_records = []

    # ─── Scenario 1: Multi-system customer (Deterministic PAN match) ───
    pan1 = "ABCDE1234F"
    rm_s1 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_s1, source_system="CORE_BANKING", source_id="CB-001",
                     raw_name="Rajesh Kumar", name="rajesh kumar", dob=date(1985, 5, 15),
                     pan=pan1, email="rajesh.kumar@gmail.com", mobile="9876543210",
                     city="Mumbai", segment="RETAIL", account_value=250000.0,
                     products=["SAVINGS", "FIXED_DEPOSIT"]),
        SourceRecord(assigned_rm_id=rm_s1, source_system="CRM", source_id="CRM-101",
                     raw_name="Rajesh H. Kumar", name="rajesh h kumar", dob=date(1985, 5, 15),
                     pan=pan1, email="rajesh.kumar@gmail.com", mobile="9876543210",
                     city="Mumbai", segment="RETAIL", account_value=0.0, products=[]),
        SourceRecord(assigned_rm_id=rm_s1, source_system="LOAN_ORIGINATION", source_id="LO-999",
                     raw_name="R. Kumar", name="r kumar", dob=date(1985, 5, 15),
                     pan=pan1, email="rkumar@corporate.in", mobile="9876543211",
                     city="Navi Mumbai", segment="RETAIL", account_value=3500000.0,
                     products=["HOME_LOAN"]),
    ])

    # ─── Scenario 2: HNI with wealth + insurance (Deterministic PAN match) ───
    pan2 = "PKLMN9876A"
    rm_s2 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_s2, source_system="CORE_BANKING", source_id="CB-002",
                     raw_name="Priya Sharma", name="priya sharma", dob=date(1990, 8, 22),
                     pan=pan2, email="priya.s@gmail.com", mobile="9998887776",
                     city="Delhi", segment="HNI", account_value=4500000.0,
                     products=["Equity", "Mutual Fund"]),
        SourceRecord(assigned_rm_id=rm_s2, source_system="CRM", source_id="CRM-102",
                     raw_name="Sharma Priya", name="sharma priya", dob=date(1990, 8, 22),
                     pan=pan2, email="priyas@gmail.com", mobile="9998887776",
                     city="New Delhi", segment="HNI", account_value=0.0, products=[]),
    ])

    # ─── Scenario 3: Isolated Record (No matches — Sanjay) ───
    all_records.append(
        SourceRecord(assigned_rm_id=get_rm(), source_system="CORE_BANKING", source_id="CB-003",
                     raw_name="Sanjay Mehta", name="sanjay mehta", dob=date(1978, 12, 5),
                     pan="XYZAB5678C", email="sanjay.mehta@corporate.in", mobile="8887776665",
                     city="Bangalore", segment="SME", account_value=800000.0,
                     products=["CURRENT"])
    )

    # ─── Scenario 4: Conflict — same mobile/email, different people → Review Queue ───
    rm_s4 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_s4, source_system="CRM", source_id="CRM-401",
                     raw_name="Amit Patel", name="amit patel", dob=date(1982, 1, 10),
                     pan="APATL1234Z", email="amit.patel@example.com", mobile="9090909090",
                     city="Ahmedabad", segment="RETAIL", account_value=120000.0, products=["SAVINGS"]),
        SourceRecord(assigned_rm_id=rm_s4, source_system="LOAN_ORIGINATION", source_id="LO-402",
                     raw_name="Sunil Verma", name="sunil verma", dob=date(1995, 7, 15),
                     pan="SVERM9876X", email="amit.patel@example.com", mobile="9090909090",
                     city="Pune", segment="RETAIL", account_value=450000.0, products=["AUTO_LOAN"]),
    ])

    # ─── Scenario 5: Wealth HNI (missing Wealth Management product → Opportunity) ───
    pan5 = "SGUPT5555Y"
    rm_s5 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_s5, source_system="CORE_BANKING", source_id="CB-501",
                     raw_name="Vikram Singhania", name="vikram singhania", dob=date(1965, 3, 21),
                     pan=pan5, email="vikram.s@enterprise.com", mobile="9898989898",
                     city="Mumbai", segment="HNI", account_value=8500000.0,
                     products=["SAVINGS", "FIXED_DEPOSIT", "Equity", "Mutual Fund"]),
        SourceRecord(assigned_rm_id=rm_s5, source_system="INSURANCE", source_id="INS-502",
                     raw_name="V. Singhania", name="v singhania", dob=date(1965, 3, 21),
                     pan=pan5, email="vikram.s2@enterprise.com", mobile="9898989898",
                     city="Mumbai", segment="HNI", account_value=1200000.0,
                     products=["TERM_LIFE"]),
    ])

    # ─── Scenario 6: Credit Card Prospect ───
    all_records.append(
        SourceRecord(assigned_rm_id=get_rm(), source_system="CORE_BANKING", source_id="CB-601",
                     raw_name="Neha Singh", name="neha singh", dob=date(1998, 11, 5),
                     pan="NSING8888P", email="neha.singh98@gmail.com", mobile="9191919191",
                     city="Bangalore", segment="RETAIL", account_value=280000.0,
                     products=["SALARY_ACCOUNT"])
    )

    # ─── Scenario 7: Email+DOB deterministic match (different PAN systems) ───
    shared_email7 = "kiran.desai@outlook.com"
    shared_dob7 = date(1988, 4, 17)
    rm_s7 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_s7, source_system="CORE_BANKING", source_id="CB-701",
                     raw_name="Kiran Desai", name="kiran desai", dob=shared_dob7,
                     pan="KDESA7701Q", email=shared_email7, mobile="9292929292",
                     city="Pune", segment="RETAIL", account_value=350000.0,
                     products=["SAVINGS", "Mutual Fund"]),
        SourceRecord(assigned_rm_id=rm_s7, source_system="WEALTH", source_id="WM-702",
                     raw_name="Kiran V Desai", name="kiran v desai", dob=shared_dob7,
                     pan=None, email=shared_email7, mobile="9292929293",
                     city="Pune", segment="HNI", account_value=2200000.0,
                     products=["Equity", "Mutual Fund"]),
    ])

    # ─── Scenario 8: Mobile+DOB deterministic match ───
    shared_mobile8 = "8181818181"
    shared_dob8 = date(1975, 9, 3)
    rm_s8 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_s8, source_system="CRM", source_id="CRM-801",
                     raw_name="Deepak Joshi", name="deepak joshi", dob=shared_dob8,
                     pan="DJOSH8801R", email="deepak.j@yahoo.com", mobile=shared_mobile8,
                     city="Jaipur", segment="SME", account_value=1100000.0,
                     products=["CURRENT", "FIXED_DEPOSIT"]),
        SourceRecord(assigned_rm_id=rm_s8, source_system="LOAN_ORIGINATION", source_id="LO-802",
                     raw_name="D. Joshi", name="d joshi", dob=shared_dob8,
                     pan=None, email="djoshi@corporate.in", mobile=shared_mobile8,
                     city="Jaipur", segment="SME", account_value=5000000.0,
                     products=["PERSONAL_LOAN"]),
    ])

    # ─── Scenarios 9-18: 10 Specific Discrepancy / Edge Cases for Review Demo ───
    
    # Case 1: Probabilistic - Similar Name + Same DOB (Typo in Name)
    rm_case1 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case1, source_system="CORE_BANKING", source_id="CB-901",
                     raw_name="Abhishek Sharma", name="abhishek sharma", dob=date(1990, 5, 10),
                     pan="ABHIS9010A", email="abhi.sharma@test.com", mobile="9876543210",
                     city="Delhi", segment="RETAIL", account_value=50000.0, products=["SAVINGS"]),
        SourceRecord(assigned_rm_id=rm_case1, source_system="CRM", source_id="CRM-902",
                     raw_name="Abishek Sharma", name="abishek sharma", dob=date(1990, 5, 10),
                     pan=None, email="abhi.s@test.com", mobile="9876543211",
                     city="Delhi", segment="RETAIL", account_value=150000.0, products=["PERSONAL_LOAN"])
    ])

    # Case 2: Probabilistic - Swapped First/Last Name + Same Mobile
    rm_case2 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case2, source_system="CRM", source_id="CRM-1001",
                     raw_name="Kumar Raj", name="kumar raj", dob=date(1985, 8, 20),
                     pan="KUMAR8520B", email="kumar.r@test.com", mobile="9123456780",
                     city="Mumbai", segment="SME", account_value=250000.0, products=["CURRENT"]),
        SourceRecord(assigned_rm_id=rm_case2, source_system="WEALTH", source_id="WM-1002",
                     raw_name="Raj Kumar", name="raj kumar", dob=date(1982, 1, 1), # diff dob
                     pan=None, email="raj.kumar@test.com", mobile="9123456780",
                     city="Mumbai", segment="SME", account_value=1250000.0, products=["Equity"])
    ])

    # Case 3: Semantic - Phonetic match (Rhea / Riya) + Same Email
    rm_case3 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case3, source_system="CORE_BANKING", source_id="CB-1101",
                     raw_name="Rhea Kapoor", name="rhea kapoor", dob=date(1995, 12, 12),
                     pan="RHEAK9512C", email="rhea.k@test.com", mobile="9988776655",
                     city="Pune", segment="RETAIL", account_value=75000.0, products=["SAVINGS"]),
        SourceRecord(assigned_rm_id=rm_case3, source_system="INSURANCE", source_id="INS-1102",
                     raw_name="Riya Kapur", name="riya kapur", dob=date(1995, 12, 12),
                     pan=None, email="rhea.k@test.com", mobile="9988776600",
                     city="Pune", segment="RETAIL", account_value=50000.0, products=["TERM_LIFE"])
    ])

    # Case 4: Deterministic Match but completely different names (Name Change after marriage)
    rm_case4 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case4, source_system="CORE_BANKING", source_id="CB-1201",
                     raw_name="Pooja Gupta", name="pooja gupta", dob=date(1992, 3, 14),
                     pan="POOJA9214D", email="pooja.g@test.com", mobile="9898981122",
                     city="Chennai", segment="RETAIL", account_value=300000.0, products=["SAVINGS"]),
        SourceRecord(assigned_rm_id=rm_case4, source_system="LOAN_ORIGINATION", source_id="LO-1202",
                     raw_name="Pooja Agarwal", name="pooja agarwal", dob=date(1992, 3, 14),
                     pan="POOJA9214D", email="pooja.a@test.com", mobile="9898981122",
                     city="Chennai", segment="RETAIL", account_value=1500000.0, products=["HOME_LOAN"])
    ])

    # Case 5: Non-Match - Same Name, Different everything else (Common Name Collision)
    rm_case5 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case5, source_system="CRM", source_id="CRM-1301",
                     raw_name="Ravi Kumar", name="ravi kumar", dob=date(1970, 1, 1),
                     pan="RAVIK7001E", email="ravi1@test.com", mobile="9000000001",
                     city="Delhi", segment="HNI", account_value=5000000.0, products=["Mutual Fund"]),
        SourceRecord(assigned_rm_id=rm_case5, source_system="CORE_BANKING", source_id="CB-1302",
                     raw_name="Ravi Kumar", name="ravi kumar", dob=date(1999, 12, 31),
                     pan="RAVIK9912F", email="ravi99@test.com", mobile="9000000002",
                     city="Bangalore", segment="RETAIL", account_value=10000.0, products=["SAVINGS"])
    ])

    # Case 6: Non-Match - Same Email (Family shared email), Different Name/DOB
    rm_case6 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case6, source_system="CORE_BANKING", source_id="CB-1401",
                     raw_name="Anil Sharma", name="anil sharma", dob=date(1965, 6, 15),
                     pan="ANILS6515G", email="sharmafamily@test.com", mobile="9111111111",
                     city="Kolkata", segment="SME", account_value=800000.0, products=["CURRENT"]),
        SourceRecord(assigned_rm_id=rm_case6, source_system="CRM", source_id="CRM-1402",
                     raw_name="Sunita Sharma", name="sunita sharma", dob=date(1970, 4, 10),
                     pan="SUNIT7041H", email="sharmafamily@test.com", mobile="9111111112",
                     city="Kolkata", segment="RETAIL", account_value=400000.0, products=["SAVINGS"])
    ])

    # Case 7: Probabilistic Match - Missing / Null data with slight name variation
    rm_case7 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case7, source_system="WEALTH", source_id="WM-1501",
                     raw_name="Mohd. Tariq", name="mohd tariq", dob=date(1980, 2, 28),
                     pan=None, email=None, mobile="9222222222",
                     city="Hyderabad", segment="HNI", account_value=3000000.0, products=["Equity"]),
        SourceRecord(assigned_rm_id=rm_case7, source_system="CORE_BANKING", source_id="CB-1502",
                     raw_name="Mohammed Tariq", name="mohammed tariq", dob=date(1980, 2, 28),
                     pan=None, email="tariq@test.com", mobile=None,
                     city="Hyderabad", segment="HNI", account_value=500000.0, products=["SAVINGS"])
    ])

    # Case 8: Semantic - Initials vs Full Name
    rm_case8 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case8, source_system="INSURANCE", source_id="INS-1601",
                     raw_name="S. K. Iyer", name="s k iyer", dob=date(1955, 10, 10),
                     pan="SKIYE5510I", email="iyer.sk@test.com", mobile="9333333333",
                     city="Chennai", segment="RETAIL", account_value=100000.0, products=["TERM_LIFE"]),
        SourceRecord(assigned_rm_id=rm_case8, source_system="CRM", source_id="CRM-1602",
                     raw_name="Srinivasan Krishnan Iyer", name="srinivasan krishnan iyer", dob=date(1955, 10, 10),
                     pan=None, email="iyer.sk@test.com", mobile="9333333334",
                     city="Chennai", segment="RETAIL", account_value=200000.0, products=["SAVINGS"])
    ])

    # Case 9: Probabilistic - Nickname match (Bob vs Robert)
    rm_case9 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case9, source_system="CORE_BANKING", source_id="CB-1701",
                     raw_name="Robert Dsouza", name="robert dsouza", dob=date(1988, 7, 7),
                     pan="ROBER8807J", email="bob.d@test.com", mobile="9444444444",
                     city="Goa", segment="RETAIL", account_value=120000.0, products=["SAVINGS"]),
        SourceRecord(assigned_rm_id=rm_case9, source_system="LOAN_ORIGINATION", source_id="LO-1702",
                     raw_name="Bob Dsouza", name="bob dsouza", dob=date(1988, 7, 7),
                     pan=None, email="bob.d@test.com", mobile=None,
                     city="Goa", segment="RETAIL", account_value=800000.0, products=["PERSONAL_LOAN"])
    ])

    # Case 10: Non-Match - Identical PAN typo collision (Data entry error)
    rm_case10 = get_rm()
    all_records.extend([
        SourceRecord(assigned_rm_id=rm_case10, source_system="WEALTH", source_id="WM-1801",
                     raw_name="Gaurav Menon", name="gaurav menon", dob=date(1991, 9, 9),
                     pan="TYPOX1234Z", email="g.menon@test.com", mobile="9555555555",
                     city="Kochi", segment="HNI", account_value=4000000.0, products=["Mutual Fund"]),
        SourceRecord(assigned_rm_id=rm_case10, source_system="CORE_BANKING", source_id="CB-1802",
                     raw_name="Amitabh Bachchan", name="amitabh bachchan", dob=date(1942, 10, 11),
                     pan="TYPOX1234Z",  # Accidentally entered same PAN
                     email="bigb@test.com", mobile="9666666666",
                     city="Mumbai", segment="HNI", account_value=9900000.0, products=["SAVINGS"])
    ])

    # ─── Scenarios 11-40: Generate more unique customers for data richness ───
    used_pans = {r.pan for r in all_records if r.pan}
    scenario_id = 1900
    for i in range(30):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"
        pan = generate_pan()
        while pan in used_pans:
            pan = generate_pan()
        used_pans.add(pan)
        mobile = generate_mobile()
        email = generate_email(first, last)
        dob = random_dob()
        city = random.choice(CITIES)
        segment = random.choice(SEGMENTS)
        system = random.choice(SYSTEMS[:3])  # Core, CRM, Loan
        products = random.choice(PRODUCTS_POOL)
        value = round(random.uniform(50000, 5000000), 2)
        rm_gen = get_rm()

        all_records.append(
            SourceRecord(assigned_rm_id=rm_gen, source_system=system, source_id=f"GEN-{scenario_id + i}",
                         raw_name=full_name, name=full_name.lower(), dob=dob,
                         pan=pan, email=email, mobile=mobile,
                         city=city, segment=segment, account_value=value,
                         products=products)
        )

        # 40% chance of a second record from different system to create multi-source matches
        if random.random() < 0.4:
            sys2 = random.choice([s for s in SYSTEMS if s != system])
            all_records.append(
                SourceRecord(assigned_rm_id=rm_gen, source_system=sys2, source_id=f"GEN-{scenario_id + i}B",
                             raw_name=full_name, name=full_name.lower(), dob=dob,
                             pan=pan, email=email, mobile=mobile,
                             city=city, segment=segment, account_value=round(random.uniform(10000, 2000000), 2),
                             products=random.choice(PRODUCTS_POOL))
            )

    db.add_all(all_records)

    # Seed ALL default config rules
    config_defaults = {
        "matching_thresholds": {"auto_merge": 0.85, "manual_review": 0.60},
        "matching_weights": {
            "pan": 0.35, "mobile": 0.20, "email": 0.15, "name_jaro": 0.12,
            "name_semantic": 0.08, "dob": 0.05, "city": 0.03, "segment": 0.02,
        },
        "opportunity_rules": {
            "Insurance": {"type": "CROSS_SELL", "min_relationship_value": 100000, "required_products_any": ["Equity", "Mutual Fund"]},
            "Wealth Management": {"type": "UPSELL", "min_relationship_value": 2500000, "required_products_all": ["Equity", "Mutual Fund"]},
            "Loan": {"type": "CROSS_SELL", "min_relationship_value": 200000},
            "Credit Card": {"type": "CROSS_SELL", "min_relationship_value": 50000},
        },
        "scoring_weights": {
            "relationship_value": 0.35, "product_affinity": 0.25, "recency": 0.20, "engagement": 0.20,
        },
        "survivorship_rules": {
            "name": {"strategy": "SOURCE_PRIORITY", "priority": ["WEALTH", "CORE_BANKING", "CRM"]},
            "mobile": {"strategy": "MOST_RECENT"},
            "email": {"strategy": "MOST_RECENT"},
            "dob": {"strategy": "MOST_FREQUENT"},
            "city": {"strategy": "SOURCE_PRIORITY", "priority": ["CORE_BANKING", "LOAN_ORIGINATION"]},
            "segment": {"strategy": "HIGHEST_VALUE_SOURCE"},
        },
    }
    for rule_type, config in config_defaults.items():
        db.add(ConfigRule(rule_type=rule_type, config=config, version=1))

    # Seed initial audit log so audit page isn't blank
    db.add(AuditLog(
        actor_id=admin.id,
        actor_role="ADMIN",
        action_type="SYSTEM_INIT",
        entity_type="System",
        entity_id="kovi-v1",
        description="System initialized and demo data seeded",
    ))

    db.commit()
    print(f"Demo data seeded! {len(all_records)} Source Records inserted.")

    # Run the resolution pipeline on a FRESH session
    print("Running Resolution Pipeline automatically...")
    pipeline_db = SessionLocal()
    try:
        run_deterministic_matching(pipeline_db)
        run_probabilistic_matching(pipeline_db)
        run_semantic_matching(pipeline_db)
        clusters = run_graph_clustering(pipeline_db)
        build_golden_records(pipeline_db, clusters)
        generate_opportunities(pipeline_db)
    finally:
        pipeline_db.close()
    print("Pipeline complete. Golden Records and Opportunities are now ready!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        clear_db(db)
        seed_data(db)
    finally:
        db.close()
