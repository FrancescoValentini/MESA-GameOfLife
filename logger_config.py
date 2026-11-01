import logging
import sys

LOG = logging.getLogger("game_of_life")


def configure_logging(debug=False, log_file=None):
    """Configure logging for the Game of Life application.

    Args:
        debug (bool): Enable DEBUG-level logging.
        log_file (str, optional): Path to a log file. If provided,
            logs are written to both stderr and the file.
    """
    level = logging.DEBUG if debug else logging.INFO

    LOG.setLevel(level)
    LOG.propagate = False

    # Remove existing handlers to avoid duplicates and allow
    # reconfiguration (e.g. changing log_file or debug mode).
    for handler in LOG.handlers[:]:
        handler.close()
        LOG.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)-7s - %(name)-19s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Always log to stderr.
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(formatter)
    LOG.addHandler(stderr_handler)

    # Optionally log to file.
    if log_file:
        file_handler = logging.FileHandler(log_file,encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        LOG.addHandler(file_handler)

    # Silence third-party libraries.
    logging.getLogger("mesa").setLevel(logging.WARNING)
    logging.getLogger("tkinter").setLevel(logging.WARNING)

    LOG.debug("Logging configured (debug=%s, log_file=%s).",debug, log_file)