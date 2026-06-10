#!/usr/bin/env python3
"""
Interactive engineering calculator with SI prefix, dB, byte/bit, and bitwise support.

Features:
  - Basic math: +, -, *, /, ^ or ** for power, % (modulo)
  - Bitwise ops: << >> & | ~ (Python integer arithmetic, unsigned)
  - Factorial: 5! = 120,  (2+3)! = 120
  - Functions: log(), ln(), log(n,base), sin(), cos(), tan(), asin(), acos(),
    atan(), atan2(), sqrt(), abs(), exp(), ceil(), floor(), factorial()
  - SI prefix input:  5k -> 5000, 3.3u -> 3.3e-6, etc.
  - SI prefix output: results auto-formatted with SI prefixes
  - Byte input:  5B  5KB  5MB  5GB  5TB   (decimal, powers of 1000)
                 5KiB 5MiB 5GiB 5TiB      (binary, powers of 1024)
  - Bit input:   5b  5Kb  5Mb  5Gb  5Tb   (decimal, powers of 1000)
                 5Kib 5Mib 5Gib 5Tib      (binary, powers of 1024)
  - Hex input:   x34 or 0x34
  - Binary input: b1101 or 0b1101
  - dB input:  20dB -> 100 (power), 20dBv -> 10 (voltage)
  - Output conversion (destructive, updates ans):
      expr -> dBp / dBv          dB conversion
      expr -> KB / KiB / Mb …   byte/bit unit conversion
  - History via readline (pyreadline3 on Windows)
  - 'ans' variable holds the last result
"""

import math
import re
import sys

# -- readline setup (pyreadline3 fallback on Windows) -------------------------
try:
    import readline  # Unix / macOS
except ImportError:
    try:
        import pyreadline3 as readline  # Windows fallback
    except ImportError:
        readline = None  # no history support -- still works

# -- SI prefix tables ---------------------------------------------------------
SI_INPUT = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "M": 1e6,
    "G": 1e9,
    "T": 1e12,
}

# Ordered from largest to smallest for output formatting
SI_OUTPUT = [
    (1e12,  "T"),
    (1e9,   "G"),
    (1e6,   "M"),
    (1e3,   "k"),
    (1e0,   ""),
    (1e-3,  "m"),
    (1e-6,  "u"),
    (1e-9,  "n"),
    (1e-12, "p"),
    (1e-15, "f"),
]

# -- Byte/bit unit tables -----------------------------------------------------
# Every value is "bytes per 1 of this unit".  All inputs are normalised to
# bytes internally so that mixed byte/bit arithmetic works (1 byte = 8 bits).
# The same table is used as divisors for -> output conversions.
BYTE_BIT_UNITS = {
    # Bytes -- decimal (powers of 1000)
    "B":   1,
    "KB":  1000,
    "kB":  1000,
    "MB":  1000**2,
    "GB":  1000**3,
    "TB":  1000**4,
    # Bytes -- binary (powers of 1024)
    "KiB": 1024,
    "MiB": 1024**2,
    "GiB": 1024**3,
    "TiB": 1024**4,
    # Bits -- decimal (powers of 1000) -- stored as bytes (÷ 8)
    "b":   0.125,                   # 1 bit  = 1/8 byte
    "Kb":  125,                     # 1000   / 8
    "kb":  125,
    "Mb":  125000,                  # 1000^2 / 8
    "Gb":  125000000,              # 1000^3 / 8
    "Tb":  125000000000,           # 1000^4 / 8
    # Bits -- binary (powers of 1024) -- stored as bytes (÷ 8)
    "Kib": 128,                     # 1024   / 8
    "Mib": 131072,                  # 1024^2 / 8
    "Gib": 134217728,              # 1024^3 / 8
    "Tib": 137438953472,           # 1024^4 / 8
}

