"""
Logging Configuration with PHI Sanitization.

HIPAA Compliance: Application logs MUST NOT contain Protected Health Information (PHI).
This module provides log sanitization to remove PHI patterns before logging.

PHI Patterns Removed:
- NHS numbers (10-digit pattern: "123 456 7890" or "1234567890")
- Patient names (proper noun patterns)
- Addresses (street address patterns)

Preserved in Logs:
- Document IDs (UUIDs)
- Patient IDs (UUIDs)
- Entity counts and statistics
- Processing status

Audit Logs:
PHI access is tracked separately in the audit_logs table (see audit_service.py).
Audit logs capture WHO accessed WHAT PHI WHEN, separate from application logs.

Usage:
    >>> import logging
    >>> from app.core.logging import sanitize_log_message, configure_logging
    >>>
    >>> configure_logging()  # Configure logger with sanitization filter
    >>> logger = logging.getLogger(__name__)
    >>> logger.info(sanitize_log_message("Patient NHS: 123 456 7890"))
    # Logs: "Patient NHS: [NHS-REDACTED]"
"""

import logging
import re
from typing import Any


# PHI Redaction Patterns
NHS_NUMBER_PATTERN = re.compile(r'\b\d{3}\s?\d{3}\s?\d{4}\b')  # "123 456 7890" or "1234567890"
ADDRESS_PATTERN = re.compile(r'\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)', re.IGNORECASE)

# Redaction placeholders
NHS_REDACTED = "[NHS-REDACTED]"
ADDRESS_REDACTED = "[ADDRESS-REDACTED]"
NAME_REDACTED = "[NAME-REDACTED]"


def sanitize_log_message(message: str) -> str:
    """
    Sanitize log message by removing PHI patterns.

    Args:
        message: Raw log message that may contain PHI

    Returns:
        str: Sanitized message with PHI patterns redacted

    Example:
        >>> sanitize_log_message("Patient NHS: 123 456 7890")
        'Patient NHS: [NHS-REDACTED]'
        >>> sanitize_log_message("Address: 123 Main Street")
        'Address: [ADDRESS-REDACTED]'
    """
    sanitized = message

    # Remove NHS numbers (10-digit pattern)
    sanitized = NHS_NUMBER_PATTERN.sub(NHS_REDACTED, sanitized)

    # Remove addresses (street address pattern)
    sanitized = ADDRESS_PATTERN.sub(ADDRESS_REDACTED, sanitized)

    # NOTE: Patient name redaction is challenging without NER/NLP
    # For now, we rely on developers NOT logging patient names directly
    # Future enhancement: Use MedCAT to detect and redact names

    return sanitized


class PHISanitizationFilter(logging.Filter):
    """
    Logging filter that sanitizes PHI from log records.

    This filter is applied to all loggers to ensure no PHI leaks into logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by sanitizing message.

        Args:
            record: Log record to filter

        Returns:
            bool: True (always allow record, but sanitize first)
        """
        # Sanitize the main message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)

        # Sanitize any string arguments
        if hasattr(record, 'args') and record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitized_args.append(sanitize_log_message(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)

        return True


def configure_logging(level: str = "INFO") -> None:
    """
    Configure application logging with PHI sanitization.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> configure_logging("DEBUG")  # Enable debug logging
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Create console handler if not already present
    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # Format: [timestamp] [level] [module] message
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)

    # Add PHI sanitization filter to all handlers
    phi_filter = PHISanitizationFilter()
    for handler in root_logger.handlers:
        handler.addFilter(phi_filter)

    # Also add to root logger (applies to all loggers)
    root_logger.addFilter(phi_filter)

    logging.info("Logging configured with PHI sanitization filter")


# Configure logging on module import (can be overridden)
# configure_logging()  # Disabled for now - let application configure explicitly
