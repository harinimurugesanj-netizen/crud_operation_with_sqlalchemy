import re

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "TRUNCATE", "GRANT", "REVOKE", "CREATE", "--", ";"
]
SELECT_PATTERN = re.compile(r"^\s*SELECT", re.IGNORECASE)

def validate_sql(sql: str):
    """Returns (is_valid, message, cleaned_sql)"""
    cleaned = sql.strip().strip("`").strip()
    if cleaned.lower().startswith("sql"):
        cleaned = cleaned[3:].strip()
    cleaned = cleaned.rstrip(";").strip()

    if not SELECT_PATTERN.match(cleaned):
        return False, "Only SELECT statements are allowed.", None

    upper_sql = cleaned.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper_sql:
            return False, f"Blocked: query contains forbidden keyword '{keyword}'.", None

    if "LIMIT" not in upper_sql:
        cleaned += " LIMIT 500"

    return True, "ok", cleaned