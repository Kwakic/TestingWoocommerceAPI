"""
Log context manager using contextvars.

Purpose:
- Provide a per-test dynamic context (test_nodeid, correlation_id) that formatters and
  the custom LogRecord factory can read without direct coupling to pytest internals.

This module is intentionally minimal: just contextvars and lightweight docstrings.
It must NOT import pytest or perform I/O at module import time.

log_context can grow over time e.g:
    - request_id = ContextVar("request_id", default="-")
    - span_id = ContextVar("span_id", default="-")
    - retry_attempt = ContextVar("retry_attempt", default=0)
    - step_name = ContextVar("step_name", default=None)

"""

import contextvars

correlation_id = contextvars.ContextVar("correlation_id", default="-")
test_nodeid = contextvars.ContextVar("test_nodeid", default="unknown")