# -- output formatting --------------------------------------------------------
def fmt(value) -> str:
    """Format a number with SI prefixes or E-notation, max 3 decimal places."""
    fval = float(value)
    if fval == 0:
        return "0"

    sign = "-" if fval < 0 else ""
    av = abs(fval)

    # Try to find a matching SI prefix (mantissa in [1, 1000))
    for thresh, prefix in SI_OUTPUT:
        if av >= thresh and thresh != 0:
            mantissa = av / thresh
            if mantissa < 1000:
                return sign + _trim(f"{mantissa:.3f}") + prefix

    # Very small -- fall through to E-notation
    if av < 1e-15:
        return sign + _sci(av)

    # Fallback: plain number if between 1 and 999.999…
    if 1 <= av < 1000:
        return sign + _trim(f"{av:.3f}")

    # Everything else: scientific E-notation
    return sign + _sci(av)


def _trim(s: str) -> str:
    """Remove trailing zeros after decimal point (but keep at least '5' not '5.')."""
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _sci(av: float) -> str:
    """Format as compact scientific notation like 1.23E15 or 4.56E-21."""
    exp = int(math.floor(math.log10(av)))
    mantissa = av / 10 ** exp
    return _trim(f"{mantissa:.3f}") + f"E{exp}"


def fmt_db(value: float, mode: str, label: str | None = None) -> tuple[float, str]:
    """Convert a linear value to dB.  Returns (db_value, display_string)."""
    if value <= 0:
        raise ValueError(f"Cannot take log of non-positive value: {value}")
    if mode == "dbv":
        db_val = 20 * math.log10(value)
        if label is None:
            label = "dBv"
    else:  # dbp (default)
        db_val = 10 * math.log10(value)
        if label is None:
            label = "dBp"
    return db_val, f"{_trim(f'{db_val:.3f}')} {label}"


def fmt_unit(value, unit: str) -> tuple[float, str]:
    """Divide value (in bytes) by a unit multiplier.  Returns (converted, display_string)."""
    divisor = BYTE_BIT_UNITS[unit]
    converted = value / divisor
    return converted, f"{_trim(f'{converted:.3f}')} {unit}"


def fmt_bytes(value_bytes) -> str:
    """Auto-format a byte value for display.

    - < 1 byte   : show in bits      (e.g. "5 bits")
    - >= 1 byte  : show bytes + bits  (e.g. "4.875 B  (39 bits)")
                   or  "4 B  (32 bits)" for whole values
    """
    fval = float(value_bytes)
    if fval == 0:
        return "0 B"

    sign = "-" if fval < 0 else ""
    av = abs(fval)

    # Less than 1 byte: display in bits only
    if av < 1:
        bits = av * 8
        return f"{sign}{_trim(f'{bits:.3f}')} bits"

    # >= 1 byte: always show  X B  (Y bits)
    bits = av * 8
    byte_s = fmt(value_bytes)          # SI-prefixed number for the byte part
    bit_s  = f"{sign}{_trim(f'{bits:.3f}')}"
    return f"{byte_s} B  ({bit_s} bits)"


# -- input preprocessing ------------------------------------------------------

# -- Hex prefix: bare x34 -> 0x34 ---------------------------------------------
_HEX_PREFIX_PAT = re.compile(
    r"(?<![a-zA-Z_0-9])x([0-9a-fA-F]+)(?![a-zA-Z_0-9])"
)

# -- Binary prefix: bare b1101 -> 0b1101 --------------------------------------
# Lookbehind excludes ALL alphanumerics and underscore so that:
#   b1101   -> 0b1101  (bare prefix, converted)
#   0b1101  -> 0b1101  (already valid Python, NOT re-matched because '0' is a digit)
#   5b      -> left alone (5 is a digit -- will be handled as 5 bits by byte/bit regex)
_BIN_PREFIX_PAT = re.compile(
    r"(?<![a-zA-Z_0-9])b([01]+)(?![0-9a-zA-Z_])"
)

# -- dB suffix pattern  -------------------------------------------------------
_DB_PAT = re.compile(
    r"""
    (?<![a-zA-Z_])           # not preceded by a letter/underscore
    (\d+\.?\d*|\.\d+)       # numeric part (e.g. 20, 3.5, .7)
    [dD][bB]                 # 'dB' case-insensitive
    ([pPvVaA]?)              # optional qualifier: p=power, v/a=voltage/amplitude
    (?![a-zA-Z_0-9(])        # not followed by alphanumeric/paren
    """,
    re.VERBOSE,
)

