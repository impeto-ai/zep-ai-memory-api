"""
Módulo de métricas para observabilidade.
"""

from .prometheus import (
    PrometheusMetrics,
    get_metrics,
    timed_operation,
    increment_api_request,
    observe_duration
)

__all__ = [
    "PrometheusMetrics",
    "get_metrics",
    "timed_operation",
    "increment_api_request",
    "observe_duration"
]