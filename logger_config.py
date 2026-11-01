import logging

LOG = logging.getLogger("game_of_life")


def configure_logging(debug=False):
    """Configure logging for the Game of Life application."""

    LOG.setLevel(logging.DEBUG if debug else logging.INFO)
    LOG.propagate = False

    # Avoid duplicate handlers if configuration is called more than once.
    if not LOG.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG if debug else logging.INFO)

        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

        LOG.addHandler(handler)

    # Silence third-party libraries.
    logging.getLogger("mesa").setLevel(logging.WARNING)
    logging.getLogger("tkinter").setLevel(logging.WARNING)

    LOG.debug("Logging configured (debug=%s).", debug)