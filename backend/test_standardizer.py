import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.standardizer import StandardizerService

def test_standardizer():
    # Test PAN
    assert StandardizerService.clean_pan("abcde1234f") == "ABCDE1234F"
    assert StandardizerService.clean_pan("  ABCDE1234F  ") == "ABCDE1234F"
    assert StandardizerService.clean_pan("INVALIDPAN") is None
    
    # Test Mobile
    assert StandardizerService.clean_mobile("+91-9876543210") == "9876543210"
    assert StandardizerService.clean_mobile("09876543210") == "9876543210"
    assert StandardizerService.clean_mobile("987 654 3210") == "9876543210"
    assert StandardizerService.clean_mobile("123") is None
    
    # Test Email
    assert StandardizerService.clean_email(" Test@EXAMPLE.com ") == "test@example.com"
    assert StandardizerService.clean_email("invalid-email") is None
    
    # Test Name
    assert StandardizerService.clean_name("Mr. John Doe") == "John Doe"
    assert StandardizerService.clean_name(" Dr.  Jane   Smith  ") == "Jane Smith"
    assert StandardizerService.clean_name("Prof. Alan Turing") == "Alan Turing"
    
    # Test City
    assert StandardizerService.clean_city("bombay") == "Mumbai"
    assert StandardizerService.clean_city("Calcutta ") == "Kolkata"
    assert StandardizerService.clean_city("pune") == "Pune"

if __name__ == "__main__":
    test_standardizer()
    print("StandardizerService tests passed!")
