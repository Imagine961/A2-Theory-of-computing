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
    "CONDITIONAL": "U+003F", # ?

    # Lambda (function abstraction)
    "LAMBDA": "U+03BB",   # λ (Greek small letter lambda)

    # Definition / binding
    "LET": "U+225C",      # ≜ (colon equals)

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
        elif tokenType == "CONDITIONAL":
            return "CONDITIONAL"
        elif tokenType == "LET":
            return "LET"
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

            if tokenType in ("LPAREN", "RPAREN", "PLUS", "MINUS", "MULT", "EQUALS", "LAMBDA", "CONDITIONAL", "LET"):
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

def let(child):
    ident, e1, e2 = child
    return ["LET", ident, e1, e2]


def args_cond(child):
    head, tail = child
    return [head] + tail

def args_empty(child):
    return []

PT = {}

def add(nt, lookahead, rhs, builder):
    for la in lookahead:
        PT[(nt, la)] = (rhs, builder)

add(NT_PROGRAM, ["NUMBER","IDENTIFIER","LPAREN"], [NT_EXPRESSION], skip)

add(NT_EXPRESSION, ["NUMBER"], ["NUMBER"], num)
add(NT_EXPRESSION, ["IDENTIFIER"], ["IDENTIFIER"], ident)
add(NT_EXPRESSION, ["LPAREN"], ["LPAREN", NT_PAREN, "RPAREN"], skip)

add(NT_PAREN, ["LAMBDA"], ["LAMBDA","IDENTIFIER", NT_EXPRESSION], lamda)
add(NT_PAREN, ["LET"],    ["LET","IDENTIFIER", NT_EXPRESSION, NT_EXPRESSION], let)
add(NT_PAREN, ["PLUS"],   ["PLUS",  NT_EXPRESSION, NT_EXPRESSION], op2("PLUS"))
add(NT_PAREN, ["MINUS"],  ["MINUS", NT_EXPRESSION, NT_EXPRESSION], op2("MINUS"))
add(NT_PAREN, ["MULT"],   ["MULT",  NT_EXPRESSION, NT_EXPRESSION], op2("MULT"))
add(NT_PAREN, ["EQUALS"], ["EQUALS",NT_EXPRESSION, NT_EXPRESSION], op2("EQUALS"))
add(NT_PAREN, ["CONDITIONAL"], ["CONDITIONAL", NT_EXPRESSION, NT_EXPRESSION, NT_EXPRESSION], conditional)

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

def compactJSON(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    

TESTS = [
    # Basic expressions
    ("basic_42", "42", False),
    ("basic_x", "x", False),
    ("plus_2_3", "(+ 2 3)", False),
    ("mult_x_5", "(× x 5)", False),
    # Nested
    ("nested_plus_mult", "(+ (× 2 3) 4)", False),
    ("cond_eq", "(? (= x 0) 1 0)", False),
    # Functions / lets / application
    ("lambda_id", "(λ x x)", False),
    ("let", "(≜ y 10 y)", False),
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
            output = parseInput(source)
            if shouldFail:
                results.append({
                        "input": source,
                        "output": output
                    })
                failed += 1
            else:
                results.append({
                    "input": source,
                    "output": output
                    })
                passed += 1
        except Exception as e:
            msg = str(e)
            if shouldFail:
                results.append({
                    "input": source,
                    "behave as expected": True,
                    "output": output
                    })
                passed += 1
            else:
                results.append({
                    "input": source,
                    "behave as expected": False,
                    "output": output
                    })
                failed += 1

    outputPath = outputDir / "results_output.json"
    with outputPath.open("w", encoding="utf-8") as f:
        for name, source, shouldFail in TESTS:
            try:
                tree = parseInput(source)
                output = tree
            except Exception as e:
                output = f"ERROR: {str(e)}"

            # If the output is structured (list, number, etc.), convert to compact JSON
            if not isinstance(output, str):
                output = json.dumps(output, ensure_ascii=False, separators=(',', ':'))

            f.write(f"Input: {source}\n")
            f.write(f"Output: {output}\n\n")


    print(f"Tests passed: {passed}, Tests failed: {failed}")


if __name__ == "__main__":
    main()

    for sample in ["(+ 2 3)", "(× x 5)", "(? (= x 0) 1 0)", "(λ x (+ x 1))", "((λ x (+ x 1)) 5)"]:
        try:
            print(sample, "-->", parseInput(sample))
        except Exception as e:
            print(sample, "--> Error:", str(e))

    
'''
to-do list:
1. remove underscore from identfiers (to match spec --> [a-zA-Z][a-zA-Z0-9]*)
2. simplify number scanning to only allow integers ([0-9]+)
3. re-add application rule in NT_PAREN for (expr expr* cases)
4. reenable NT_ARGRTAIL rules to collect multiple arguments
5. fix first test loops exception so output is not used before assignment
6. convert to laTeX format along with PDF for submission
'''
