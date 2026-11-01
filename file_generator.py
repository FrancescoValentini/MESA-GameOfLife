import csv
import logging
from pathlib import Path

import matplotlib.pyplot as plt

logger = logging.getLogger("game_of_life.files")


def save_results(history, alive, changed, folder):
    """Save bitmaps, graphs and CSV statistics."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    logger.info("Saving %d generations to %s", len(history), folder.resolve())

    # First and last generation bitmaps
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))

    axes[0].imshow(history[0], cmap="binary", vmin=0, vmax=1,interpolation="nearest")
    axes[0].set_title("First Generation")

    axes[1].imshow(history[-1], cmap="binary", vmin=0, vmax=1,interpolation="nearest")
    axes[1].set_title(f"Final Generation (n. {len(history) - 1})")

    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])

    fig.tight_layout()
    fig.subplots_adjust(top=0.75)  # Add whitespace at the top
    fig.savefig(folder / "bitmaps.png", dpi=150)
    plt.close(fig)
    logger.debug("bitmaps.png written.")

    # Combined graphs
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(changed, color="tab:orange", label="Changed Cells")
    ax.plot(alive, color="tab:blue", label="Alive Cells")

    ax.set_title("Cell Statistics per Generation")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Number of Cells")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(folder / "graphs.png", dpi=150)
    plt.close(fig)
    logger.debug("graphs.png written.")

    # CSV
    with open(folder / "statistics.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["generation", "alive", "changed"])
        writer.writerows(zip(range(len(alive)), alive, changed))

    logger.debug("statistics.csv written (%d rows).", len(alive))
    logger.info("Results saved to %s", folder.resolve())
