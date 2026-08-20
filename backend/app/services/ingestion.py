import json
import random
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.ingest import IngestRecord
from app.db.models.source_record import SourceRecord
from app.services.standardizer import StandardizerService
from app.services.embeddings import EmbeddingService

class IngestionService:
    @staticmethod
    def process_records(db: Session, records: List[IngestRecord]) -> Dict[str, Any]:
        """
        Process a list of IngestRecords: standardizes fields, generates embeddings,
        and saves them to the source_records table.
        """
        processed_count = 0
        skipped_count = 0
        
        for record in records:
            # Check if record already exists to make endpoint idempotent
            exists = db.query(SourceRecord).filter(
                SourceRecord.source_system == record.source_system,
                SourceRecord.source_id == record.source_id
            ).first()
            
            if exists:
                skipped_count += 1
                continue

            # Standardize fields
            std_pan = StandardizerService.clean_pan(record.raw_pan) if record.raw_pan else None
            std_mobile = StandardizerService.clean_mobile(record.raw_mobile) if record.raw_mobile else None
            std_email = StandardizerService.clean_email(record.raw_email) if record.raw_email else None
            std_name = StandardizerService.clean_name(record.raw_name) if record.raw_name else None
            std_city = StandardizerService.clean_city(record.city) if record.city else None
            
            # Construct embedding input string
            # Format: <name> | <city> | <segment>
            name_part = std_name or ""
            city_part = std_city or ""
            segment_part = record.segment or ""
            embedding_text = f"{name_part} | {city_part} | {segment_part}"
            
            # Generate embedding
            embedding_vector = EmbeddingService.generate_embedding(embedding_text)
            
            # Handle DOB string to Date object
            dob_date = None
            if record.dob:
                try:
                    dob_date = datetime.strptime(record.dob, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            # Create SourceRecord
            db_record = SourceRecord(
                source_system=record.source_system,
                source_id=record.source_id,
                raw_name=record.raw_name,
                raw_pan=record.raw_pan,
                raw_mobile=record.raw_mobile,
                raw_email=record.raw_email,
                pan=std_pan,
                mobile=std_mobile,
                email=std_email,
                name=std_name,
                dob=dob_date,
                city=std_city,
                segment=record.segment,
                account_value=record.account_value,
                products=record.products,
                metadata_extra=record.metadata_extra,
                vector_embedding=embedding_vector
            )
            
            db.add(db_record)
            processed_count += 1
            
            # Commit in batches of 50 for performance
            if processed_count % 50 == 0:
                db.commit()
                
        # Final commit
        db.commit()
        
        return {
            "status": "success",
            "processed": processed_count,
            "skipped": skipped_count,
            "total": len(records)
        }

    @staticmethod
    def seed_synthetic_data(db: Session) -> Dict[str, Any]:
        """
        Generates synthetic data and processes it.
        Creates ~250 mock records simulating different source systems.
        """
        source_systems = ["CORE_BANKING", "CREDIT_CARD", "WEALTH_MGMT", "LOAN_SYS", "CRM"]
        cities = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Pune", "Gurugram"]
        segments = ["RETAIL", "HNI", "CORPORATE", "SME"]
        
        first_names = ["Rahul", "Priya", "Amit", "Neha", "Vikram", "Sneha", "Karan", "Pooja", "Arjun", "Anjali"]
        last_names = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Deshmukh", "Reddy", "Iyer", "Joshi", "Verma"]
        
        records_to_ingest = []
        
        # We will create 50 base individuals, and for each, simulate records across 1-5 source systems
        # with slight variations in the raw data (typos, missing fields)
        
        base_id = 1000
        for i in range(50):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            base_name = f"{fn} {ln}"
            
            base_mobile = f"98765{random.randint(10000, 99999)}"
            base_email = f"{fn.lower()}.{ln.lower()}{random.randint(1, 99)}@example.com"
            base_pan = f"{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}P{chr(random.randint(65, 90))}{random.randint(1000, 9999)}{chr(random.randint(65, 90))}"
            base_city = random.choice(cities)
            base_segment = random.choice(segments)
            base_dob = f"{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            
            num_systems = random.randint(1, 5)
            user_systems = random.sample(source_systems, num_systems)
            
            for sys in user_systems:
                # Add some noise to simulate real-world messy data
                noise = random.random()
                
                name_variant = base_name
                if noise < 0.1:
                    name_variant = f"Mr. {base_name}"
                elif noise < 0.2:
                    name_variant = f"{fn.upper()} {ln.upper()}"
                    
                mobile_variant = base_mobile
                if noise < 0.15:
                    mobile_variant = f"+91-{base_mobile}"
                elif noise < 0.3:
                    mobile_variant = f"0{base_mobile}"
                    
                city_variant = base_city
                if base_city == "Mumbai" and noise < 0.2:
                    city_variant = "Bombay"
                elif base_city == "Bengaluru" and noise < 0.2:
                    city_variant = "Bangalore"
                    
                # Create the raw record
                record = IngestRecord(
                    source_system=sys,
                    source_id=f"{sys}-{base_id}",
                    raw_name=name_variant,
                    raw_pan=base_pan if random.random() > 0.1 else None, # 10% missing PAN
                    raw_mobile=mobile_variant if random.random() > 0.05 else None,
                    raw_email=base_email if random.random() > 0.2 else None,
                    dob=base_dob,
                    city=city_variant,
                    segment=base_segment,
                    account_value=round(random.uniform(1000, 500000), 2),
                    products={"type": sys, "active": True},
                    metadata_extra={"loyalty_points": random.randint(0, 10000)} if sys == "CREDIT_CARD" else {}
                )
                records_to_ingest.append(record)
            
            base_id += 1
            
        return IngestionService.process_records(db, records_to_ingest)
