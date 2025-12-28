# test_argon2.py
import sys
sys.path.append('.')
from app.core.security import get_password_hash, verify_password

# Test with a VERY long password
long_password = "a" * 1000  # 1000 characters!
print(f"Testing with {len(long_password)} character password...")

try:
    hash_result = get_password_hash(long_password)
    print(f"✅ Hash successful!")
    
    # Test verification
    is_valid = verify_password(long_password, hash_result)
    print(f"✅ Verification: {is_valid}")
    
    # Test wrong password
    is_wrong = verify_password("wrongpassword", hash_result)
    print(f"✅ Wrong password rejected: {not is_wrong}")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()