import re

class StandardizerService:
    @staticmethod
    def clean_pan(pan: str) -> str | None:
        if not pan:
            return None
        # Uppercase and strip whitespace
        cleaned = pan.strip().upper()
        # Basic validation for PAN format: 5 letters, 4 numbers, 1 letter
        if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', cleaned):
            return cleaned
        return None

    @staticmethod
    def clean_mobile(mobile: str) -> str | None:
        if not mobile:
            return None
        # Strip all non-digits
        cleaned = re.sub(r'\D', '', mobile)
        # Strip common prefixes +91 or 0
        if cleaned.startswith('91') and len(cleaned) == 12:
            cleaned = cleaned[2:]
        elif cleaned.startswith('0') and len(cleaned) == 11:
            cleaned = cleaned[1:]
        
        # Must be 10 digits
        if len(cleaned) == 10:
            return cleaned
        return None

    @staticmethod
    def clean_email(email: str) -> str | None:
        if not email:
            return None
        cleaned = email.strip().lower()
        if '@' in cleaned and '.' in cleaned:
            return cleaned
        return None

    @staticmethod
    def clean_name(name: str) -> str | None:
        if not name:
            return None
        
        # Remove common titles
        titles = [r'\bmr\.?\b', r'\bmrs\.?\b', r'\bms\.?\b', r'\bdr\.?\b', r'\bprof\.?\b']
        cleaned = name.lower()
        for title in titles:
            cleaned = re.sub(title, '', cleaned)
        
        # Remove extra whitespace and special characters
        cleaned = re.sub(r'[^a-zA-Z\s]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Title case
        if cleaned:
            return cleaned.title()
        return None

    @staticmethod
    def clean_city(city: str) -> str | None:
        if not city:
            return None
        cleaned = city.strip().title()
        
        # Normalize aliases
        aliases = {
            'Bombay': 'Mumbai',
            'Calcutta': 'Kolkata',
            'Madras': 'Chennai',
            'Bangalore': 'Bengaluru',
            'Trivandrum': 'Thiruvananthapuram',
            'Gurgaon': 'Gurugram'
        }
        
        return aliases.get(cleaned, cleaned)
