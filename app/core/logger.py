"""Logging configuration."""

import logging


class Logger:
    """Singleton logger class."""

    _instance = None

    def __new__(cls):
        """Ensure only one instance of Logger exists."""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            # Initialize logger
            logger = logging.getLogger("escriba_api")
            logger.setLevel(logging.INFO)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)

            # Add handler to logger
            logger.addHandler(console_handler)

            cls._instance.logger = logger
        return cls._instance

    def info(self, message):
        """Log info level message."""
        self.logger.info(message)

    def error(self, message):
        """Log error level message."""
        self.logger.error(message)

    def debug(self, message):
        """Log debug level message."""
        self.logger.debug(message)

    def warning(self, message):
        """Log warning level message."""
        self.logger.warning(message)


# Create singleton logger instance
log = Logger()
