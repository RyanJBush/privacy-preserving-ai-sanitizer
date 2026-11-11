"""Synthetic development fixture dev-001 and canaries (they appear in source by design)."""

CANARY_EMAIL = "ava@example.com"
CANARY_CUSTOMER = "CUST-004271"
CANARY_PHONE = "(415) 555-0132"  # inside the frozen phone scope: (AAA) BBB-CCCC, A and first B in 2-9

DEV_001 = {
    "id": "dev-001",
    "text": "Email ava@example.com; customer CUST-004271; quantity 24.",
    "entities": [
        {"entity_type": "EMAIL_ADDRESS", "start": 6, "end": 21},
        {"entity_type": "CUSTOMER_ID", "start": 32, "end": 43},
    ],
}

# All-three-entity synthetic canary text (gold offsets are located by substring, not by a detector).
CANARY_TEXT = f"Email {CANARY_EMAIL}; phone {CANARY_PHONE}; customer {CANARY_CUSTOMER}; quantity 24."
CANARY_SANITIZED = "Email [EMAIL_ADDRESS]; phone [PHONE_NUMBER]; customer [CUSTOMER_ID]; quantity 24."
CANARY_GOLD = [
    {"entity_type": t, "start": CANARY_TEXT.index(v), "end": CANARY_TEXT.index(v) + len(v)}
    for t, v in (("EMAIL_ADDRESS", CANARY_EMAIL), ("PHONE_NUMBER", CANARY_PHONE), ("CUSTOMER_ID", CANARY_CUSTOMER))
]
