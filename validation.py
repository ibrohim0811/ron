import re

# Strict regex checking country code + valid operator + 7 digits
UZ_PHONE_REGEX = r"^(\+?998)?(20|33|55|77|88|90|91|93|94|95|97|98|99)\d{7}$"

def is_valid_uz_phone(phone: str) -> bool:
    # Strip common formatting characters like spaces, hyphens, and parentheses
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    return bool(re.match(UZ_PHONE_REGEX, cleaned))