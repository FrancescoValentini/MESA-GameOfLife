""" 
GameOfLife.py - Agent-based implementation of Conway's Game of Life using the
Mesa framework.

Note: Mesa adds complexity and overhead compared to a traditional grid-based implementation. The goal is not performance, but to demonstrate how to build an agent-based simulation using Mesa. 
"""
import logging

import mesa
from mesa.datacollection import DataCollector
from mesa.space import SingleGrid


LOG = logging.getLogger("game_of_life")


def configure_logging(debug=False):
    """Attach one console handler to the project logger (idempotent)."""
    LOG.setLevel(logging.DEBUG if debug else logging.INFO)
    LOG.propagate = False
    if not LOG.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"))
        LOG.addHandler(handler)
    LOG.debug("Logging configured (debug=%s).", debug)



# Each pattern is a list of (x, y) live cells with the top-left corner of its
# bounding box at (0, 0).  The model centres the bounding box on the grid.
PATTERNS = {
    'single': [(0, 0)],
    'block': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'blinker': [(0, 0), (1, 0), (2, 0)],
    'glider': [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)],
}


def pattern_size(name):
    """(width, height) of the bounding box of a named pattern."""
    points = PATTERNS[name]
    return max(x for x, y in points) + 1, max(y for x, y in points) + 1


# ----- BEGIN CELL AGENT DEFINITION -----
class Cell(mesa.Agent):
    """A fixed agent per cell, even when the cell is dead."""

    def __init__(self, model, alive=False):
        super().__init__(model)  # Mesa registers the agent and assigns an ID.
        self.alive = alive
        self.next_alive = alive

    @staticmethod
    def apply_rules(alive: bool, neighbors: int) -> bool:
        """
        Apply the four rules of Conway's Game of Life.

        Parameters:
            alive (bool): Whether the cell is currently alive.
            neighbors (int): Number of live neighboring cells.

        Returns:
            bool: The cell's state in the next generation.
        """

        # Rule 1: Live cell with fewer than two neighbours dies.
        if alive and neighbors < 2:
            return False

        # Rule 2: Live cell with two or three neighbours survives.
        if alive and (neighbors == 2 or neighbors == 3):
            return True

        # Rule 3: Live cell with more than three neighbours dies.
        if alive and neighbors > 3:
            return False

        # Rule 4: Dead cell with exactly three neighbours becomes alive.
        if not alive and neighbors == 3:
            return True

        # All other dead cells remain dead.
        return False

    def compute_next_state(self):
        """Phase 1: count live neighbours, store the result, change nothing."""
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False)
        n = sum(cell.alive for cell in neighbors)  # True counts as 1
        self.next_alive = self.apply_rules(self.alive, n)

    def advance(self):
        """Phase 2: apply the state computed in phase 1."""
        self.alive = self.next_alive

# ----- END CELL AGENT DEFINITION -----


# ----- BEGIN GAME OF LIFE MODEL DEFINITION -----
class GameOfLife(mesa.Model):
    """
    Mesa model holding a width x height grid of Cell agents.

    State:
        - grid: Grid containing the Cell agents.
        - generation (int): Current simulation generation.
        - changed (int): Number of cells that changed state in the last step.
        - births (int): Cells that became alive in the last step.
        - deaths (int): Cells that became dead in the last step.
        - config (dict): Parameters used to recreate the model.
    """

    PATTERNS = PATTERNS  # also reachable as model.PATTERNS

    def __init__(self, width=50, height=50, pattern="random", density=0.3, seed=42, torus=False, live_cells=None):
        """
        Parameters:
            - width (int): Grid width (default: 50).
            - height (int): Grid height (default: 50).
            - pattern (str): Initial configuration (default: "random").
            - density (float): Initial population density (default: 0.3).
            - seed (int): Random seed for reproducibility (default: 42).
            - torus (bool): Whether grid borders wrap around (default: False).
            - live_cells (list): Explicit coordinates of initially live cells.
        """
        self.validate_parameters(width, height, pattern, density, live_cells)
        super().__init__(rng=seed)
        LOG.info('Grid config: height=%d | width=%d | borders=%s | pattern=%s | seed=%s',height, width, "periodic" if torus else "closed", pattern, seed)
        # Parameters needed to build an equivalent model again (UI reset).
        self.config = dict(width=width, height=height, density=density,seed=seed, torus=torus)

        self.grid = SingleGrid(width, height, torus=torus)
        self.generation = 0
        self.changed = 0  # At the initial generation there is no transition.
        self.births = 0
        self.deaths = 0

        
        self._setup_datacollector()
        self._log_ready()

    # Constructor Helpers
    @staticmethod
    def validate_parameters(width, height, pattern, density, live_cells=None):
        """Raise ValueError if the constructor arguments are inconsistent."""
        if width < 5 or height < 5:
            raise ValueError("Dimensions must be at least 5.")
        if not 0 <= density <= 1:
            raise ValueError("Density must be between 0 and 1.")
        if pattern not in (*PATTERNS, "random", "custom"):
            raise ValueError("Unknown pattern.")
        if pattern in PATTERNS:
            pw, ph = pattern_size(pattern)
            if pw > width or ph > height:
                raise ValueError(f'Pattern "{pattern}" needs at least {pw}x{ph} cells.')
        if live_cells is not None:
            if pattern != "custom":
                raise ValueError("live_cells can only be used with pattern 'custom'.")
            if any(not (0 <= x < width and 0 <= y < height) for x, y in live_cells):
                raise ValueError("live_cells contains a position outside the grid.")
        LOG.debug("Parameters validated: %dx%d, pattern=%s, density=%.2f, ""live_cells=%s.", width, height, pattern, density,"none" if live_cells is None else len(live_cells))


    def _setup_datacollector(self):
        """Record generation, alive count and changed count every step."""
        self.datacollector = DataCollector(model_reporters={
            "generation": "generation",
            "alive": lambda m: sum(c.alive for c in m.agents),
            "changed": "changed",
            "births": "births",
            "deaths": "deaths",
        })
        self.datacollector.collect(self)
        LOG.debug("DataCollector ready (generation 0 recorded).")

    def _log_ready(self):
        live = self.live_positions()
        total = self.grid.width * self.grid.height
        alive = len(live)
        dead = total - alive
        density = 100 * alive / total

        LOG.info("Grid state: total=%d | alive=%d | dead=%d", total, alive, dead)
        LOG.info("Generation=0 | alive=%d | dead=%d | density=%.1f%%", alive, dead, density)

        if 0 < alive <= 20:
            LOG.info("Initial live cells: %s", sorted(live))

        if not live:
            LOG.info("Grid state: empty | status=halted")
# ----- END GAME OF LIFE MODEL DEFINITION -----