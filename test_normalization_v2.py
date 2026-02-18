def normalize_phone(phone: str) -> str:
    """Normalize phone number to 998XXXXXXXXX format (Uzbekistan)."""
    # Remove all non-digits (removes +, spaces, dashes, etc)
    digits = ''.join(filter(str.isdigit, phone))
    
    # Check for short format (9 digits) -> Add 998
    if len(digits) == 9:
        return f"998{digits}"
        
    # Check for full format (12 digits, starts with 998)
    if len(digits) == 12 and digits.startswith("998"):
        return digits
    
    # If already starts with 998 (and length is not 12, e.g. 13?), return as is
    # This preserves existing logic for edge cases but prioritizes exact matches above
    if digits.startswith('998'):
        return digits
    
    # Add 998 prefix for local numbers if not caught by len 9
    return f"998{digits}"

test_cases = [
    "+998123456789",
    "998123456789",
    "123456789",
    "12 345 67 89",
    "(12) 345-67-89",
    # Edge cases
    "+998 (90) 123-45-67",
    "8901234567"  # Russian format attempt?
]

print("Testing normalize_phone V2...")
for phone in test_cases:
    normalized = normalize_phone(phone)
    print(f"'{phone}' -> '{normalized}'")
