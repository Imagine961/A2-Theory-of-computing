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

class LexicalAnalyser:
    #This is how to check things from the table apparently
    

    
    def lookup_char(ch, table):
        code = f"U+{ord(ch):04X}"
        for key, value in table.items():
            if isinstance(value, list):
                if code in value:
                    return key
            elif value == code:
                return key
        return None  # not found
    

    def Tokentype(ch):

        token_type = LexicalAnalyser.lookup_char(ch,uniCodeTable)

        if token_type == "PLUS":
            return "PLUS"
        elif token_type == "MINUS":
            return "MINUS"
        elif token_type == "MULT":
            return "MULT"
        elif token_type == "EQUALS":
            return "EQUALS"
        elif token_type == "num":
            return "NUMBER"
        elif token_type == "LPAREN":
            return "LPAREN"
        elif token_type == "RPAREN":
            return "RPARENT"
        elif token_type == "QUESTION":
            return "QUESTION"
        elif token_type == "LAMDA":
            return "LAMDA"
        else:
            return None

    #implement first() and follow() logic to determine what terminal it is, and thus what may be in it

    # i.e. if first() = NUMBER it must be an expression, etc etc 

    # Define what an expression and paran-expression is???

    
            

    


    def analyse(input_str: str):
        stack = list(input_str)
        tokens = []
        singletoken = ""

        for k in range(len(stack)):
            currentchar = stack[k]
    
            # Operator logic
            if operatersymbol and not number:
                if singletoken:
                    tokens.append(Token(float(singletoken)))
                    singletoken = ""
    
                tokens.append(Token(typeOf(currentchar)))
    
            # Decimal logic
            elif currentchar == '.':
                singletoken += currentchar
    
                if 0 < k < len(stack) - 1:
                    nextchar = stack[k + 1]
                    prevchar = stack[k - 1]
                    nextnumber = nextchar in '123456789'
    
                    if not (nextchar == '0' or nextnumber):
                        raise NumberException("Invalid number after decimal point")
                    elif prevchar != '0':
                        raise NumberException("Invalid number before decimal point")
    
            # Number or other valid character logic
            else:
            singletoken += currentchar

    # Push last token
    if singletoken:
        tokens.append(Token(float(singletoken)))

    return tokens