def _replace_db(m: re.Match) -> str:
    """Convert a dB literal to its linear equivalent as a Python expression."""
    num = m.group(1)
    qualifier = m.group(2).lower()
    if qualifier in ("v", "a"):
        return f"(10**({num}/20))"
    else:
        return f"(10**({num}/10))"


# -- Byte/bit suffix pattern ---------------------------------------------------
# Longest suffixes listed first so regex alternation matches them before shorter ones.
# Lookbehind prevents matching inside identifiers.
# Lookahead prevents matching when suffix is followed by more word characters
# (e.g. '0b1101' -- the '0' would match the number, 'b' the suffix, but '1' follows).
_BYTE_BIT_PAT = re.compile(
    r"""
    (?<![a-zA-Z_])           # not preceded by letter/underscore
    (\d+\.?\d*|\.\d+)       # numeric part
    (TiB|GiB|MiB|KiB        # 3-char byte binary
    |Tib|Gib|Mib|Kib        # 3-char bit  binary
    |TB|GB|MB|KB|kB         # 2-char byte decimal
    |Tb|Gb|Mb|Kb|kb         # 2-char bit  decimal
    |B|b)                   # 1-char base
    (?![a-zA-Z_0-9(])        # not followed by word char / paren
    """,
    re.VERBOSE,
)

def _replace_byte_bit(m: re.Match) -> str:
    """Convert a byte/bit-suffixed number to a plain multiplication."""
    num = m.group(1)
    unit = m.group(2)
    factor = BYTE_BIT_UNITS.get(unit)
    if factor is None:
        return m.group(0)  # shouldn't happen
    return f"({num}*{factor})"


# -- SI suffix pattern ---------------------------------------------------------
_SI_PAT = re.compile(
    r"""
    (?<![a-zA-Z_])          # not preceded by a letter
    (\d+\.?\d*|\.\d+)      # the numeric part
    ([fFpPnNuUmkKMGgTt])   # SI suffix
    (?![a-zA-Z_(])          # not followed by letter/paren
    """,
    re.VERBOSE,
)

_SUFFIX_MAP = {
    "f": "f", "F": "f",
    "p": "p", "P": "p",
    "n": "n", "N": "n",
    "u": "u", "U": "u",
    "m": "m",            # lowercase only -- 'M' is mega
    "k": "k", "K": "k",
    "M": "M",
    "g": "G", "G": "G",
    "t": "T", "T": "T",
}


def _replace_si(m: re.Match) -> str:
    num = m.group(1)
    raw_suffix = m.group(2)
    suffix = _SUFFIX_MAP.get(raw_suffix)
    if suffix is None:
        return m.group(0)
    factor = SI_INPUT[suffix]
    return f"({num}*{factor})"


# -- Factorial: postfix ! -> factorial() ---------------------------------------
def _apply_factorial(expr: str) -> str:
    """Convert postfix ! to factorial() calls.
    5!       -> factorial(5)
    (2+3)!   -> factorial((2+3))
    ans!     -> factorial(ans)
    sin(5)!  -> factorial(sin(5))
    Does NOT touch != (not-equal).
    """
    i = 0
    while i < len(expr):
        if expr[i] == '!' and (i + 1 >= len(expr) or expr[i + 1] != '='):
            if i == 0:
                i += 1
                continue

            prev = expr[i - 1]

            if prev == ')':
                # Walk back to the matching '('
                depth = 1
                j = i - 2
                while j >= 0 and depth > 0:
                    if expr[j] == ')':
                        depth += 1
                    elif expr[j] == '(':
                        depth -= 1
                    j -= 1
                j += 1  # j now points to the '('
                # Also grab a preceding function name, e.g. sin(...)!
                k = j
                while k > 0 and (expr[k - 1].isalnum() or expr[k - 1] == '_'):
                    k -= 1
                operand = expr[k:i]
                repl = f"factorial({operand})"
                expr = expr[:k] + repl + expr[i + 1:]
                i = k + len(repl)

            elif prev.isdigit() or prev == '.':
                j = i - 1
                while j > 0 and (expr[j - 1].isdigit() or expr[j - 1] == '.'):
                    j -= 1
                operand = expr[j:i]
                repl = f"factorial({operand})"
                expr = expr[:j] + repl + expr[i + 1:]
                i = j + len(repl)

            elif prev.isalpha() or prev == '_':
                j = i - 1
                while j > 0 and (expr[j - 1].isalnum() or expr[j - 1] == '_'):
                    j -= 1
                operand = expr[j:i]
                repl = f"factorial({operand})"
                expr = expr[:j] + repl + expr[i + 1:]
                i = j + len(repl)
            else:
                i += 1
        else:
            i += 1
    return expr


