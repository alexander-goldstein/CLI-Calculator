# Engineering Calculator

An interactive command-line calculator designed for engineers, with built-in support for SI prefix notation and decibel (dB) conversions.

## Features

- **Standard math** — arithmetic operators, power (`^` or `**`), modulo (`%`)
- **SI prefix input/output** — type `4.7k` instead of `4700`; results are automatically displayed with SI prefixes
- **dB input** — write `20dB` or `20dBv` directly in expressions
- **dB output** — append `-> dBp` or `-> dBv` to any expression to see the result in decibels
- **Rich function library** — trig, inverse trig, hyperbolic, logarithms, rounding, combinatorics, and more
- **Variable assignment** — store intermediate results (e.g., `x = 4.7k * 2`)
- **`ans` variable** — automatically holds the last computed result
- **Command history** — via `readline` (Unix/macOS) or `pyreadline3` (Windows)

## Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python calc.py
```

At the `>` prompt, type any expression and press Enter.

```
Engineering Calculator  (type 'help' for info, Ctrl+C / 'quit' to exit)

> 4.7k * 2
  = 9.4k
> 100 -> dBp
  = 20 dBp  (100 linear)
> 20dBv
  = 10
> x = 3.3u * 47k
  x = 155.1m
> ans + 1
  = 1.155
> quit
Bye!
```

## SI Prefixes

| Suffix | Multiplier |
|--------|-----------|
| `f`    | 1e-15     |
| `p`    | 1e-12     |
| `n`    | 1e-9      |
| `u`    | 1e-6      |
| `m`    | 1e-3      |
| `k`    | 1e3       |
| `M`    | 1e6       |
| `G`    | 1e9       |
| `T`    | 1e12      |

Suffixes are case-sensitive where it matters (`m` = milli, `M` = mega).

## dB Support

### Input
| Syntax  | Interpretation                          |
|---------|-----------------------------------------|
| `20dB`  | Power ratio — `10^(20/10)` = 100        |
| `20dBp` | Explicit power ratio (same as above)    |
| `20dBv` | Voltage/field ratio — `10^(20/20)` = 10 |
| `20dBa` | Amplitude alias for `dBv`               |

### Output
Append `-> dBp` or `-> dBv` to any expression:
```
> 100 -> dBp
  = 20 dBp  (100 linear)
> 10 -> dBv
  = 20 dBv  (10 linear)
> 4.7k * 2 -> dBp
  = 39.731 dBp  (9.4k linear)
```

### Helper Functions
| Function      | Description                         |
|---------------|-------------------------------------|
| `dBp(x)`      | Linear → power dB (returns number)  |
| `dBv(x)`      | Linear → voltage/field dB           |

To convert dB back to linear, use the `dB` input suffix directly in your expression (e.g. `20dBv`, `6dBp`).

## Functions Reference

| Category        | Functions                                                                 |
|-----------------|---------------------------------------------------------------------------|
| Powers/Roots    | `sqrt`, `exp`, `pow`                                                      |
| Logarithms      | `ln`, `log` (base-10), `log(x, base)`, `log2`, `log10`                   |
| Trig (radians)  | `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`                      |
| Trig (degrees)  | `sind`, `cosd`, `tand`                                                    |
| Angle convert   | `rad`, `deg`                                                              |
| Hyperbolic      | `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`                         |
| Rounding        | `ceil`, `floor`, `round`, `abs`                                           |
| Combinatorics   | `factorial`, `comb`, `perm`                                               |
| Misc            | `min`, `max`, `sum`                                                       |

## Constants

| Name         | Value          |
|--------------|----------------|
| `pi` / `PI`  | π ≈ 3.14159…   |
| `e` / `E`    | e ≈ 2.71828…   |
| `tau`        | τ = 2π         |

## Commands

| Command        | Action           |
|----------------|------------------|
| `help`         | Show help text   |
| `quit` / `exit` / `q` | Exit the calculator |
| Ctrl+C / Ctrl+D | Exit             |
