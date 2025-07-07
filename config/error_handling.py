"""
RadioX Error Handling - Google Style
Centralized error handling following Google Engineering Principles
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException


class ConfigurationError(Exception):
    """Raised when required configuration is missing"""
    pass


class ServiceUnavailableError(Exception):
    """Raised when a required service is unavailable"""
    pass


def create_error_response(
    error_type: str,
    message: str,
    status: str = "error",
    source: str = "service_error"
) -> Dict[str, Any]:
    """Create standardized error response - Google Style"""
    return {
        "error": error_type,
        "status": status,
        "message": message,
        "source": source,
        "timestamp": datetime.now().isoformat()
    }


def raise_configuration_error(service_name: str, missing_config: str) -> None:
    """Raise configuration error with clear message - Fail Fast"""
    raise HTTPException(
        status_code=503,
        detail=f"{service_name}: {missing_config} configuration required"
    )


def raise_service_unavailable(service_name: str, dependency: str) -> None:
    """Raise service unavailable error - Fail Fast"""
    raise HTTPException(
        status_code=503,
        detail=f"{service_name}: {dependency} service unavailable"
    )


# Google Style: No mock data, no fallbacks, clear error communication
def create_unavailable_response(
    service_name: str,
    dependency: str,
    action: str = "configure"
) -> Dict[str, Any]:
    """Create service unavailable response - Google Style"""
    return create_error_response(
        error_type=f"{dependency} unavailable",
        message=f"{action.title()} {dependency} to enable {service_name}",
        status="unavailable",
        source="configuration_error"
    ) 