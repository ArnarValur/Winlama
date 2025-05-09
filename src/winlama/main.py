"""
Main entry point for the Winlama application.
"""
import logging
import sys
import os

from ui.app import Application

def setup_logging():
    """Set up application logging."""
    logger = logging.getLogger('winlama')
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(console_handler)

    # Log file in user's home directory
    try:
        log_dir = os.path.join(os.path.expanduser("~"), ".winlama")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "winlama.log")

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")

    return logger

def main():
    """Main entry point for the application."""
    logger = setup_logging()
    logger.info("Starting Winlama...")

    try:
        app = Application()
        app.run()
    except Exception as e:
        logger.exception(f"Unhandled exception in main: {e}")
        raise

if __name__ == "__main__":
    main()