# -- Detect byte/bit units in expression --------------------------------------
def _has_data_units(expr: str) -> bool:
    """Return True if expression contains byte/bit unit suffixes."""
    return bool(_BYTE_BIT_PAT.search(expr))


# -- Output conversion: "-> target" at end of expression ----------------------
# Generic pattern that captures any non-whitespace token after ->
_OUT_CONV_PAT = re.compile(r"\s*->\s*(\S+)\s*$")


def fmt_base(value, base: str) -> str:
    """Format an integer value in hex or binary.  Non-destructive display."""
    iv = int(value) if isinstance(value, float) and value == int(value) else value
    if not isinstance(iv, int):
        iv = int(round(value))
    if base == "hex":
        return f"0x{iv:X}" if iv >= 0 else f"-0x{abs(iv):X}"
    else:  # bin
        return f"0b{iv:b}" if iv >= 0 else f"-0b{abs(iv):b}"


def _parse_conv_target(target: str):
    """Parse a -> conversion target.

    Returns:
        ('db',   mode)      -- mode is 'dbp' or 'dbv'
        ('unit', unit_key)  -- unit_key is a key in BYTE_BIT_UNITS
        ('fmt',  base)      -- base is 'hex' or 'bin' (non-destructive)
        None                -- unrecognised target
    """
    # dB targets (case-insensitive)
    low = target.lower()
    if low == "db":
        return ("db", "dbp", "dB")
    if low == "dbp":
        return ("db", "dbp", "dBp")
    if low in ("dbv", "dba"):
        return ("db", "dbv", "dBv")

    # Format-only targets (non-destructive)
    if low == "hex":
        return ("fmt", "hex")
    if low == "bin":
        return ("fmt", "bin")

    # Exact match in byte/bit table
    if target in BYTE_BIT_UNITS:
        return ("unit", target)

    # Normalise lowercase 'k' prefix -> 'K' (common casual typing)
    if len(target) >= 2 and target[0] == 'k':
        normalized = 'K' + target[1:]
        if normalized in BYTE_BIT_UNITS:
            return ("unit", normalized)

    return None


# -- preprocessor --------------------------------------------------------------
def preprocess(expr: str) -> str:
    """Transform user expression into valid Python math expression."""
    # 1. Hex prefix:  x34 -> 0x34
    expr = _HEX_PREFIX_PAT.sub(r"0x\1", expr)

    # 2. Binary prefix:  b1101 -> 0b1101
    expr = _BIN_PREFIX_PAT.sub(r"0b\1", expr)

    # 3. dB-suffixed numbers:  20dB -> (10**(20/10))
    expr = _DB_PAT.sub(_replace_db, expr)

    # 4. Byte/bit-suffixed numbers:  5KB -> (5*1000)
    expr = _BYTE_BIT_PAT.sub(_replace_byte_bit, expr)

    # 5. SI-suffixed numbers:  4.7k -> (4.7*1000.0)
    expr = _SI_PAT.sub(_replace_si, expr)

    # 6. Factorial:  5! -> factorial(5)
    expr = _apply_factorial(expr)

    # 7. Caret -> power
    expr = expr.replace("^", "**")

    return expr


