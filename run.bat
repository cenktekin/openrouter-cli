@echo off
@REM    import logging
@REM    logging.getLogger("httpx").setLevel(logging.WARNING)  # Disable INFO logs
@REM httpx_logger = logging.getLogger(“httpx”)
@REM httpx_logger.setLevel(logging.WARNING)
set DEBUG=off
python run.py
