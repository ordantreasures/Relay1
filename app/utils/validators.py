import re
from typing import Tuple, Optional


def validate_email_domain(email: str, allowed_domains: Optional[list] = None) -> Tuple[bool, str]:
    """Validate email domain."""
    if allowed_domains is None:
        allowed_domains = ["stu.cu.edu.ng"]
    
    if not email or "@" not in email:
        return False, "Invalid email format"
    
    domain = email.split("@")[1]
    
    for allowed_domain in allowed_domains:
        if domain.endswith(allowed_domain):
            return True, ""
    
    return False, f"Email must be from {', '.join(allowed_domains)}"


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Add more strength checks if needed
    return True, ""


def validate_post_content(content: str, min_length: int = 10, max_length: int = 5000) -> Tuple[bool, str]:
    """Validate post content length."""
    if len(content) < min_length:
        return False, f"Content must be at least {min_length} characters"
    
    if len(content) > max_length:
        return False, f"Content must be at most {max_length} characters"
    
    return True, ""


def validate_price_format(price: str) -> Tuple[bool, str]:
    """Validate price format (e.g., ₦5,000)."""
    if not price:
        return True, ""
    
    # Basic validation - can be enhanced
    price_patterns = [
        r'^₦\d+(,\d{3})*(\.\d{2})?$',  # ₦5,000 or ₦5,000.00
        r'^\$\d+(,\d{3})*(\.\d{2})?$',  # $5,000 or $5,000.00
        r'^\d+(,\d{3})*(\.\d{2})?\s*(NGN|USD)$',  # 5,000 NGN
    ]
    
    for pattern in price_patterns:
        if re.match(pattern, price.strip()):
            return True, ""
    
    return False, "Invalid price format. Use format like: ₦5,000 or $5,000"