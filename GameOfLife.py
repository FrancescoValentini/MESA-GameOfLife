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

