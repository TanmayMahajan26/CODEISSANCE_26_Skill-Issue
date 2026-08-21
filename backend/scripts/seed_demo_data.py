import asyncio
import os
import sys
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

# Add backend dir to pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import Base, engine, async_session_factory
from app.models.golden_customer import GoldenCustomer, GoldenCustomerStatus
from app.models.source_record import SourceRecord, SourceSystem
from app.models.match_case import MatchCase, MatchClassification, MatchStatus, RiskLevel
from app.models.verification_case import VerificationCase, VerificationMethod, VerificationStatus
from app.models.verification_result import VerificationResult
from app.models.opportunity import Opportunity, OpportunityType, OpportunityStatus
from app.models.audit_log import AuditLog, AuditAction


async def seed_data():
    print("Connecting to DB and recreating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    print("Inserting data...")
    async with async_session_factory() as session:
        # CUSTOMER 1
        rohit_golden = GoldenCustomer(
            golden_id="GOLD-000101",
            full_name="Rohit Prakash Raghavan",
            normalized_name="ROHIT PRAKASH RAGHAVAN",
            pan_masked="ABCDE1234F",
            mobile_masked="9812345670",
            email="rohit.raghavan@example.demo",
            dob=None,
            city="Mumbai",
            relationship_value=12800000.0,
            relationship_manager="RM-MUM-04",
            status=GoldenCustomerStatus.ACTIVE
        )
        session.add(rohit_golden)
        await session.flush()
        
        rohit_eq = SourceRecord(
            source_system=SourceSystem.EQUITY,
            source_record_id="EQ-ROH-01",
            full_name="Rohit P. Raghavan",
            pan="ABCDE1234F",
            mobile="9812345670",
            email="rohit.raghavan@example.demo",
            city="Mumbai",
            product_type="Equity",
            holding_value=5000000
        )
        rohit_mf = SourceRecord(
            source_system=SourceSystem.MUTUAL_FUND,
            source_record_id="MF-ROH-02",
            full_name="Rohit Prakash Raghavan",
            pan="ABCDE1234F",
            mobile="+91 98123 45670",
            email="rohit.raghavan@example.demo",
            city="Bombay",
            product_type="Mutual Fund",
            holding_value=6000000
        )
        rohit_w = SourceRecord(
            source_system=SourceSystem.WEALTH,
            source_record_id="WL-ROH-03",
            full_name="Rohit Raghavan",
            pan="ABCDE1234F",
            mobile="9812345670",
            email="rohit.raghavan@example.demo",
            city="Mumbai",
            product_type="Wealth",
            holding_value=1800000
        )
        session.add_all([rohit_eq, rohit_mf, rohit_w])
        await session.flush()
        
        rohit_match = MatchCase(
            case_id="TC-001",
            record_a_id=rohit_eq.id,
            record_b_id=rohit_mf.id,
            match_score=0.97,
            classification=MatchClassification.AUTO_MATCH,
            risk_level=RiskLevel.LOW,
            primary_discrepancy=None,
            pan_match=True,
            name_score=0.95,
            mobile_match=True,
            email_score=1.0,
            city_match=True,
            recommended_action="APPROVE",
            status=MatchStatus.APPROVED
        )
        session.add(rohit_match)
        
        rohit_opp = Opportunity(
            customer_id=rohit_golden.id,
            opportunity_type=OpportunityType.CROSS_SELL,
            opportunity_name="Wealth Management PMS",
            estimated_value=5000000.0,
            readiness_score=0.92,
            reasoning="Customer has significant Equity and Mutual Fund holdings but no PMS allocation.",
            status=OpportunityStatus.OPEN
        )
        session.add(rohit_opp)

        # CUSTOMER 2
        sunita_golden = GoldenCustomer(
            golden_id="GOLD-000102",
            full_name="Sunita Mehra",
            normalized_name="SUNITA MEHRA",
            pan_masked="BKMPM1920P",
            mobile_masked="9822012345",
            email="sunita.mehra@example.demo",
            city="Pune",
            relationship_value=45000000.0,
            relationship_manager="RM-PUN-02"
        )
        session.add(sunita_golden)
        await session.flush()
        
        sunita_w = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-SUN-01", full_name="Sunita Mehra", pan="BKMPM1920P", mobile="9822012345", email="sunita.mehra@example.demo")
        sunita_mf = SourceRecord(source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-SUN-02", full_name="Sunita Mehara", pan="BKMPM1920P", mobile="9822012345", email="sunita.mehra@example.demo")
        sunita_in = SourceRecord(source_system=SourceSystem.INSURANCE, source_record_id="IN-SUN-03", full_name="S. Mehra", pan="BKMPM1920P", mobile="+91-98220-12345", email="sunita.mehra@example.demo")
        session.add_all([sunita_w, sunita_mf, sunita_in])
        await session.flush()
        
        sunita_match = MatchCase(
            case_id="TC-002",
            record_a_id=sunita_w.id,
            record_b_id=sunita_mf.id,
            match_score=0.89,
            classification=MatchClassification.REVIEW,
            risk_level=RiskLevel.LOW,
            primary_discrepancy="Minor Name Variation",
            pan_match=True, name_score=0.85, mobile_match=True, email_score=1.0,
            status=MatchStatus.APPROVED
        )
        session.add(sunita_match)
        await session.flush()
        
        sunita_verif = VerificationCase(
            verification_id="VER-001",
            match_case_id=sunita_match.id,
            customer_id=sunita_golden.id,
            discrepancy_type="Minor name spelling variation.",
            risk_level="LOW",
            verification_method=VerificationMethod.KOVI_AI_CALL,
            ai_eligible=True,
            status=VerificationStatus.CALL_COMPLETED
        )
        session.add(sunita_verif)
        await session.flush()
        
        session.add(VerificationResult(
            verification_case_id=sunita_verif.id,
            language_detected="Hindi",
            call_summary="The customer confirmed that Sunita Mehra is her legal name. The alternate spelling found in one financial record appears to be a minor spelling variation.",
            customer_response="मेरा पूरा नाम सुनीता मेहरा है।",
            confidence=0.94,
            outcome="VERIFIED_EXPLANATION"
        ))

        # CUSTOMER 3
        vikram_golden = GoldenCustomer(
            golden_id="GOLD-000103", full_name="Vikram Aditya Singhania", city="Bengaluru", relationship_value=89000000.0, relationship_manager="RM-BLR-01"
        )
        session.add(vikram_golden)
        await session.flush()
        
        vikram_eq = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-VIK-01", full_name="Vikram Aditya Singhania", pan="AAACS1928L", mobile="9811234567", dob=date(1985, 6, 12), city="Bengaluru")
        vikram_mf = SourceRecord(source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-VIK-02", full_name="Vikram A. Singhania", pan="AAACS1928K", mobile="9811234567", dob=date(1985, 6, 12), city="Bangalore")
        session.add_all([vikram_eq, vikram_mf])
        await session.flush()
        
        vikram_match = MatchCase(
            case_id="TC-003", record_a_id=vikram_eq.id, record_b_id=vikram_mf.id, match_score=0.76, classification=MatchClassification.REVIEW, risk_level=RiskLevel.HIGH, primary_discrepancy="PAN Conflict (1 character diff)", pan_match=False, name_score=0.90, mobile_match=True, dob_match=True, city_match=True, recommended_action="HUMAN_REQUIRED", status=MatchStatus.PENDING
        )
        session.add(vikram_match)
        await session.flush()
        
        session.add(VerificationCase(
            verification_id="VER-005", match_case_id=vikram_match.id, customer_id=vikram_golden.id, discrepancy_type="PAN conflict.", risk_level="HIGH", verification_method=VerificationMethod.HUMAN_CALL, ai_eligible=False, status=VerificationStatus.HUMAN_REQUIRED
        ))

        # CUSTOMER 4
        ananya_golden = GoldenCustomer(golden_id="GOLD-000104", full_name="Ananya Shah", city="Ahmedabad", relationship_value=27500000.0)
        session.add(ananya_golden)
        await session.flush()
        ananya_in = SourceRecord(source_system=SourceSystem.INSURANCE, source_record_id="IN-ANA-01", full_name="Ananya Shah", pan="PQRSX4567M", mobile="9876543210")
        ananya_eq = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-ANA-02", full_name="Ananya S. Shah", pan="PQRSX4567M", mobile="9876543210")
        session.add_all([ananya_in, ananya_eq])
        await session.flush()
        ananya_match = MatchCase(case_id="TC-004", record_a_id=ananya_in.id, record_b_id=ananya_eq.id, match_score=0.94, classification=MatchClassification.REVIEW, pan_match=True, mobile_match=True, status=MatchStatus.APPROVED)
        session.add(ananya_match)
        await session.flush()
        session.add(VerificationCase(verification_id="VER-002", match_case_id=ananya_match.id, customer_id=ananya_golden.id, discrepancy_type="DOB format variation.", risk_level="LOW", verification_method=VerificationMethod.KOVI_AI_CALL, ai_eligible=True, status=VerificationStatus.AI_ELIGIBLE))

        # CUSTOMER 5
        arjun_golden = GoldenCustomer(golden_id="GOLD-000105", full_name="Arjun Malhotra", city="Delhi", relationship_value=9500000.0)
        session.add(arjun_golden)
        await session.flush()
        arjun_a = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-ARJ-01", full_name="Arjun Malhotra", pan="LMNOP6789Q", mobile="9988776655")
        arjun_b = SourceRecord(source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-ARJ-02", full_name="Arjun Malhotra", pan="LMNOP6789Q", mobile="9988776605")
        session.add_all([arjun_a, arjun_b])
        await session.flush()
        arjun_match = MatchCase(case_id="TC-005", record_a_id=arjun_a.id, record_b_id=arjun_b.id, match_score=0.82, classification=MatchClassification.REVIEW, risk_level=RiskLevel.MEDIUM, primary_discrepancy="Mobile conflict", pan_match=True, mobile_match=False, status=MatchStatus.PENDING)
        session.add(arjun_match)
        await session.flush()
        session.add(VerificationCase(verification_id="VER-003", match_case_id=arjun_match.id, customer_id=arjun_golden.id, discrepancy_type="Mobile number conflict.", risk_level="MEDIUM", verification_method=VerificationMethod.KOVI_AI_CALL, ai_eligible=True, status=VerificationStatus.AI_ELIGIBLE))

        # CUSTOMER 6
        priya_golden = GoldenCustomer(golden_id="GOLD-000106", full_name="Priya Iyer", city="Chennai", relationship_value=16500000.0)
        session.add(priya_golden)
        await session.flush()
        priya_a = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-PRI-01", full_name="Priya Iyer", pan="IYERP1234D", mobile="9123456780")
        priya_b = SourceRecord(source_system=SourceSystem.INSURANCE, source_record_id="IN-PRI-02", full_name="Priya A. Iyer", pan="IYERX1234D", mobile="9123456780")
        session.add_all([priya_a, priya_b])
        await session.flush()
        priya_match = MatchCase(case_id="TC-006", record_a_id=priya_a.id, record_b_id=priya_b.id, match_score=0.74, classification=MatchClassification.REVIEW, risk_level=RiskLevel.HIGH, primary_discrepancy="PAN Conflict", pan_match=False, mobile_match=True, status=MatchStatus.PENDING)
        session.add(priya_match)
        await session.flush()
        session.add(VerificationCase(verification_id="VER-006", match_case_id=priya_match.id, customer_id=priya_golden.id, discrepancy_type="PAN conflict.", risk_level="HIGH", verification_method=VerificationMethod.HUMAN_CALL, ai_eligible=False, status=VerificationStatus.HUMAN_REQUIRED))

        # CUSTOMER 7
        rahul_a = SourceRecord(source_system=SourceSystem.LOAN, source_record_id="LN-RAH-01", full_name="Rahul Verma", pan="VERMA5678R", mobile="9000001234")
        rahul_b = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-ROH-02", full_name="Rohul Varma", pan="ZXCVB9876T", mobile="9111114321")
        session.add_all([rahul_a, rahul_b])
        await session.flush()
        rahul_match = MatchCase(case_id="TC-007", record_a_id=rahul_a.id, record_b_id=rahul_b.id, match_score=0.31, classification=MatchClassification.NO_MATCH, risk_level=RiskLevel.HIGH, pan_match=False, mobile_match=False, status=MatchStatus.REJECTED)
        session.add(rahul_match)
        
        # CUSTOMER 8
        meera_golden = GoldenCustomer(golden_id="GOLD-000108", full_name="Meera Deshpande", city="Mumbai", relationship_value=32000000.0)
        session.add(meera_golden)
        await session.flush()
        meera_a = SourceRecord(source_system=SourceSystem.WEALTH, source_record_id="WL-MEE-01", full_name="Meera Deshpande", pan="DESHP4321M", mobile="9765432109")
        meera_b = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-MEE-02", full_name="Mira Deshpande", pan="DESHP4321M", mobile="9765432109")
        session.add_all([meera_a, meera_b])
        await session.flush()
        meera_match = MatchCase(case_id="TC-008", record_a_id=meera_a.id, record_b_id=meera_b.id, match_score=0.96, classification=MatchClassification.AUTO_MATCH, pan_match=True, mobile_match=True, status=MatchStatus.APPROVED)
        session.add(meera_match)
        
        # CUSTOMER 9
        kavita_golden = GoldenCustomer(golden_id="GOLD-000109", full_name="Kavita Joshi", city="Nagpur", relationship_value=11000000.0)
        session.add(kavita_golden)
        await session.flush()
        kavita_a = SourceRecord(source_system=SourceSystem.INSURANCE, source_record_id="IN-KAV-01", full_name="Kavita Joshi", pan="JOSHI2468K", mobile="9898989898")
        kavita_b = SourceRecord(source_system=SourceSystem.MUTUAL_FUND, source_record_id="MF-KAV-02", full_name="Kavitha Joshi", pan="JOSHI2468K", mobile="9898989898")
        session.add_all([kavita_a, kavita_b])
        await session.flush()
        kavita_match = MatchCase(case_id="TC-009", record_a_id=kavita_a.id, record_b_id=kavita_b.id, match_score=0.98, classification=MatchClassification.AUTO_MATCH, pan_match=True, mobile_match=True, status=MatchStatus.APPROVED)
        session.add(kavita_match)
        
        # CUSTOMER 10
        sameer_golden = GoldenCustomer(golden_id="GOLD-000110", full_name="Sameer Khan", city="Mumbai", relationship_value=56000000.0)
        session.add(sameer_golden)
        await session.flush()
        sameer_a = SourceRecord(source_system=SourceSystem.EQUITY, source_record_id="EQ-SAM-01", full_name="Sameer Khan", pan="KHANS1357P", mobile="9876501234")
        sameer_b = SourceRecord(source_system=SourceSystem.LOAN, source_record_id="LN-SAM-02", full_name="Samir Khan", pan="KHANS1357P", mobile="9876501234")
        session.add_all([sameer_a, sameer_b])
        await session.flush()
        sameer_match = MatchCase(case_id="TC-010", record_a_id=sameer_a.id, record_b_id=sameer_b.id, match_score=0.90, classification=MatchClassification.REVIEW, pan_match=True, mobile_match=True, status=MatchStatus.APPROVED)
        session.add(sameer_match)
        await session.flush()
        sameer_verif = VerificationCase(verification_id="VER-004", match_case_id=sameer_match.id, customer_id=sameer_golden.id, discrepancy_type="Name variation.", risk_level="LOW", verification_method=VerificationMethod.KOVI_AI_CALL, ai_eligible=True, status=VerificationStatus.CALL_COMPLETED)
        session.add(sameer_verif)
        await session.flush()
        session.add(VerificationResult(
            verification_case_id=sameer_verif.id,
            language_detected="Marathi",
            call_summary="The customer confirmed that the name variation Samir/Sameer refers to the same person.",
            customer_response="माझं पूर्ण नाव समीर खान आहे.",
            confidence=0.93,
            outcome="VERIFIED_EXPLANATION"
        ))

        # Add Audit Log
        session.add(AuditLog(actor_name="Admin", actor_role="ADMIN", module="Matching Pipeline", action="AUTO_MATCH", description="Rohit records auto merged."))

        await session.commit()
    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
