import json, os, sys, pathlib

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
            return "RPAREN"
        elif token_type == "QUESTION":
            return "QUESTION"
        elif token_type == "LAMBDA":
            return "LAMBDA"
        else:
            return None

    def _is_digit(ch):
        return LexicalAnalyser.lookup_char(ch, uniCodeTable) == "num"

     
    def _is_letter_or_underscore(ch):
        t = LexicalAnalyser.lookup_char(ch, uniCodeTable)
        return t in ("letters_lower","letters_upper","underscore")

     
    def _is_whitespace(ch):
        t = LexicalAnalyser.lookup_char(ch, uniCodeTable)
        return t in ("SPACE","TAB","NEWLINE")

     
    def _scan_number(s, i):
        """
        Accepts:
          - '0'
          - '0.' DIGITS+
          - [1-9] DIGITS*    (no fractional part; change here if you want 12.34)
        Returns (j, numeric_value)
        """
        n = len(s)
        j = i
        ch = s[j]

        if ch == '0':
            j += 1
            if j < n and s[j] == '.':
                j += 1
                if not (j < n and LexicalAnalyser._is_digit(s[j])):
                    raise ValueError(f"Invalid number at {i}: digits required after '.'")
                while j < n and LexicalAnalyser._is_digit(s[j]):
                    j += 1
                return j, float(s[i:j])
            return j, 0
        elif ch in '123456789':
            j += 1
            while j < n and LexicalAnalyser._is_digit(s[j]):
                j += 1
            if j < n and s[j] == '.':
                raise ValueError(f"Invalid number at {i}: decimals must be 0.<digits>")
            return j, int(s[i:j])
        else:
            raise ValueError(f"Invalid number start {ch!r} at {i}")

     
    def _scan_identifier(s, i):
        n = len(s)
        j = i
        if not LexicalAnalyser._is_letter_or_underscore(s[j]):
            raise ValueError(f"Invalid identifier start at {i}")
        j += 1
        while j < n:
            ch = s[j]
            if LexicalAnalyser._is_letter_or_underscore(ch) or LexicalAnalyser._is_digit(ch):
                j += 1
            else:
                break
        return j, s[i:j]
    

    # ---- main scan ----
     
    def analyse(input_str: str):
        tokens = []
        i, n = 0, len(input_str)

        def emit(tt, val=None):
            tokens.append((tt, val))

        while i < n:
            ch = input_str[i]

            if LexicalAnalyser._is_whitespace(ch):
                i += 1
                continue

            tt = LexicalAnalyser.Tokentype(ch)

            if tt == "DIGIT":
                j, numval = LexicalAnalyser._scan_number(input_str, i)
                emit("NUMBER", numval)
                i = j
                continue

            if LexicalAnalyser._is_letter_or_underscore(ch):
                j, name = LexicalAnalyser._scan_identifier(input_str, i)
                emit("IDENTIFIER", name)
                i = j
                continue

            if tt in ("LPAREN","RPAREN","PLUS","MINUS","MULT","EQUALS","QUESTION","LAMBDA","DEF"):
                emit(tt, ch)
                i += 1
                continue

            if tt == "DOT":  # disallow bare '.' — decimals must start '0.'
                raise ValueError(f"Invalid number at index {i}: decimals must start with '0.'")

            raise ValueError(f"Illegal character {ch!r} at index {i}")

        emit("EOF", None)
        return tokens
    

# ---------- Parser (table-driven LL(1)) ----------
# Nonterminals
NT_PROGRAM = "PROGRAM"
NT_EXPR    = "EXPR"
NT_PAREN   = "PAREN"
NT_ARGTAIL = "ARGTAIL"

# Small node builders → list-based trees
def _pass(children):                  # take first child (PROGRAM→EXPR, EXPR→( PAREN ), etc.)
    return children[0]

def _num(children):                   # EXPR→NUMBER
    return children[0]

def _ident(children):                 # EXPR→IDENTIFIER
    return children[0]

def _op2(name):
    def build(children):
        _, a, b = children
        return [name, a, b]
    return build

def _cond(children):                  # ? e e e
    _, c, t, f = children
    return ["COND", c, t, f]

def _lam(children):                   # λ IDENT e
    _, ident, body = children
    return ["LAMBDA", ident, body]

def _def(children):                   # ≜ IDENT e e
    _, ident, e1, e2 = children
    return ["DEF", ident, e1, e2]

def _app(children):                   # PAREN → EXPR ARGTAIL
    head, args = children
    return head if len(args) == 0 else ["APPLY", head, *args]

def _args_cons(children):             # ARGTAIL → EXPR ARGTAIL
    head, tail = children
    return [head] + tail

def _args_eps(children):              # ARGTAIL → ε
    return []

# Parse table: (NT, lookahead) -> (RHS, builder)
PT = {}

def _add(nt, lookaheads, rhs, builder):
    for la in lookaheads:
        PT[(nt, la)] = (rhs, builder)

# PROGRAM
_add(NT_PROGRAM, ["NUMBER","IDENTIFIER","LPAREN"], [NT_EXPR], _pass)

