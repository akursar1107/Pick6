"""Structured logging configuration for the application"""

import logging
import logging.config
import sys
from typing import Any, Dict


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.

    This sets up:
    - Console handler with colored output
    - Structured log format with timestamps
    - Separate loggers for different components
    - Request ID tracking (when available)

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    LOGGING_CONFIG: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "[%(filename)s:%(lineno)d] - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": sys.stdout,
            },
            "detailed_console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level,
                "handlers": ["console"],
            },
            # Application loggers
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "app.services.scoring": {
                "level": log_level,
                "handlers": ["detailed_console"],
                "propagate": False,
            },
            "app.services.nfl_ingest": {
                "level": log_level,
                "handlers": ["detailed_console"],
                "propagate": False,
            },
            "app.worker.scheduler": {
                "level": log_level,
                "handlers": ["detailed_console"],
                "propagate": False,
            },
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "apscheduler": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)


class ScoringLogger:
    """
    Specialized logger for scoring operations with structured logging.

    Provides consistent logging format for:
    - Job executions
    - API calls
    - Grading operations
    - Errors and exceptions
    """

    def __init__(self, name: str = "app.services.scoring"):
        self.logger = logging.getLogger(name)

    def log_job_start(self, job_name: str, context: Dict[str, Any] = None) -> None:
        """Log the start of a scheduled job"""
        context_str = f" - Context: {context}" if context else ""
        self.logger.info(f"Job started: {job_name}{context_str}")

    def log_job_complete(
        self, job_name: str, duration: float, results: Dict[str, Any]
    ) -> None:
        """Log successful job completion with results"""
        self.logger.info(
            f"Job completed: {job_name} - Duration: {duration:.2f}s - Results: {results}"
        )

    def log_job_error(self, job_name: str, duration: float, error: Exception) -> None:
        """Log job failure with error details"""
        self.logger.error(
            f"Job failed: {job_name} - Duration: {duration:.2f}s - Error: {str(error)}",
            exc_info=True,
        )

    def log_api_call(
        self, service: str, method: str, params: Dict[str, Any] = None
    ) -> None:
        """Log API call to external service"""
        params_str = f" - Params: {params}" if params else ""
        self.logger.info(f"API call: {service}.{method}{params_str}")

    def log_api_success(
        self, service: str, method: str, duration: float, result_summary: str = None
    ) -> None:
        """Log successful API call"""
        result_str = f" - Result: {result_summary}" if result_summary else ""
        self.logger.info(
            f"API success: {service}.{method} - Duration: {duration:.2f}s{result_str}"
        )

    def log_api_error(
        self,
        service: str,
        method: str,
        duration: float,
        error: Exception,
        retry: int = 0,
    ) -> None:
        """Log API call failure"""
        retry_str = f" - Retry: {retry}" if retry > 0 else ""
        self.logger.error(
            f"API error: {service}.{method} - Duration: {duration:.2f}s{retry_str} - Error: {str(error)}",
            exc_info=True,
        )

    def log_grading_start(self, game_id: str, picks_count: int) -> None:
        """Log start of game grading"""
        self.logger.info(
            f"Grading started: game_id={game_id}, picks_to_grade={picks_count}"
        )

    def log_grading_complete(
        self, game_id: str, picks_graded: int, duration: float, errors: int = 0
    ) -> None:
        """Log completion of game grading"""
        error_str = f", errors={errors}" if errors > 0 else ""
        self.logger.info(
            f"Grading completed: game_id={game_id}, picks_graded={picks_graded}, "
            f"duration={duration:.2f}s{error_str}"
        )

    def log_grading_error(self, game_id: str, error: Exception) -> None:
        """Log grading error"""
        self.logger.error(
            f"Grading error: game_id={game_id} - Error: {str(error)}", exc_info=True
        )

    def log_validation_error(
        self, entity_type: str, entity_id: str, errors: list
    ) -> None:
        """Log data validation error"""
        self.logger.error(
            f"Validation error: {entity_type}={entity_id} - Errors: {errors}"
        )

    def log_pick_result(
        self,
        pick_id: str,
        user_id: str,
        status: str,
        ftd_points: int,
        attd_points: int,
    ) -> None:
        """Log individual pick grading result"""
        self.logger.debug(
            f"Pick graded: pick_id={pick_id}, user_id={user_id}, status={status}, "
            f"ftd_points={ftd_points}, attd_points={attd_points}"
        )

    def log_user_score_update(
        self, user_id: str, points_added: int, new_total: int
    ) -> None:
        """Log user score update"""
        self.logger.debug(
            f"User score updated: user_id={user_id}, points_added={points_added}, "
            f"new_total={new_total}"
        )
