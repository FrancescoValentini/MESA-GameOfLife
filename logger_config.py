import logging

LOG = logging.getLogger("game_of_life.logger_config")

def configure_logging(debug=False):
    """Attach one console handler to the project logger"""
    LOG.setLevel(logging.DEBUG if debug else logging.INFO)
    LOG.propagate = False
    if not LOG.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"))
        LOG.addHandler(handler)
    LOG.debug("Logging configured (debug=%s).", debug)