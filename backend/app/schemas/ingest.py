from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class IngestRecord(BaseModel):
    source_system: str
    source_id: str
    
    # Raw values
    raw_name: Optional[str] = None
    raw_pan: Optional[str] = None
    raw_mobile: Optional[str] = None
    raw_email: Optional[str] = None
    
    # Other metadata
    dob: Optional[str] = None
    city: Optional[str] = None
    segment: Optional[str] = None
    account_value: Optional[float] = None
    products: Optional[Dict[str, Any]] = None
    metadata_extra: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra='ignore')