# -- math environment ----------------------------------------------------------
def _build_env():
    """Build the dict of names available inside expressions."""
    env = {
        # constants
        "pi": math.pi,
        "PI": math.pi,
        "e": math.e,
        "E": math.e,
        "tau": math.tau,
        "nan": math.nan,

        # basic
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "int": int,
        "float": float,

        # powers / roots
        "sqrt": math.sqrt,
        "exp": math.exp,
        "pow": pow,

        # logarithms
        "ln":  math.log,           # ln(x) = natural log
        "log": _log,               # log(x)=log10, log(x,b)=logb
        "log2": math.log2,
        "log10": math.log10,

        # trig (radians)
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        "arcsin": math.asin,
        "arccos": math.acos,
        "arctan": math.atan,

        # trig (degrees convenience)
        "sind": lambda x: math.sin(math.radians(x)),
        "cosd": lambda x: math.cos(math.radians(x)),
        "tand": lambda x: math.tan(math.radians(x)),
        "rad": math.radians,
        "deg": math.degrees,

        # hyperbolic
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "asinh": math.asinh,
        "acosh": math.acosh,
        "atanh": math.atanh,

        # rounding
        "ceil": math.ceil,
        "floor": math.floor,

        # combinatorics
        "factorial": math.factorial,
        "comb": math.comb,
        "perm": math.perm,
        "nCk": math.comb,          # nCk(n, k) = comb(n, k)
        "nPk": math.perm,          # nPk(n, k) = perm(n, k)

        # -- dB helpers --------------------------------------------------------
        "dB":      lambda x: 10 * math.log10(x),
        "dBp":     lambda x: 10 * math.log10(x),
        "dBv":     lambda x: 20 * math.log10(x),
        "dBa":     lambda x: 20 * math.log10(x),
        "db":      lambda x: 10 * math.log10(x),
        "dbp":     lambda x: 10 * math.log10(x),
        "dbv":     lambda x: 20 * math.log10(x),
        "dba":     lambda x: 20 * math.log10(x),

        # last answer
        "ans": 0,
    }
    return env


def _log(x, base=10):
    """log(x) -> log10, log(x, base) -> log_base(x)."""
    if base == 10:
        return math.log10(x)
    return math.log(x, base)


# -- REPL ----------------------------------------------------------------------
HELP = """\
Engineering Calculator -- type an expression, press Enter.
  Operators : + - * / ^ (power) ** (power) % (modulo)
  Bitwise   : << (left shift)  >> (right shift)  & (AND)  | (OR)  ~ (NOT)
  Factorial : 5! = 120    (2+3)! = 120    ans!
  Functions : sin cos tan asin acos atan atan2 sqrt exp abs
              ln (natural) log (base-10) log(x,base) log2
              sinh cosh tanh asinh acosh atanh
              ceil floor factorial comb(n,k) perm(n,k)
              nCk(n,k) nPk(n,k)  (aliases for comb / perm)
              sind cosd tand (degree variants) rad deg
              int() float() (type casting for bitwise ops)
  Constants : pi e tau
  Hex input : x34 or 0x34  (= 52 decimal)
  Bin input : b1101 or 0b1101  (= 13 decimal)
  SI input  : 4.7k = 4700   3.3u = 0.0000033   100M = 100e6
  SI output : results auto-formatted with SI prefixes
  Byte input: 5B  5KB  5MB  5GB  5TB   (decimal, powers of 1000)
              5KiB  5MiB  5GiB  5TiB   (binary, powers of 1024)
  Bit input : 5b  5Kb  5Mb  5Gb  5Tb   (decimal, powers of 1000)
              5Kib  5Mib  5Gib  5Tib   (binary, powers of 1024)
  Note      : 1 Byte = 8 bits.  B = Bytes (uppercase), b = bits (lowercase).
              Bytes and bits share a common base (bytes) internally,
              so  23b + 2B  =  4.875 B (39 bits)
              and  72B -> b  =  576 b
  dB input  : 20dB  = 100  (power ratio, 10^(x/10))
              20dBp = 100  (explicit power)
              20dBv = 10   (voltage/field ratio, 10^(x/20))
  Conversion: append  -> target  to convert (destructive -- updates ans)
              -> dBp / -> dBv           dB conversion
              -> KB  -> KiB  -> Mb …    byte/bit unit conversion
              -> hex / -> bin            display as hex/binary (non-destructive)
              e.g.  100 -> dBp          ==> 20 dBp     (ans = 20)
                    1024 -> KiB         ==> 1 KiB      (ans = 1)
                    5GB -> MB           ==> 5000 MB    (ans = 5000)
                    255 -> hex          ==> 0xFF       (ans = 255)
                    13 -> bin           ==> 0b1101     (ans = 13)
  dB helpers: dB(x)      linear -> power dB  (= dBp, returns number)
              dBp(x)     linear -> power dB  (returns number)
              dBv(x)     linear -> voltage dB
  Variables : ans = last result;  you can assign: x = 3.3k
  Commands  : help  quit/exit/q
"""


