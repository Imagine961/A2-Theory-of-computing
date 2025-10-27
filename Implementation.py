import json, os, sys, pathlib

uniCodeTable = {
    # Digits 0–9
    "NUM": [
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
    def lookupChar(ch, table):
        code = f"U+{ord(ch):04X}"
        for key, value in table.items():
            if isinstance(value, list):
                if code in value:
                    return key
            elif value == code:
                return key
        return None
    
    def Tokentype(ch):
        tokenType = LexicalAnalyser.lookupChar(ch, uniCodeTable)

        if tokenType == "PLUS":
            return "PLUS"
        elif tokenType == "MINUS":
            return "MINUS"
        elif tokenType == "MULT":
            return "MULT"
        elif tokenType == "EQUALS": 
            return "EQUALS"
        elif tokenType == "LPAREN":
            return "LPAREN"
        elif tokenType == "RPAREN":
            return "RPAREN"
        elif tokenType == "LAMBDA":
            return "LAMBDA"
        elif tokenType == "NUM":
            return "NUMBER"
        elif tokenType == "QUESTION":
            return "QUESTION"
        elif tokenType == "DEF":
            return "DEF"
        else:
            return None
        
    def isNum(ch):
        return LexicalAnalyser.lookupChar(ch, uniCodeTable) == "NUM"
    
    def isLetter(ch): #side note this also includes underscore
        tokenType = LexicalAnalyser.lookupChar(ch, uniCodeTable)
        return tokenType == "letters_lower" or tokenType == "letters_upper" or tokenType == "underscore"
    
    def isWhitespace(ch):
        tokenType = LexicalAnalyser.lookupChar(ch, uniCodeTable)
        return tokenType == "SPACE" or tokenType == "TAB" or tokenType == "NEWLINE"
    
    def scanNumber(source, index):
        n = len(source)
        i = index
        ch = source[i]

        if ch == '0':
            i += 1
            if i < n and source[i] == '.':
                i += 1
                if not (i < n and LexicalAnalyser.isNum(source[i])):
                    raise ValueError(f"Invalid number format at index {i}")
                while i < n and LexicalAnalyser.isNum(source[i]):
                    i += 1
                return i, float(source[index:i])
            return i, 0
        elif ch in '123456789':
            i += 1
            while i < n and LexicalAnalyser.isNum(source[i]):
                i += 1
            if i < n and source[i] == '.':
                raise ValueError(f"Invalid number format at index {i}")
            return i, int(source[index:i])
        else:
            raise ValueError(f"Invalide number start at index {i}")
        
    def scanIdentifier(source, index):
        n = len(source)
        i = index
        ch = source[i]

        if not LexicalAnalyser.isLetter(ch):
            raise ValueError(f"Invalid identifier start at index {i}")
        i += 1
        while i < n:
            ch = source[i]
            if LexicalAnalyser.isLetter(ch) or LexicalAnalyser.isNum(ch):
                i += 1
            else:
                break
        return i, source[index:i]
    
    
    def analyse(input: str):
        tokens = []
        i, n = 0, len(input)

        def addToken(tokenType, value=None):
            tokens.append((tokenType, value))
        
        while i < n:
            ch = input[i]

            if LexicalAnalyser.isWhitespace(ch):
                i += 1
                continue

            tokenType = LexicalAnalyser.Tokentype(ch)

            if tokenType == "NUMBER":
                i, number = LexicalAnalyser.scanNumber(input, i)
                addToken("NUMBER", number)
                continue

            if LexicalAnalyser.isLetter(ch):
                i, identifier = LexicalAnalyser.scanIdentifier(input, i)
                addToken("IDENTIFIER", identifier)
                continue

            if tokenType in ("LPAREN", "RPAREN", "PLUS", "MINUS", "MULT", "EQUALS", "LAMBDA", "QUESTION", "DEF"):
                addToken(tokenType, ch)
                i += 1
                continue

            if tokenType == "DOT":
                raise ValueError(f"Invalid number format at index {i}")

            raise ValueError(f"Unrecognized character '{ch}' at index {i}")
        
        addToken("EOF", None)
        return tokens


# ---------- LL(1) Parser ---------- #
NT_PROGRAM = "PROGRAM" #NT = Non-Terminal
NT_EXPRESSION = "EXPRESSION"
NT_PAREN = "PAREN"
NT_ARGTAIL = "ARGTAIL"

def skip(child):
    return child[0]

def num(child):
    return child[0]

def ident(child):
    return child[0]

def op2(name):
    def wrapper(child):
        a, b = child
        return [name, a, b]
    return wrapper

def conditional(child):
    c, t, f = child
    return ["COND", c, t, f]

def lamda(child):
    ident, body = child
    return ["LAMBDA", ident, body]

def definition(child):
    ident, e1, e2 = child
    return ["DEF", ident, e1, e2]

def application(child):
    head, args = child
    return head if len(args) == 0 else ["APPLY", head] + args

def args_cond(child):
    head, tail = child
    return [head] + tail

def args_empty(child):
    return []

PT = {}

def add(nt, lookahead, rhs, builder):
    for la in lookahead:
        PT[(nt, la)] = (rhs, builder)

add(NT_PROGRAM, ["NUMBER", "IDENTIFIER", "LPAREN"], [NT_EXPRESSION], skip)

add(NT_EXPRESSION, ["NUMBER"], ["NUMBER"], num)
add(NT_EXPRESSION, ["IDENTIFIER"], ["IDENTIFIER"], ident)
add(NT_EXPRESSION, ["LPAREN"], ["LPAREN", NT_PAREN, "RPAREN"], skip)

add(NT_PAREN, ["LAMBDA"], ["LAMBDA", "IDENTIFIER", NT_EXPRESSION], lamda)
add(NT_PAREN, ["DEF"], ["DEF", "IDENTIFIER", NT_EXPRESSION, NT_EXPRESSION], definition)
add(NT_PAREN, ["PLUS"], ["PLUS", NT_EXPRESSION, NT_EXPRESSION], op2("PLUS"))
add(NT_PAREN, ["MINUS"], ["MINUS", NT_EXPRESSION, NT_EXPRESSION], op2("MINUS"))
add(NT_PAREN, ["MULT"], ["MULT", NT_EXPRESSION, NT_EXPRESSION], op2("MULT"))
add(NT_PAREN, ["EQUALS"], ["EQUALS", NT_EXPRESSION, NT_EXPRESSION], op2("EQUALS"))
add(NT_PAREN, ["QUESTION"], ["QUESTION", NT_EXPRESSION, NT_EXPRESSION, NT_EXPRESSION], conditional)

add(NT_PAREN, ["NUMBER", "IDENTIFIER", "LPAREN"], [NT_EXPRESSION, NT_ARGTAIL], application)

add(NT_ARGTAIL, ["NUMBER", "IDENTIFIER", "LPAREN"], [NT_EXPRESSION, NT_ARGTAIL], args_cond)
add(NT_ARGTAIL, ["RPAREN"], [], args_empty)

class parseError(Exception):
    pass

class LL1Parser:
    
    def parse(tokens):
        stack = [NT_PROGRAM]
        values = []
        index = 0

        def lookahead_type():
            return tokens[index][0]
        
        def lookahead_token():
            return tokens[index]
        
        def stack_reduce(builder, mark):
            stack.append(("@reduce", builder, mark))
        
        while stack:
            top = stack.pop()
            tokenType, tokenValue = lookahead_token()

            if isinstance(top, tuple) and top and top[0] == "@reduce":
                _, builder, mark = top
                children = values[mark:]
                del values[mark:]
                nodeValue = builder(children)
                values.append(nodeValue)
                continue

            if top in (NT_PROGRAM, NT_EXPRESSION, NT_PAREN, NT_ARGTAIL):
                la = lookahead_type()
                key = (top, la)
                if key not in PT:
                    expected = sorted({k[1] for k in PT.keys() if k[0] == top})
                    raise parseError(f"Unexpected token {tokenType} at index {index}. Expected one of: {expected}")
                
                rhs, builder = PT[key]
                stack_reduce(builder, len(values))
                for symbol in reversed(rhs):
                    stack.append(symbol)
                continue

            if isinstance(top, str):
                if top == tokenType:
                    if tokenType == "NUMBER" or tokenType == "IDENTIFIER":
                        values.append(tokenValue)
                    index += 1
                    continue
                raise parseError(f"Unexpected token {tokenType} at index {index}. Expected {top}")
            
            raise parseError("parser error: invalid stack symbol")
        
        if not tokens or tokens[-1][0] != "EOF":
            raise parseError("Unexpected end of input")
        if index != len(tokens) - 1:
            raise parseError(f"Unconsumed tokens")
        if len(values) != 1:
            raise parseError("Invalid value stack")
        return values[0]
    

def parseInput(source: str):
    tokens = LexicalAnalyser.analyse(source)
    return LL1Parser.parse(tokens)

TESTS = [
    # Basic expressions
    ("basic_42", "42", False),
    ("basic_x", "x", False),
    ("plus_2_3", "(+ 2 3)", False),
    ("mult_x_5", "(× x 5)", False),
    # Nested
    ("nested_plus_mult", "(+ (× 2 3) 4)", False),
    ("cond_eq", "(? (= x 0) 1 0)", False),
    # Functions / defs / application
    ("lambda_id", "(λ x x)", False),
    ("def_y", "(≜ y 10 y)", False),
    ("apply_lambda", "((λ x (+ x 1)) 5)", False),
    ("grouping", "(x)", False),
    ("application", "(x 1 2)", False),
    # Error handling
    ("err_missing_rparen", "(+ 2", True),
    ("err_unmatched_rparen", ")", True),
    ("err_wrong_arity_plus", "(+ 2 3 4)", True),
]
                

def main():
    outputDir = pathlib.Path("./parser_tests_output")
    outputDir.mkdir(exist_ok=True)
    passed = 0
    failed = 0
    results = []

    for name, source, shouldFail in TESTS:
        try:
            tree = parseInput(source)
            if shouldFail:
                results.append({
                        "input": source,
                        "tree": tree
                    })
                failed += 1
            else:
                results.append({
                    "input": source,
                    "tree": tree
                    })
                passed += 1
        except Exception as e:
            msg = str(e)
            if shouldFail:
                results.append({
                    "input": source,
                    "behave as expected": True,
                    "tree": tree
                    })
                passed += 1
            else:
                results.append({
                    "input": source,
                    "behave as expected": False,
                    "tree": tree
                    })
                failed += 1

    outputPath = outputDir / "results_output.json"
    outputPath.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Tests passed: {passed}, Tests failed: {failed}")


if __name__ == "__main__":
    main()

    for sample in ["(+ 2 3)", "(× x 5)", "(? (= x 0) 1 0)", "(λ x (+ x 1))", "((λ x (+ x 1)) 5)"]:
        try:
            print(sample, "-->", parseInput(sample))
        except Exception as e:
            print(sample, "--> Error:", str(e))


'''
final to-do list:
1. fix up output to json file, should only contain input and tree
2. add more test cases to TESTS list
3. double check all code remove any extras related to outputs that need to be removed (part of to-do 1)
'''

    