# EXPR
_add(NT_EXPR, ["NUMBER"], ["NUMBER"], _num)
_add(NT_EXPR, ["IDENTIFIER"], ["IDENTIFIER"], _ident)
_add(NT_EXPR, ["LPAREN"], ["LPAREN", NT_PAREN, "RPAREN"], _pass)

# PAREN – operator-headed
_add(NT_PAREN, ["PLUS"],     ["PLUS", NT_EXPR, NT_EXPR], _op2("PLUS"))
_add(NT_PAREN, ["MULT"],     ["MULT", NT_EXPR, NT_EXPR], _op2("MULT"))
_add(NT_PAREN, ["EQUALS"],   ["EQUALS", NT_EXPR, NT_EXPR], _op2("EQUALS"))
_add(NT_PAREN, ["MINUS"],    ["MINUS", NT_EXPR, NT_EXPR], _op2("MINUS"))
_add(NT_PAREN, ["QUESTION"], ["QUESTION", NT_EXPR, NT_EXPR, NT_EXPR], _cond)
_add(NT_PAREN, ["LAMBDA"],   ["LAMBDA", "IDENTIFIER", NT_EXPR], _lam)
_add(NT_PAREN, ["DEF"],      ["DEF", "IDENTIFIER", NT_EXPR, NT_EXPR], _def)
# PAREN – application-headed
_add(NT_PAREN, ["NUMBER","IDENTIFIER","LPAREN"], [NT_EXPR, NT_ARGTAIL], _app)

# ARGTAIL
_add(NT_ARGTAIL, ["NUMBER","IDENTIFIER","LPAREN"], [NT_EXPR, NT_ARGTAIL], _args_cons)
_add(NT_ARGTAIL, ["RPAREN"], [], _args_eps)

class ParseError(Exception): pass

class Parser:
     
    def parse(tokens):
        """
        Table-driven predictive parser.
        Input tokens are tuples (TYPE, VALUE). Produces list-based trees.
        """
        stack = [NT_PROGRAM]
        values = []
        i = 0

        def lookahead_type():
            return tokens[i][0]

        def lookahead_tok():
            return tokens[i]

        def push_reduce(builder, mark):
            stack.append(("@reduce", builder, mark))

        while stack:
            top = stack.pop()
            tt, tv = lookahead_tok()

            # reduction?
            if isinstance(top, tuple) and top and top[0] == "@reduce":
                _, builder, mark = top
                children = values[mark:]
                del values[mark:]
                node = builder(children)
                values.append(node)
                continue

            # nonterminal?
            if top in (NT_PROGRAM, NT_EXPR, NT_PAREN, NT_ARGTAIL):
                la = lookahead_type()
                key = (top, la)
                if key not in PT:
                    expected = sorted({k[1] for k in PT.keys() if k[0] == top})
                    raise ParseError(
                        f"Syntax error: while expanding {top}, got {la}; expected one of {{{', '.join(expected)}}}"
                    )
                rhs, builder = PT[key]
                push_reduce(builder, len(values))
                for sym in reversed(rhs):
                    stack.append(sym)
                continue

            # terminal?
            if isinstance(top, str):
                if top == tt:
                    if tt == "NUMBER" or tt == "IDENTIFIER":
                        values.append(tv)
                    i += 1
                    continue
                raise ParseError(f"Unexpected token {tt} at this position; expected {top}")

            raise ParseError("Internal parser error: bad stack element")

        if not tokens or tokens[-1][0] != "EOF":
            raise ParseError("Missing EOF token")
        if i != len(tokens) - 1:
            raise ParseError("Input not fully consumed")
        if len(values) != 1:
            raise ParseError("Ambiguous value stack")
        return values[0]

# ---------- Convenience entrypoint ----------
def parse_input(src: str):
    toks = LexicalAnalyser.analyse(src)
    return Parser.parse(toks)

# ---------- Test harness (writes JSON to ./out) ----------
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
    out_dir = pathlib.Path("out")
    out_dir.mkdir(exist_ok=True)
    passed = failed = 0

    for name, src, expect_error in TESTS:
        path = out_dir / f"{name}.json"
        try:
            tree = parse_input(src)
            if expect_error:
                data = {"input": src, "ok": False, "error": "EXPECTED_ERROR_BUT_PARSED", "tree": tree}
                failed += 1
            else:
                data = {"input": src, "ok": True, "tree": tree}
                passed += 1
        except Exception as e:
            msg = str(e)
            if expect_error:
                data = {"input": src, "ok": True, "error_expected": True, "message": msg}
                passed += 1
            else:
                data = {"input": src, "ok": False, "message": msg}
                failed += 1
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Tests complete. Passed: {passed}, Failed: {failed}. JSON results in ./out")



if __name__ == "__main__":
    main()
    

    for sample in ["(+ 2 3)", "(× x 5)", "(? (= x 0) 1 0)", "(λ x (+ x 1))", "((λ x (+ x 1)) 5)"]:
        try:
            print(sample, "→", parse_input(sample))
        except Exception as e:
            print(sample, "✗", e)

