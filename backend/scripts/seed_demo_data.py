import asyncio
import os
import sys
from datetime import datetime, timezone, date
import json

# Add parent directory to path so imports work when running from scripts folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.database import async_session_factory, Base, engine
from app.models import (
    GoldenCustomer, SourceRecord, MatchDecision, ReviewCase, 
    Opportunity, AuditLog, SourceSystem, GoldenCustomerStatus,
    Decision, ReviewStatus, ReviewPriority, ReviewType,
    OpportunityType, OpportunityStatus, AuditAction
)
from app.models.review_case import VerificationClassification, VerificationStatus

async def clear_database(session):
    await session.execute(text("DELETE FROM audit_logs"))
    await session.execute(text("DELETE FROM opportunities"))
    await session.execute(text("DELETE FROM review_cases"))
    await session.execute(text("DELETE FROM match_decisions"))
    await session.execute(text("DELETE FROM source_records"))
    await session.execute(text("DELETE FROM golden_customers"))
    await session.commit()

async def seed_data():
    async with async_session_factory() as session:
        print("Clearing database...")
        await clear_database(session)
        print("Database cleared. Starting seed...")

        # ---------------------------------------------------------
        # CUSTOMER 1 - ROHIT PRAKASH RAGHAVAN (AUTO MATCH)
        # ---------------------------------------------------------
        rohit = GoldenCustomer(
            golden_customer_id="GOLD-000101",
            canonical_name="Rohit Prakash Raghavan",
            canonical_city="Mumbai",
            total_relationship_value=12800000.00,
            assigned_rm_id="RM-MUM-04",
            canonical_pan="ABCDE1234F",
            canonical_mobile="9812345670",
            canonical_email="rohit.raghavan@example.demo"
        )
        session.add(rohit)
        await session.flush()
        
        sr_rohit_eq = SourceRecord(
            source_system=SourceSystem.EQUITY, source_record_id="EQ-R-01", original_name="Rohit P. Raghavan", original_pan="ABCDE1234F", original_mobile="9812345670", original_email="rohit.raghavan@example.demo", original_city="Mumbai"
        )
        sr_rohit_mf = SourceRecord(
            source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-R-01", original_name="Rohit Prakash Raghavan", original_pan="ABCDE1234F", original_mobile="+91 98123 45670", original_email="rohit.raghavan@example.demo", original_city="Bombay"
        )
        sr_rohit_wl = SourceRecord(
            source_system=SourceSystem.WEALTH, source_record_id="WL-R-01", original_name="Rohit Raghavan", original_pan="ABCDE1234F", original_mobile="9812345670", original_email="rohit.raghavan@example.demo", original_city="Mumbai"
        )
        session.add_all([sr_rohit_eq, sr_rohit_mf, sr_rohit_wl])
        await session.flush()

        md_rohit = MatchDecision(
            record_a_id=sr_rohit_eq.id, record_b_id=sr_rohit_mf.id, decision=Decision.MATCH, final_score=0.97,
            reasoning={"mobile": "formatting difference", "pan": "exact match", "name": "abbreviation"},
            pan_match=1.0, mobile_match=1.0, email_match=1.0, name_similarity=0.92, name_semantic_similarity=0.96, dob_match=0.0, city_similarity=1.0
        )
        session.add(md_rohit)

        opp_rohit = Opportunity(
            golden_customer_id=rohit.golden_customer_id, opportunity_type=OpportunityType.CROSS_SELL, product_recommended="Wealth Management PMS", potential_value=5000000, score=0.92, ai_reasoning="Customer has significant Equity and Mutual Fund holdings but no PMS allocation.", status=OpportunityStatus.NEW
        )
        session.add(opp_rohit)

        # ---------------------------------------------------------
        # CUSTOMER 2 - SUNITA MEHRA (AI VERIFIED -> MERGED)
        # ---------------------------------------------------------
        sunita = GoldenCustomer(
            golden_customer_id="GOLD-000102", canonical_name="Sunita Mehra", canonical_city="Pune", total_relationship_value=45000000.00, assigned_rm_id="RM-PUN-02", canonical_pan="BKMPM1920P", canonical_mobile="9822012345"
        )
        session.add(sunita)
        await session.flush()

        sr_sun_wl = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-S-01", original_name="Sunita Mehra", original_pan="BKMPM1920P", original_mobile="9822012345", original_email="sunita.mehra@example.demo")
        sr_sun_mf = SourceRecord(source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-S-01", original_name="Sunita Mehara", original_pan="BKMPM1920P", original_mobile="9822012345", original_email="sunita.mehra@example.demo")
        sr_sun_ins = SourceRecord(source_system=SourceSystem.INSURANCE, source_record_id="INS-S-01", original_name="S. Mehra", original_pan="BKMPM1920P", original_mobile="+91-98220-12345", original_email="sunita.mehra@example.demo")
        session.add_all([sr_sun_wl, sr_sun_mf, sr_sun_ins])
        await session.flush()

        md_sun = MatchDecision(
            record_a_id=sr_sun_wl.id, record_b_id=sr_sun_mf.id, decision=Decision.MATCH, final_score=0.89,
            reasoning={"name": "minor spelling variation"},
            pan_match=1.0, mobile_match=1.0, email_match=1.0, name_similarity=0.95, name_semantic_similarity=0.98, dob_match=0.0, city_similarity=0.0
        )
        session.add(md_sun)
        await session.flush()

        rev_sun = ReviewCase(
            match_decision_id=md_sun.id, priority=ReviewPriority.LOW, status=ReviewStatus.APPROVED,
            review_type=ReviewType.AI_FLAGGED, verification_classification=VerificationClassification.AI_VERIFICATION_ELIGIBLE, verification_status=VerificationStatus.VERIFIED,
            ai_call_result={"summary": "Customer confirmed: My full legal name is Sunita Mehra.", "outcome": "VERIFIED_EXPLANATION", "language": "Hindi"},
            ai_call_confidence="94%", details={"discrepancy": "Minor spelling variation."}
        )
        session.add(rev_sun)

        opp_sun = Opportunity(
            golden_customer_id=sunita.golden_customer_id, opportunity_type=OpportunityType.UPSELL, product_recommended="Structured Debt & Loan Against Securities", potential_value=150000, score=0.88, status=OpportunityStatus.NEW
        )
        session.add(opp_sun)

        # ---------------------------------------------------------
        # CUSTOMER 3 - VIKRAM ADITYA SINGHANIA (PAN CONFLICT)
        # ---------------------------------------------------------
        vikram = GoldenCustomer(
            golden_customer_id="GOLD-000103", canonical_name="Vikram Aditya Singhania", canonical_city="Bengaluru", total_relationship_value=89000000.00, assigned_rm_id="RM-BLR-01"
        )
        session.add(vikram)
        await session.flush()

        sr_vik_eq = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-V-01", original_name="Vikram Aditya Singhania", original_pan="AAACS1928L", original_mobile="9811234567", original_dob=date(1985,6,12), original_city="Bengaluru")
        sr_vik_mf = SourceRecord(source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-V-01", original_name="Vikram A. Singhania", original_pan="AAACS1928K", original_mobile="9811234567", original_dob=date(1985,6,12), original_city="Bangalore")
        session.add_all([sr_vik_eq, sr_vik_mf])
        await session.flush()

        md_vik = MatchDecision(
            record_a_id=sr_vik_eq.id, record_b_id=sr_vik_mf.id, decision=Decision.REVIEW, final_score=0.76,
            reasoning={"pan": "conflict by 1 character"},
            pan_match=0.0, mobile_match=1.0, email_match=0.85, name_similarity=0.92, name_semantic_similarity=0.94, dob_match=1.0, city_similarity=1.0
        )
        session.add(md_vik)
        await session.flush()

        rev_vik = ReviewCase(
            match_decision_id=md_vik.id, priority=ReviewPriority.HIGH, status=ReviewStatus.PENDING,
            review_type=ReviewType.ATTRIBUTE_CONFLICT, verification_classification=VerificationClassification.HUMAN_VERIFICATION_REQUIRED, verification_status=VerificationStatus.HUMAN_VERIFICATION_REQUIRED,
            details={"discrepancy": "PAN differs by one character.", "reason": "PAN conflict must have high importance", "score": 0.76}
        )
        session.add(rev_vik)

        opp_vik = Opportunity(
            golden_customer_id=vikram.golden_customer_id, opportunity_type=OpportunityType.PROTECTION, product_recommended="Keyman Insurance & Corporate Trust", potential_value=20000000, score=0.85, status=OpportunityStatus.NEW
        )
        session.add(opp_vik)

        # ---------------------------------------------------------
        # CUSTOMER 4 - ANANYA SHAH
        # ---------------------------------------------------------
        ananya = GoldenCustomer(golden_customer_id="GOLD-000104", canonical_name="Ananya Shah", canonical_city="Ahmedabad", total_relationship_value=27500000.00)
        session.add(ananya)
        await session.flush()

        sr_an_ins = SourceRecord(source_system=SourceSystem.INSURANCE, source_record_id="INS-A-01", original_name="Ananya Shah", original_pan="PQRSX4567M", original_mobile="9876543210")
        sr_an_eq = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-A-01", original_name="Ananya S. Shah", original_pan="PQRSX4567M", original_mobile="9876543210")
        session.add_all([sr_an_ins, sr_an_eq])
        await session.flush()

        md_an = MatchDecision(
            record_a_id=sr_an_ins.id, record_b_id=sr_an_eq.id, decision=Decision.REVIEW, final_score=0.94,
            pan_match=0.0, mobile_match=1.0, email_match=0.0, name_similarity=0.88, name_semantic_similarity=0.92, dob_match=0.0, city_similarity=0.0
        )
        session.add(md_an)
        await session.flush()

        rev_an = ReviewCase(
            match_decision_id=md_an.id, priority=ReviewPriority.LOW, status=ReviewStatus.PENDING,
            review_type=ReviewType.AI_FLAGGED, verification_classification=VerificationClassification.AI_VERIFICATION_ELIGIBLE, verification_status=VerificationStatus.PENDING,
            details={"discrepancy": "DOB format variation.", "score": 0.94}
        )
        session.add(rev_an)

        # ---------------------------------------------------------
        # CUSTOMER 5 - ARJUN MALHOTRA
        # ---------------------------------------------------------
        arjun = GoldenCustomer(golden_customer_id="GOLD-000105", canonical_name="Arjun Malhotra", canonical_city="Delhi", total_relationship_value=9500000.00)
        session.add(arjun)
        await session.flush()

        sr_arj_1 = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-A-01", original_name="Arjun Malhotra", original_pan="LMNOP6789Q", original_mobile="9988776655")
        sr_arj_2 = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-A-02", original_name="Arjun Malhotra", original_pan="LMNOP6789Q", original_mobile="9988776605")
        session.add_all([sr_arj_1, sr_arj_2])
        await session.flush()

        md_arj = MatchDecision(
            record_a_id=sr_arj_1.id, record_b_id=sr_arj_2.id, decision=Decision.REVIEW, final_score=0.82,
            pan_match=1.0, mobile_match=0.80, email_match=0.0, name_similarity=1.0, name_semantic_similarity=1.0, dob_match=0.0, city_similarity=0.0
        )
        session.add(md_arj)
        await session.flush()

        rev_arj = ReviewCase(
            match_decision_id=md_arj.id, priority=ReviewPriority.MEDIUM, status=ReviewStatus.PENDING,
            review_type=ReviewType.ATTRIBUTE_CONFLICT, verification_classification=VerificationClassification.AI_VERIFICATION_ELIGIBLE, verification_status=VerificationStatus.PENDING,
            details={"discrepancy": "Mobile number conflict.", "score": 0.82}
        )
        session.add(rev_arj)

        # ---------------------------------------------------------
        # CUSTOMER 6 - PRIYA IYER (PAN CONFLICT -> HUMAN REQUIRED)
        # ---------------------------------------------------------
        priya = GoldenCustomer(golden_customer_id="GOLD-000106", canonical_name="Priya Iyer", canonical_city="Chennai", total_relationship_value=16500000.00)
        session.add(priya)
        await session.flush()
        
        sr_priya_1 = SourceRecord(source_system=SourceSystem.INSURANCE, source_record_id="INS-P-01", original_name="Priya Iyer", original_pan="IYERP1234D", original_mobile="9123456780")
        sr_priya_2 = SourceRecord(source_system=SourceSystem.LOAN, source_record_id="LN-P-01", original_name="Priya A. Iyer", original_pan="IYERX1234D", original_mobile="9123456780")
        session.add_all([sr_priya_1, sr_priya_2])
        await session.flush()

        md_priya = MatchDecision(
            record_a_id=sr_priya_1.id, record_b_id=sr_priya_2.id, decision=Decision.REVIEW, final_score=0.74, 
            reasoning={"pan": "differ"},
            pan_match=0.0, mobile_match=1.0, email_match=0.0, name_similarity=0.95, name_semantic_similarity=0.95, dob_match=0.0, city_similarity=0.0
        )
        session.add(md_priya)
        await session.flush()

        rev_priya = ReviewCase(
            match_decision_id=md_priya.id, priority=ReviewPriority.HIGH, status=ReviewStatus.PENDING,
            review_type=ReviewType.ATTRIBUTE_CONFLICT, verification_classification=VerificationClassification.HUMAN_VERIFICATION_REQUIRED, verification_status=VerificationStatus.HUMAN_VERIFICATION_REQUIRED,
            details={"discrepancy": "PAN conflict.", "score": 0.74}
        )
        session.add(rev_priya)

        # ---------------------------------------------------------
        # CUSTOMER 7 - RAHUL VERMA (NO MATCH)
        # ---------------------------------------------------------
        sr_rahul_1 = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-R-02", original_name="Rahul Verma", original_pan="VERMA5678R", original_mobile="9000001234")
        sr_rahul_2 = SourceRecord(source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-R-02", original_name="Rohul Varma", original_pan="ZXCVB9876T", original_mobile="9111114321")
        session.add_all([sr_rahul_1, sr_rahul_2])
        await session.flush()

        md_rahul = MatchDecision(
            record_a_id=sr_rahul_1.id, record_b_id=sr_rahul_2.id, decision=Decision.NON_MATCH, final_score=0.31, 
            reasoning={"pan": "differ", "mobile": "differ"},
            pan_match=0.0, mobile_match=0.0, email_match=0.0, name_similarity=0.75, name_semantic_similarity=0.80, dob_match=0.0, city_similarity=0.0
        )
        session.add(md_rahul)

        # ---------------------------------------------------------
        # CUSTOMER 8 - MEERA DESHPANDE
        # ---------------------------------------------------------
        meera = GoldenCustomer(golden_customer_id="GOLD-000108", canonical_name="Meera Deshpande", canonical_city="Mumbai", total_relationship_value=32000000.00)
        session.add(meera)
        await session.flush()
        
        sr_meera_1 = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-M-01", original_name="Meera Deshpande", original_pan="DESHP4321M", original_mobile="9765432109", original_email="meera.d@example.demo")
        sr_meera_2 = SourceRecord(source_system=SourceSystem.LOAN, source_record_id="LN-M-01", original_name="Mira Deshpande", original_pan="DESHP4321M", original_mobile="9765432109", original_email="meera.d@example.demo")
        session.add_all([sr_meera_1, sr_meera_2])
        await session.flush()

        md_meera = MatchDecision(
            record_a_id=sr_meera_1.id, record_b_id=sr_meera_2.id, decision=Decision.MATCH, final_score=0.96,
            pan_match=1.0, mobile_match=1.0, email_match=1.0, name_similarity=0.96, name_semantic_similarity=0.98, dob_match=0.0, city_similarity=0.0
        )
        session.add(md_meera)

        # ---------------------------------------------------------
        # CUSTOMER 9 - KAVITA JOSHI
        # ---------------------------------------------------------
        kavita = GoldenCustomer(golden_customer_id="GOLD-000109", canonical_name="Kavita Joshi", canonical_city="Nagpur", total_relationship_value=11000000.00)
        session.add(kavita)
        await session.flush()

        sr_kavita_1 = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-K-01", original_name="Kavita Joshi", original_pan="JOSHI2468K", original_mobile="9898989898")
        sr_kavita_2 = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-K-01", original_name="Kavitha Joshi", original_pan="JOSHI2468K", original_mobile="9898989898")
        session.add_all([sr_kavita_1, sr_kavita_2])
        await session.flush()

        md_kavita = MatchDecision(
            record_a_id=sr_kavita_1.id, record_b_id=sr_kavita_2.id, decision=Decision.MATCH, final_score=0.98,
            pan_match=1.0, mobile_match=1.0, email_match=0.0, name_similarity=0.94, name_semantic_similarity=0.97, dob_match=0.0, city_similarity=0.0
        )
        session.add(md_kavita)

        # ---------------------------------------------------------
        # CUSTOMER 10 - SAMEER KHAN
        # ---------------------------------------------------------
        sameer = GoldenCustomer(golden_customer_id="GOLD-000110", canonical_name="Sameer Khan", canonical_city="Mumbai", total_relationship_value=56000000.00)
        session.add(sameer)
        await session.flush()

        sr_sameer_1 = SourceRecord(source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-S-02", original_name="Sameer Khan", original_pan="KHANS1357P", original_mobile="9876501234")
        sr_sameer_2 = SourceRecord(source_system=SourceSystem.LOAN, source_record_id="LN-S-02", original_name="Samir Khan", original_pan="KHANS1357P", original_mobile="9876501234")
        session.add_all([sr_sameer_1, sr_sameer_2])
        await session.flush()

        md_sameer = MatchDecision(
            record_a_id=sr_sameer_1.id, record_b_id=sr_sameer_2.id, decision=Decision.REVIEW, final_score=0.90,
            pan_match=1.0, mobile_match=1.0, email_match=0.0, name_similarity=0.90, name_semantic_similarity=0.94, dob_match=0.0, city_similarity=0.0
        )
        session.add(md_sameer)
        await session.flush()

        rev_sameer = ReviewCase(
            match_decision_id=md_sameer.id, priority=ReviewPriority.LOW, status=ReviewStatus.APPROVED,
            review_type=ReviewType.AI_FLAGGED, verification_classification=VerificationClassification.AI_VERIFICATION_ELIGIBLE, verification_status=VerificationStatus.VERIFIED,
            ai_call_result={"summary": "Customer confirmed: My full name is Sameer Khan.", "outcome": "VERIFIED_EXPLANATION", "language": "Marathi"},
            ai_call_confidence="93%", details={"discrepancy": "Name transliteration.", "score": 0.90}
        )
        session.add(rev_sameer)

        # AUDIT LOGS
        log1 = AuditLog(actor_username="System", actor_role="Admin", entity_type="Ingestion", action=AuditAction.DATA_INGEST, entity_id="batch_1")
        log2 = AuditLog(actor_username="System", actor_role="Admin", entity_type="Matching", action=AuditAction.MATCHING_RUN, entity_id="pipeline_1")
        log3 = AuditLog(actor_username="System", actor_role="Admin", entity_type="Matching", action=AuditAction.MERGE_APPROVE, entity_id="GOLD-000101")
        log4 = AuditLog(actor_username="System", actor_role="Admin", entity_type="Review", action=AuditAction.REVIEW_CREATED, entity_id=str(md_vik.id))
        session.add_all([log1, log2, log3, log4])

        await session.commit()
        print("Seed completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
