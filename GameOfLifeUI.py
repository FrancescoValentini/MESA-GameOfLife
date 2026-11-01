"""
GameOfLifeUI.py - Tkinter + Matplotlib front-end for the Mesa model.

How it works with a forward-only model
--------------------------------------
* The Mesa model always sits at the LATEST computed generation.
* The UI records a snapshot (``model.matrix()``) of every generation in
  ``self.history`` and just moves ``self.index`` through it:
    - Previous / Next inside the history only change what is DISPLAYED;
    - Next at the end of the history calls ``model.step()`` and records it.
* Clicking a cell edits the Cell agent directly (only on the latest
  generation, where the model really is).
* Reset / Apply Pattern build a NEW ``GameOfLife`` from the saved
  configuration, so no state-copying code is needed.
"""
import logging

from matplotlib.figure import Figure

from GameOfLife import GameOfLife
from file_generator import save_results

LOG = logging.getLogger("game_of_life.ui")


class GameOfLifeUI:
    def __init__(self, model, steps, results):
        # Tkinter is imported lazily so headless mode works without a display.
        import tkinter as tk
        from tkinter import ttk

        self.tk, self.ttk = tk, ttk
        self.model, self.steps, self.results = model, steps, results
        self.running = False
        self.after_id = None
        self.initial_live = model.live_positions()  # what Reset restores
        self._reset_history()
        LOG.info("UI created (max %d generations, results -> %s).",
                 steps, results)

        self.root = tk.Tk()
        self.root.title("Conway's Game of Life")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._build_controls()
        self._build_figure()
        self.refresh()

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def _build_controls(self):
        tk, ttk = self.tk, self.ttk
        controls = ttk.Frame(self.root, padding=5)
        controls.pack(fill=tk.X)

        for text, command in [("Play", self.play), ("Pause", self.pause),
                              ("Previous", self.previous), ("Next", self.next),
                              ("Save", self.save), ("Reset", self.reset)]:
            ttk.Button(controls, text=text, command=command).pack(side=tk.LEFT)

        ttk.Label(controls, text="Speed").pack(side=tk.LEFT, padx=8)
        self.speed = tk.DoubleVar(value=5)
        ttk.Scale(controls, from_=1, to=30, variable=self.speed,
                  orient=tk.HORIZONTAL).pack(side=tk.LEFT)

        self.label = ttk.Label(controls, text="Generation: 0")
        self.label.pack(side=tk.RIGHT)

        ttk.Label(controls, text="Pattern").pack(side=tk.LEFT, padx=(10, 2))
        self.pattern_var = tk.StringVar(value="glider")
        ttk.Combobox(controls, textvariable=self.pattern_var,
                     values=["random", "custom", *GameOfLife.PATTERNS],
                     state="readonly", width=12).pack(side=tk.LEFT)
        ttk.Button(controls, text="Apply Pattern",
                   command=self.apply_pattern).pack(side=tk.LEFT, padx=5)

    def _build_figure(self):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.fig = Figure(figsize=(12, 8))
        axes = self.fig.subplots(2, 2)
        self.ax_prev, self.ax_current, self.ax_alive, self.ax_changed = axes.flatten()

        self.ax_prev.set_title("Previous generation")
        self.ax_current.set_title("Current generation (click latest to draw)")
        self.prev_img = self.ax_prev.imshow(
            self.history[0], cmap="binary", vmin=0, vmax=1, interpolation="nearest")
        self.current_img = self.ax_current.imshow(
            self.history[0], cmap="binary", vmin=0, vmax=1, interpolation="nearest")
        for ax in (self.ax_prev, self.ax_current):
            ax.set_xticks([])
            ax.set_yticks([])

        self.alive_line, = self.ax_alive.plot([], [])
        self.ax_alive.set_title("Alive cells per generation")
        self.ax_alive.set_xlabel("Generation")
        self.ax_alive.set_ylabel("Alive cells")
        self.ax_alive.grid()

        self.changed_line, = self.ax_changed.plot([], [])
        self.ax_changed.set_title("Changed cells per generation")
        self.ax_changed.set_xlabel("Generation")
        self.ax_changed.set_ylabel("Births + deaths")
        self.ax_changed.grid()

        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=self.tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_click)

    def _reset_history(self):
        """Start recording from the model's current (generation 0) state."""
        self.history = [self.model.matrix()]
        self.alive = [len(self.model.live_positions())]
        self.changed = [0]
        self.index = 0

    def _rebuild_model(self, pattern, live_cells=None):
        """Create a fresh model with the same settings and a new start."""
        self.pause()
        self.model = GameOfLife(pattern=pattern, live_cells=live_cells,
                                **self.model.config)
        self.initial_live = self.model.live_positions()
        self._reset_history()
        self.refresh()

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def reset(self):
        """Restart from the stored generation 0 (including drawn cells)."""
        LOG.info("Resetting to generation 0 (%d live cells).",
                 len(self.initial_live))
        self._rebuild_model("custom", self.initial_live)

    def apply_pattern(self):
        """Replace the board with the chosen pattern."""
        name = self.pattern_var.get()
        LOG.info('Applying pattern "%s".', name)
        self._rebuild_model(name)

    def next(self):
        """Show the next generation (replay from history, or compute it)."""
        if self.index < len(self.history) - 1:
            self.index += 1                       # already computed: view only
            LOG.debug("Viewing generation %d from history.", self.index)
        elif self.index < self.steps:
            self.model.step()                     # model is at the latest gen
            if self.model.generation == self.index:   # halted: all cells dead
                LOG.info("Nothing to compute: all cells are dead "
                         "(draw some cells to continue).")
                self.pause()
                return
            self.history.append(self.model.matrix())
            self.alive.append(len(self.model.live_positions()))
            self.changed.append(self.model.changed)
            self.index += 1
            LOG.debug("Computed generation %d: %d alive, %d changed.",
                      self.index, self.alive[-1], self.changed[-1])
        self.refresh()

    def previous(self):
        """Look at the previous generation (display only)."""
        self.pause()
        if self.index > 0:
            self.index -= 1
            LOG.debug("Viewing generation %d from history.", self.index)
        self.refresh()

    def play(self):
        if not self.running and self.index < self.steps:
            self.running = True
            LOG.info("Play from generation %d.", self.index)
            self.tick()

    def pause(self):
        if self.running:
            LOG.info("Paused at generation %d.", self.index)
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def tick(self):
        """One animation frame; reschedules itself while running."""
        if not self.running:
            return
        self.next()
        halted = self.index == len(self.history) - 1 and not self.model.running
        if self.index < self.steps and not halted:
            delay = int(1000 / max(0.1, self.speed.get()))
            self.after_id = self.root.after(delay, self.tick)
        else:
            LOG.info("Stopped at generation %d (%s).", self.index,
                     "all cells dead" if halted else "step limit reached")
            self.pause()

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------
    def on_click(self, event):
        """Toggle a Cell agent of the latest generation."""
        if event.inaxes != self.ax_current or event.xdata is None or event.ydata is None:
            return

        # imshow centres pixel i at coordinate i, so round() (not int()).
        x, y = int(round(event.xdata)), int(round(event.ydata))
        if not (0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height):
            return

        self.pause()
        if self.index != len(self.history) - 1:
            LOG.info("Edit ignored: go to the latest generation (%d) to draw.",
                     len(self.history) - 1)
            return

        cell = self.model.grid.get_cell_list_contents([(x, y)])[0]
        cell.alive = cell.next_alive = not cell.alive
        LOG.info("Cell (%d, %d) set to %s at generation %d.",
                 x, y, cell.alive, self.index)

        self.history[-1] = self.model.matrix()
        self.alive[-1] = len(self.model.live_positions())
        if self.index == 0:
            self.initial_live = self.model.live_positions()  # Reset keeps it
        self.refresh()

    # ------------------------------------------------------------------
    # Drawing / persistence
    # ------------------------------------------------------------------
    def refresh(self):
        """Redraw grids, statistic curves and the generation label."""
        self.prev_img.set_data(self.history[max(0, self.index - 1)])
        self.current_img.set_data(self.history[self.index])

        generations = range(len(self.alive))
        self.alive_line.set_data(generations, self.alive)
        self.changed_line.set_data(generations, self.changed)
        for ax in (self.ax_alive, self.ax_changed):
            ax.relim()
            ax.autoscale_view()

        self.label.config(text=f"Generation: {self.index}")
        self.canvas.draw_idle()

    def save(self):
        LOG.info("Saving results (%d generations).", len(self.history) - 1)
        save_results(self.history, self.alive, self.changed, self.results)

    def close(self):
        """Window closed: stop the animation, save, destroy the window."""
        self.pause()
        self.save()
        self.root.destroy()

    def run(self):
        self.root.mainloop()