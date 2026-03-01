"""
API Call Instrumentation for Damascus 3D Simulator
===================================================

Wraps public methods on simulator classes with structured logging so every
invocation records the callable name, source file, and definition line.

Usage:
    from lib.api_instrumentation import install_api_call_logging
    install_api_call_logging(MyClass1, MyClass2)
"""

import functools
import inspect
import os
from typing import Tuple

from lib.logging_config import logger


def _resolve_source_location(func) -> Tuple[str, int]:
    """Return source filename and definition start line for a callable."""
    source_path = inspect.getsourcefile(func)
    source_file = os.path.basename(source_path) if source_path else "<unknown>"
    try:
        source_line = inspect.getsourcelines(func)[1]
    except (OSError, TypeError):
        source_line = -1
    return source_file, source_line


def _api_call_wrapper(func):
    """Wrap callable to emit a structured API call log on each invocation."""
    if getattr(func, "_damascus_api_wrapped", False):
        return func

    source_file, source_line = _resolve_source_location(func)

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        logger.info(
            "API_CALL | %s | file=%s | starts_at_line=%d",
            func.__qualname__,
            source_file,
            source_line,
        )
        return func(*args, **kwargs)

    wrapped._damascus_api_wrapped = True
    return wrapped


def install_api_call_logging(*classes):
    """
    Instrument public methods on the given classes with API_CALL logs.

    Public methods (those not starting with '_') are wrapped so each
    invocation records the callable, source file, and definition line.

    Args:
        *classes: One or more classes to instrument.
    """
    for cls in classes:
        for attr_name, attr_value in list(vars(cls).items()):
            if attr_name.startswith('_'):
                continue
            if not inspect.isfunction(attr_value):
                continue
            setattr(cls, attr_name, _api_call_wrapper(attr_value))
