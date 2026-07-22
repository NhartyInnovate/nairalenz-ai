import re

def normalize_description(description: str) -> str:
    """
    Standardize description strings by removing common headers, NIP/POS/ATM prefixes,
    bank names, and extra spaces, returning a clean lowercase match string.
    """
    if not description:
        return ""
        
    # 1. Lowercase and strip whitespace
    val = description.lower().strip()
    
    # 2. Define word boundary regexes of bank indicators and transaction routes to strip
    strip_patterns = [
        r"\bpos\b",
        r"\batm\b",
        r"\bweb\b",
        r"\btransfer\b",
        r"\bpurchase\b",
        r"\bnip\b",
        r"\bpayment\b",
        r"\bfrom\b",
        r"\bto\b",
        r"\bgtb\b",
        r"\bzenith\b",
        r"\baccess\b",
        r"\buba\b",
        r"\bopay\b",
        r"\bpalmpay\b",
        r"\bmoniepoint\b",
        r"\bcard\b",
        r"\bref\b",
        r"\bval\b",
    ]
    
    for pat in strip_patterns:
        val = re.sub(pat, " ", val)
        
    # 3. Collapse multiple whitespace structures down to a single space
    val = re.sub(r"\s+", " ", val).strip()
    return val
