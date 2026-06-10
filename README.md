# Engineering Calculator

A calculator designed for engineers, in your terminal.

## Features

- **SI prefix I/O** — `4.7k * 2` → `9.4k`; results auto-formatted with SI suffixes (`f p n u m k M G T`)
- **Variable assignment** — `x = 4.7k * 2`; `ans` always holds the last result
- **dB input & conversions** — `20dB`, `20dBv`; append `-> dBp` or `-> dBv` to convert
- **Bitwise operations** — `<<` `>>` `&` `|` `~` (integer, unsigned)
- **Hex & binary I/O** — `0xFF` / `x34`; `0b1101` / `b1101`; append `-> hex` or `-> bin`
- **Byte & bit units** — `KB`, `KiB`, `Kb`, `Kib`, etc.; mixed arithmetic (1 byte = 8 bits); convert with `-> MB`, `-> Kib`, etc.
- **Rich math library** — trig (radians & degrees), hyperbolic, logs, combinatorics, rounding, and more
- **Command history** — via `readline` (Unix/macOS) or `pyreadline3` (Windows)

## Setup

```bash
# Clone using Git Bash 
git clone <repo>
cd <repo>

# Set up virtual environment
python -m venv .venv

# Install dependencies
pip install -r requirements.txt

# Run the calculator!
python calc.py
```

**Optional alias** — add to `~/.bashrc` for access from anywhere:
```bash
calc_folder="${HOME}/Documents/CLI-Calculator"
alias cli-calc="${calc_folder}/.venv/Scripts/python ${calc_folder}/calc.py"
```

Avoid placing the folder in a path with spaces, as this makes it trickier to access using a terminal.

## Highlights

### SI Prefixes
```
> 3.3u * 47k             # 3.3 µF × 47 kΩ
  = 155.1m
> 1.5G / 1M
  = 1.5k
> ans * 2u
  = 3m
```

Valid SI prefixes range from femto (`f`) to Tera (`T`). Notation is case-insensitive, except for milli/Mega (`m`/`M`).


### Hex & Binary
```
> 0xFD & 0x0F -> hex
  = 0xD  (13)
> ans -> bin
  = 0b1101  (13)          # -> hex / -> bin are display-only; ans unchanged
> 0xABb                   # Hex is case-insensitive — b is a hex digit here
  = 2.747k
```

### Bitwise
```
> 5 << 3                  # 5 × 2³
  = 40
> ~0 & 0xFF
  = 255
```

### Byte & Bit Units
Stored internally as bytes (1 byte = 8 bits); bytes and bits mix freely.

```
> 5KiB                    # 5120 bytes
  = 5.12k B  (40960 bits)
> 5b + 3b
  = 1 B  (8 bits)
> 8MB -> Mb
  = 64 Mb
> 1GiB -> MB
  = 1073.742 MB
```

Decimal (KB, MB…) = powers of 1000. Binary (KiB, MiB…) = powers of 1024. See [this page](https://ss64.com/tools/convert.html) for more detail.

### dB
```
> 20dB                    # Power ratio: 10^(20/10)
  = 100
> 20dBv                   # Voltage ratio: 10^(20/20)
  = 10
> ans * 2k -> dBp
  = 43.01 dBp  (20k linear)
> dB(20dB * 10k) / 2      # Using functions to apply dB inline. (Output is printed without units)
  = 60
```

### Variables
```
> r1 = 3.3k
> r2 = 4.7k
> r1 * r2
  = 15.51M
> ans -> dBp
  = 71.907 dBp
```

## Reference

### Functions
| Category       | Functions |
|----------------|-----------|
| Powers/Roots   | `sqrt`, `exp`, `pow` |
| Logarithms     | `ln`, `log` (base-10), `log(x, base)`, `log2`, `log10` |
| Trig (radians) | `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2` |
| Trig (degrees) | `sind`, `cosd`, `tand` |
| Angle convert  | `rad`, `deg` |
| Hyperbolic     | `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh` |
| Rounding       | `ceil`, `floor`, `round`, `abs` |
| Combinatorics  | `factorial` / `!`, `comb` / `nCk`, `perm` / `nPk` |
| Type casting   | `int`, `float` |
| dB helpers     | `dBp(x)` / `dB(x)`, `dBv(x)` |
| Misc           | `min`, `max`, `sum` |

Constants: `pi`, `e`, `tau`

### Output Conversions (`->`)
| Syntax | Effect | `ans` updated? |
|--------|--------|:-:|
| `-> dBp` / `-> dBv` | Convert to dB | ✓ |
| `-> KB`, `-> MiB`, `-> Mb`, … | Convert byte/bit unit | ✓ |
| `-> hex` | Display as hex | ✗ |
| `-> bin` | Display as binary | ✗ |

Type `help` to show help, `quit` / `q` to exit.
