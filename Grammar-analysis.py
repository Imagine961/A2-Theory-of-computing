uniCodeTable = {
    # Digits 0–9
    "num": [
        "U+0030", "U+0031", "U+0032", "U+0033", "U+0034",
        "U+0035", "U+0036", "U+0037", "U+0038", "U+0039"
    ],

    # Letters (for identifiers) — a–z, A–Z, underscore
    "letters_lower": [f"U+{ord(c):04X}" for c in "abcdefghijklmnopqrstuvwxyz"],
    "letters_upper": [f"U+{ord(c):04X}" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
    "underscore": "U+005F",

    # Parentheses
    "LPAREN": "U+0028",   # (
    "RPAREN": "U+0029",   # )

    # operators
    "PLUS": "U+002B",     # +
    "MINUS": "U+2212",    # − (Unicode minus)
    "MULT": "U+00D7",     # × (multiplication)
    "EQUALS": "U+003D",   # =

    # Conditional operator
    "QUESTION": "U+003F", # ?

    # Lambda (function abstraction)
    "LAMBDA": "U+03BB",   # λ (Greek small letter lambda)

    # Definition / binding
    "DEF": "U+225C",      # ≜ (colon equals)

    # Whitespace characters
    "SPACE": "U+0020",
    "TAB": "U+0009",
    "NEWLINE": "U+000A",

    
}