def main():
    env = _build_env()
    print("Engineering Calculator  (type 'help' for info, Ctrl+C / 'quit' to exit)")
    print()

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not raw:
            continue
        if raw.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        if raw.lower() == "help":
            print(HELP)
            continue

        # -- Variable assignment:  x = 4.7k * 2 --
        assign_name = None
        assign_match = re.match(r"^([a-zA-Z_]\w*)\s*=\s*(.+)$", raw)
        if assign_match:
            assign_name = assign_match.group(1)
            expr_raw = assign_match.group(2)
        else:
            expr_raw = raw

        # -- Output conversion: detect trailing "-> target" --
        conv_target = None  # None | ('db', mode) | ('unit', key)
        conv_match = _OUT_CONV_PAT.search(expr_raw)
        if conv_match:
            parsed = _parse_conv_target(conv_match.group(1))
            if parsed:
                conv_target = parsed
                expr_raw = expr_raw[: conv_match.start()].rstrip()

        expr = preprocess(expr_raw)

        try:
            result = eval(expr, {"__builtins__": {}}, env)
        except Exception as exc:
            print(f"  Error: {exc}")
            continue

        if isinstance(result, (int, float)):
            # ---- apply conversion (destructive) ----
            if conv_target:
                conv_type, conv_key = conv_target[0], conv_target[1]
                conv_label = conv_target[2] if len(conv_target) > 2 else None
                if conv_type == "db":
                    try:
                        conv_val, conv_str = fmt_db(result, conv_key, conv_label)
                    except ValueError as exc:
                        print(f"  Error: {exc}")
                        continue
                    linear_str = fmt(result)
                    # Store the dB number as ans (destructive)
                    env["ans"] = conv_val
                    if assign_name:
                        env[assign_name] = conv_val
                    label = f"{assign_name} = " if assign_name else "= "
                    print(f"  {label}{conv_str}  ({linear_str} linear)")
                elif conv_type == "fmt":
                    # Non-destructive: just display in hex/bin, keep ans unchanged
                    env["ans"] = result
                    if assign_name:
                        env[assign_name] = result
                    label = f"{assign_name} = " if assign_name else "= "
                    print(f"  {label}{fmt_base(result, conv_key)}  ({fmt(result)})")
                else:  # 'unit'
                    conv_val, conv_str = fmt_unit(result, conv_key)
                    # Store the converted number as ans (destructive)
                    env["ans"] = conv_val
                    if assign_name:
                        env[assign_name] = conv_val
                    label = f"{assign_name} = " if assign_name else "= "
                    print(f"  {label}{conv_str}")
            else:
                # ---- normal output ----
                env["ans"] = result
                if assign_name:
                    env[assign_name] = result
                label = f"{assign_name} = " if assign_name else "= "
                # Use byte-aware formatting when expression has byte/bit units
                if _has_data_units(expr_raw):
                    print(f"  {label}{fmt_bytes(result)}")
                else:
                    print(f"  {label}{fmt(result)}")
        else:
            # Non-numeric results (bool, tuple, etc.)
            if assign_name:
                env[assign_name] = result
                print(f"  {assign_name} = {result}")
            else:
                print(f"  = {result}")


if __name__ == "__main__":
    main()
