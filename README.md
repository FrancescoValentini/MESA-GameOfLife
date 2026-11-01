# Conway's Game of Life (Mesa)

An agent-based implementation of Conway's Game of Life built with [Mesa](https://mesa.readthedocs.io). Every grid position holds a `Cell` agent, and all cells update together each generation. Run it with an interactive Tkinter UI or headless and save the results to disk.

## Features

- Predefined patterns: `single`, `block`, `blinker`, `glider`, plus `random` and `custom` (draw your own)
- Interactive UI with play, pause, previous/next, speed control and click-to-draw
- Headless mode that saves a bitmap, a graph and a CSV of statistics
- Closed or wrap-around (torus) borders
- Reproducible runs with a seed
- Logging to the console and optionally a file

## Requirements

- Python 3.10+
- `mesa`
- `matplotlib`
- `tkinter` (included with most Python installs; only needed for the UI)

```bash
pip install mesa matplotlib
```

## Usage

Open the interactive UI (results are saved when you close the window):

```bash
python main.py --initial-pattern glider --steps 200
```

Run headless and save the results:

```bash
python main.py --headless --initial-pattern random --density 0.25 --seed 1
```

Run every predefined pattern headless:

```bash
python main.py --all-patterns-headless --steps 100
```

### Options

| Option | Description | Default |
|---|---|---|
| `--width`, `--height` | Grid size | 50 |
| `--initial-pattern` | `random`, `custom`, or a pattern name | `random` |
| `--density` | Live-cell probability (for `random`) | 0.3 |
| `--steps` | Number of generations | 1000 |
| `--seed` | Random seed | random |
| `--torus` | Wrap-around borders | off |
| `--headless` | Run without the UI | off |
| `--all-patterns-headless` | Run all patterns headless | off |
| `--results` | Output folder | `results/` |
| `--debug` | Verbose logging | off |
| `--log-file` | Also write logs to this file | none |

Tip: use `--initial-pattern custom` to start with an empty board and draw cells in the UI.

## Output

Each run writes to the results folder:

- `bitmaps.png` – first and final generation
- `graphs.png` – alive and changed cells per generation
- `statistics.csv` – `generation, alive, changed`

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Command-line entry point |
| `GameOfLife.py` | Mesa model, `Cell` agent and patterns |
| `GameOfLifeUI.py` | Tkinter + Matplotlib interface |
| `file_generator.py` | Saves bitmaps, graphs and CSV |
| `logger_config.py` | Logging setup |

## How it works

Each generation runs in two phases so all cells change at the same time:

1. **Compute:** every cell counts its 8 neighbours and decides its next state.
2. **Advance:** every cell applies that state.

The rules:

- A live cell with fewer than 2 live neighbours dies.
- A live cell with 2 or 3 live neighbours survives.
- A live cell with more than 3 live neighbours dies.
- A dead cell with exactly 3 live neighbours becomes alive.

The simulation halts when all cells are dead. In the UI you can draw new cells to resume it.
