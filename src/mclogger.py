__all__ = ["mclogger"]

import logging
import sys
from pathlib import Path

import __main__
from version import __app_name__


class Logger:
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self):
        self.logger = logging.getLogger(__app_name__)
        self.logger.propagate = False
        self._interactive = self._is_interactive()

    def _is_interactive(self):
        # Case 1: Python REPL / IPython / Jupyter
        if hasattr(sys, "ps1") or not hasattr(__main__, "__file__"):
            return True
        # Case 2: Script is being run directly (not piped or redirected)
        return sys.stdin.isatty() and sys.stdout.isatty()

    @property
    def interactive(self):
        return self._interactive

    def setup(
        self,
        log_file_path,
        log_level=logging.INFO,
        stdout_enabled=False,
        stdout_only=False,
    ):
        if self.logger.handlers:
            self.logger.handlers.clear()

        self.logger.setLevel(log_level)

        # Add file handler unless stdout_only is enabled
        if not stdout_only:
            try:
                # Ensure directory exists before creating file handler
                import os

                log_dir = Path(log_file_path).parent
                if log_dir and not log_dir.exists():
                    log_dir.mkdir(parents=True, exist_ok=True)

                file_handler = logging.FileHandler(log_file_path)
                file_handler.setLevel(log_level)
                file_formatter = logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)

                # Test write to ensure the handler is working
                self.logger.info("Logger initialized successfully")

            except (OSError, PermissionError) as e:
                # If file logging fails, fall back to stderr and continue
                # This ensures the application doesn't fail silently in file manager contexts
                stderr_handler = logging.StreamHandler()
                stderr_handler.setLevel(log_level)
                stderr_formatter = logging.Formatter("%(levelname)s: %(message)s")
                stderr_handler.setFormatter(stderr_formatter)
                self.logger.addHandler(stderr_handler)
                self.logger.error(
                    f"Failed to initialize file logging to {log_file_path}: {e}"
                )
                self.logger.error("Falling back to stderr logging")

        # Add stdout handler if requested or if stdout_only is enabled
        if stdout_enabled or stdout_only:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter("%(levelname)s: %(message)s")
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message):
        if self.logger.isEnabledFor(logging.DEBUG):
            # if self._interactive:
            #     print("DEBUG: " + message)
            self.logger.debug(message)

    def info(self, message):
        if self.logger.isEnabledFor(logging.INFO):
            # if self._interactive:
            #     print("INFO:  " + message)
            self.logger.info(message)

    def error(self, message):
        if self.logger.isEnabledFor(logging.ERROR):
            # if self._interactive:
            #     print("ERROR: " + message)
            self.logger.error(message)

    def critical(self, message):
        # if self._interactive:
        #     print("CRIT:  " + message)
        self.logger.critical(message)

    def warning(self, message):
        if self.logger.isEnabledFor(logging.WARNING):
            # if self._interactive:
            #     print("WARN:  " + message)
            self.logger.warning(message)


logger = Logger()
