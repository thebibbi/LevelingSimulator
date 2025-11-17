"""
Structured logging configuration
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from pythonjsonlogger import jsonlogger
from config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["environment"] = settings.environment

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging():
    """Configure application logging"""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with JSON formatting in production
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.is_production:
        console_formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_dir / "api.log")
    file_formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Error file handler
    error_handler = logging.FileHandler(log_dir / "error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logging.info(
        "Logging configured",
        extra={"log_level": settings.log_level, "environment": settings.environment},
    )


# Request logging middleware
async def log_request(request, call_next):
    """Log HTTP requests"""
    logger = logging.getLogger("api.requests")

    start_time = datetime.utcnow()

    # Log request
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
        },
    )

    # Process request
    try:
        response = await call_next(request)

        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration,
            },
        )

        return response

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(
            "Request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "duration_ms": duration,
            },
            exc_info=True,
        )
        raise
