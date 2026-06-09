#!/usr/bin/env python3
"""
Interactive engineering calculator with SI prefix and dB support.

Features:
  - Basic math: +, -, *, /, ^ or ** for power
  - Functions: log(), ln(), log(n,base), sin(), cos(), tan(), asin(), acos(),
    atan(), atan2(), sqrt(), abs(), exp(), ceil(), floor()
  - SI prefix input:  5k -> 5000, 3.3u -> 3.3e-6, etc.
  - SI prefix output: results auto-formatted with SI prefixes
  - dB input  :  20dB  -> 100  (power ratio),  20dBv -> 10  (voltage ratio)
  - dB output :  expr -> dBp   prints result in power dB
                 expr -> dBv   prints result in voltage/field dB
  - dB helpers:  dBp(x), dBv(x) convert linear value to dB inline
  - Engineer E-notation fallback for extreme magnitudes
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

# -- output formatting --------------------------------------------------------
def fmt(value: float) -> str:
    """Format a number with SI prefixes or E-notation, max 3 decimal places."""
    if value == 0:
        return "0"

    sign = "-" if value < 0 else ""
    av = abs(value)

    # Try to find a matching SI prefix (mantissa in [1, 1000))
    for thresh, prefix in SI_OUTPUT:
        if av >= thresh and thresh != 0:
            mantissa = av / thresh
            if mantissa < 1000:
                return sign + _trim(f"{mantissa:.3f}") + prefix

    # Very small -- check if any SI prefix gives a reasonable mantissa
    if av < 1e-15:
        # Fall through to E-notation
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


def fmt_db(value: float, mode: str) -> str:
    """Format a linear value as dB.  mode='dbp' (power) or 'dbv' (voltage)."""
    if value <= 0:
        raise ValueError(f"Cannot take log of non-positive value: {value}")
    if mode == "dbv":
        db_val = 20 * math.log10(value)
        label = "dBv"
    else:  # dbp (default)
        db_val = 10 * math.log10(value)
        label = "dBp"
    return f"{_trim(f'{db_val:.3f}')} {label}"


# -- input preprocessing ------------------------------------------------------

# -- dB suffix pattern  -------------------------------------------------------
# Matches: 20dB  20dBp  20dBP  20dBv  20dBV  20dBa  20dBA
# 'dB' alone or 'dBp' -> power ratio:   linear = 10^(x/10)
# 'dBv' / 'dBa'       -> voltage ratio: linear = 10^(x/20)
# Does NOT match dBm, dBW, dBu, etc. (followed by another letter) to avoid
# accidentally eating units that embed more meaning.
_DB_PAT = re.compile(
    r"""
    (?<![a-zA-Z_])           # not preceded by a letter/underscore
    (\d+\.?\d*|\.\d+)       # numeric part (e.g. 20, 3.5, .7)
    [dD][bB]                 # 'dB' case-insensitive
    ([pPvVaA]?)              # optional qualifier: p=power, v/a=voltage/amplitude
    (?![a-zA-Z_0-9(])        # not followed by alphanumeric/paren (avoids dBm, dBW…)
    """,
    re.VERBOSE,
)

def _replace_db(m: re.Match) -> str:
    """Convert a dB literal to its linear equivalent as a Python expression."""
    num = m.group(1)
    qualifier = m.group(2).lower()  # '', 'p', 'v', 'a'
    if qualifier in ("v", "a"):
        # Voltage / field / amplitude: linear = 10^(dB / 20)
        return f"(10**({num}/20))"
    else:
        # Power (default, also explicit 'p'): linear = 10^(dB / 10)
        return f"(10**({num}/10))"


# -- SI suffix pattern ---------------------------------------------------------
# Matches a number (int or float, with optional leading sign for the exponent
# part handled by float()) followed immediately by an SI suffix letter.
# We use a negative lookbehind to avoid matching things like "sin" -> "si * 1e-9".
# Suffixes are case-sensitive: m (milli) vs M (mega).
_SI_PAT = re.compile(
    r"""
    (?<![a-zA-Z_])          # not preceded by a letter (avoid matching inside func names)
    (\d+\.?\d*|\.\d+)      # the numeric part
    ([fFpPnNuUmkKMGgTt])   # SI suffix (case-insensitive capture, we normalise)
    (?![a-zA-Z_(])          # not followed by letter/paren (avoid 'log', 'min', etc.)
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
        return m.group(0)  # shouldn't happen
    factor = SI_INPUT[suffix]
    return f"({num}*{factor})"


# -- dB output trailing syntax -------------------------------------------------
# Matches: "-> dBp", "-> dBv", "-> dBa", "-> dB"  (case-insensitive, optional spaces)
_DB_OUT_PAT = re.compile(r"\s*->\s*(dBp|dBv|dBa|dB)\s*$", re.IGNORECASE)


def preprocess(expr: str) -> str:
    """Transform user expression into valid Python math expression."""
    # Replace dB-suffixed numbers FIRST (multi-char suffix, must run before SI)
    expr = _DB_PAT.sub(_replace_db, expr)

    # Replace SI-suffixed numbers:  4.7k -> (4.7*1000.0)
    expr = _SI_PAT.sub(_replace_si, expr)

    # Replace ^ with ** (power), but not inside ** already
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

        # -- dB helpers --------------------------------------------------------
        # linear -> dB  (useful for intermediate calculations / chaining with ans)
        "dBp":     lambda x: 10 * math.log10(x),   # power quantity  -> dB
        "dBv":     lambda x: 20 * math.log10(x),   # voltage / field -> dB
        "dBa":     lambda x: 20 * math.log10(x),   # amplitude alias for dBv

        # last answer
        "ans": 0.0,
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
  Functions : sin cos tan asin acos atan atan2 sqrt exp abs
              ln (natural) log (base-10) log(x,base) log2
              sinh cosh tanh asinh acosh atanh
              ceil floor factorial comb perm
              sind cosd tand (degree variants) rad deg
  Constants : pi e tau
  SI input  : 4.7k = 4700   3.3u = 0.0000033   100M = 100e6
  SI output : results auto-formatted with SI prefixes
  dB input  : 20dB  = 100  (power ratio, 10^(x/10))
              20dBp = 100  (explicit power)
              20dBv = 10   (voltage/field ratio, 10^(x/20))
  dB output : append  -> dBp  to display result as power dB
              append  -> dBv  to display result as voltage/field dB
              e.g.  100 -> dBp       ==> 20 dBp
                    10  -> dBv       ==> 20 dBv
                    4.7k * 2 -> dBp  ==> 39.731 dBp
  dB helpers: dBp(x)     linear -> power dB  (returns number, stored in ans)
              dBv(x)     linear -> voltage dB
              (use dB suffix for inline linear conversion, e.g. 20dBv)
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

        # -- dB output mode: detect trailing "-> dBp" / "-> dBv" / "-> dB" --
        db_out_mode = None  # None | 'dbp' | 'dbv'

        # Allow variable assignment:  x = 4.7k * 2
        assign_name = None
        assign_match = re.match(r"^([a-zA-Z_]\w*)\s*=\s*(.+)$", raw)
        if assign_match:
            assign_name = assign_match.group(1)
            expr_raw = assign_match.group(2)
        else:
            expr_raw = raw

        # Strip trailing -> dBp / -> dBv from the expression part
        db_out_match = _DB_OUT_PAT.search(expr_raw)
        if db_out_match:
            qualifier = db_out_match.group(1).lower()  # 'dbp', 'dbv', 'dba', 'db'
            db_out_mode = "dbv" if qualifier in ("dbv", "dba") else "dbp"
            expr_raw = expr_raw[: db_out_match.start()].rstrip()

        expr = preprocess(expr_raw)

        try:
            result = eval(expr, {"__builtins__": {}}, env)
        except Exception as exc:
            print(f"  Error: {exc}")
            continue

        if isinstance(result, (int, float)):
            env["ans"] = result
            if assign_name:
                env[assign_name] = result

            if db_out_mode:
                try:
                    db_str = fmt_db(result, db_out_mode)
                except ValueError as exc:
                    print(f"  Error: {exc}")
                    continue
                linear_str = fmt(result)
                if assign_name:
                    print(f"  {assign_name} = {db_str}  ({linear_str} linear)")
                else:
                    print(f"  = {db_str}  ({linear_str} linear)")
            else:
                if assign_name:
                    print(f"  {assign_name} = {fmt(result)}")
                else:
                    print(f"  = {fmt(result)}")
        else:
            # For non-numeric results (bool, tuple, etc.) just print normally
            if assign_name:
                env[assign_name] = result
                print(f"  {assign_name} = {result}")
            else:
                print(f"  = {result}")


if __name__ == "__main__":
    main()
