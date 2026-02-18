def normalize_phone(phone: str) -> str:
    """Normalize phone number to 998XXXXXXXXX format (Uzbekistan)."""
    # Remove all non-digits (removes +, spaces, dashes, etc)
    digits = ''.join(filter(str.isdigit, phone))
    
    # If already starts with 998, return as is
    if digits.startswith('998'):
        return digits
    
    # Add 998 prefix for local numbers
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

print("Testing normalize_phone...")
for phone in test_cases:
    normalized = normalize_phone(phone)
    print(f"'{phone}' -> '{normalized}'")
