import logging

__all__ = [
    "setup_custom_logger"
]

# make RootLogger quiet
root_logger = logging.getLogger()
root_logger.handlers = []


def setup_custom_logger(name, level=logging.INFO):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
