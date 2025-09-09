import logging

from rich.console import Console
from rich.logging import RichHandler


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a configured logger instance with Rich formatting.

    Args:
        name: Logger name (usually __name__ from calling module)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Setup rich console
        console = Console()

        # Configure logging with Rich handler
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=console, rich_tracebacks=True)],
        )

    return logger
