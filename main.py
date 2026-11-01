"""
main.py - Command-line entry point for Conway's Game of Life (Mesa).

Two modes:
    --headless   run ``--steps`` generations and save the results to disk
    (default)    open the Tkinter UI, which saves on close

Examples:
    python main.py --initial-pattern glider --steps 200
    python main.py --headless --initial-pattern random --density 0.25 --seed 1
    python main.py --headless --initial-pattern glider_gun --torus --debug
"""
import argparse
import logging
from pathlib import Path
import random

from GameOfLife import GameOfLife, PATTERNS
from logger_config import configure_logging
from file_generator import save_results

DEFAULT_HEIGHT = 50
DEFAULT_WIDTH = 50
DEFAULT_SEED = None
DEFAULT_DENSITY = 0.3
DEFAULT_RESULTS = Path("results")
DEFAULT_STEPS = 1000
DEFAULT_PATTERN = "random"

RANDOM_SEED_RANGE = 2**32

def parse_arguments():
    parser = argparse.ArgumentParser(description="Conway's Game of Life with Mesa")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--density", type=float, default=DEFAULT_DENSITY,help="live-cell probability (only for 'random')")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--initial-pattern", default=DEFAULT_PATTERN,choices=["random", "custom", *PATTERNS],help="'custom' starts empty so you can draw in the UI")
    parser.add_argument("--all-patterns-headless",action="store_true",help="run a headless simulation for every predefined pattern",)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--torus", action="store_true",help="periodic borders (default: closed borders)")
    parser.add_argument("--debug", action="store_true",help="verbose per-generation logging")
    parser.add_argument("--log-file",type=str,default=None,metavar="PATH",help="optional path to a log file (logs to stderr as well)")
    return parser.parse_args(), parser

def create_model(args, log):
    """Create and initialize the Game of Life model."""

    seed = (
        args.seed
        if args.seed is not None
        else random.randrange(RANDOM_SEED_RANGE)
    )

    log.info("Using seed %d.", seed)

    try:
        return GameOfLife(
            width=args.width,
            height=args.height,
            pattern=args.initial_pattern,
            density=args.density,
            seed=seed,
            torus=args.torus,
        )
    except ValueError as error:
        raise error


def run_headless(args, model, LOG):
    LOG.info("Headless run: %d generations.", args.steps)
    # Boards are snapshotted every step; the alive/changed statistics
    # come straight from the model's DataCollector.
    history = [model.matrix()]
    for _ in range(args.steps):
        before = model.generation
        model.step()
        if model.generation == before:  # model halted: all cells dead
            LOG.warning("Stopping early at generation %d of %d.",model.generation, args.steps)
            break
        history.append(model.matrix())

    alive = model.datacollector.model_vars["alive"]
    changed = model.datacollector.model_vars["changed"]
    save_results(history, alive, changed, args.results)

def run_all_patterns_headless(args, LOG):
    LOG.info("Running headless simulations for all patterns.")

    for pattern in PATTERNS:
        LOG.info("Starting pattern: %s", pattern)

        pattern_args = argparse.Namespace(**vars(args))
        pattern_args.headless = True
        pattern_args.initial_pattern = pattern
        pattern_args.results = args.results / pattern

        model = create_model(pattern_args, LOG)
        run_headless(pattern_args, model, LOG)

        LOG.info("Finished pattern: %s", pattern)

def run_tkinter_ui(args, model, LOG):
    from GameOfLifeUI import GameOfLifeUI
    LOG.info("Starting the interactive UI.")
    GameOfLifeUI(model, args.steps, args.results).run()


def main():
    LOG = logging.getLogger("game_of_life.main")
    args, parser = parse_arguments()

    configure_logging(args.debug, args.log_file)

    if args.steps < 0:
        parser.error("--steps must be non-negative")

    if args.all_patterns_headless:
        run_all_patterns_headless(args, LOG)
    else:
        model = create_model(args, LOG)

        if args.headless:
            run_headless(args, model, LOG)
        else:
            run_tkinter_ui(args, model, LOG)


if __name__ == "__main__":
    main()