"""Synthesize AWS Lambda HTTP events (ALB / API Gateway v1 / v2).

Mangum auto-detects the shape, so for FastAPI services `apigw_v2` is the safe
default. ALB is the right pick for Lambdas behind an Application Load Balancer.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

_PATH_PARAM_RE = re.compile(r"\{([^}]+)\}")


def resolve_path(path: str, path_params: Optional[Dict[str, str]]) -> str:
    """Substitute {name} placeholders in path with path_params values."""
    if not path_params:
        return path
    resolved = path
    for key, value in path_params.items():
        resolved = resolved.replace("{" + key + "}", str(value))
    return resolved


def _normalize_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    base = {
        "accept": "application/json",
        "content-type": "application/json",
        "host": "test.example.com",
        "user-agent": "lambda-local-test/1.0",
        "x-forwarded-for": "127.0.0.1",
        "x-forwarded-port": "443",
        "x-forwarded-proto": "https",
    }
    if headers:
        for k, v in headers.items():
            base[k.lower()] = str(v)
    return base


def _serialize_body(body: Any) -> str:
    if body is None:
        return ""
    if isinstance(body, str):
        return body
    return json.dumps(body, ensure_ascii=False)


def build_alb_event(
    method: str,
    path: str,
    query: Optional[Dict[str, Any]] = None,
    body: Any = None,
    headers: Optional[Dict[str, str]] = None,
    path_params: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """ALB target-group event. Used by Lambdas behind an Application Load Balancer."""
    resolved = resolve_path(path, path_params)
    return {
        "requestContext": {
            "elb": {
                "targetGroupArn": (
                    "arn:aws:elasticloadbalancing:us-east-1:"
                    "123456789012:targetgroup/test/1234567890123456"
                )
            }
        },
        "httpMethod": method.upper(),
        "path": resolved,
        "queryStringParameters": {k: str(v) for k, v in (query or {}).items()},
        "headers": _normalize_headers(headers),
        "body": _serialize_body(body),
        "isBase64Encoded": False,
    }


def build_apigw_v1_event(
    method: str,
    path: str,
    query: Optional[Dict[str, Any]] = None,
    body: Any = None,
    headers: Optional[Dict[str, str]] = None,
    path_params: Optional[Dict[str, str]] = None,
    stage: str = "dev",
) -> Dict[str, Any]:
    """API Gateway REST (v1) proxy integration event."""
    resolved = resolve_path(path, path_params)
    qs = {k: str(v) for k, v in (query or {}).items()}
    return {
        "resource": path,
        "path": resolved,
        "httpMethod": method.upper(),
        "headers": _normalize_headers(headers),
        "multiValueHeaders": {k: [v] for k, v in _normalize_headers(headers).items()},
        "queryStringParameters": qs or None,
        "multiValueQueryStringParameters": {k: [v] for k, v in qs.items()} or None,
        "pathParameters": dict(path_params) if path_params else None,
        "stageVariables": None,
        "requestContext": {
            "resourceId": "test",
            "resourcePath": path,
            "httpMethod": method.upper(),
            "path": f"/{stage}{resolved}",
            "stage": stage,
            "requestId": "test-request-id",
            "identity": {"sourceIp": "127.0.0.1", "userAgent": "lambda-local-test/1.0"},
        },
        "body": _serialize_body(body),
        "isBase64Encoded": False,
    }


def build_apigw_v2_event(
    method: str,
    path: str,
    query: Optional[Dict[str, Any]] = None,
    body: Any = None,
    headers: Optional[Dict[str, str]] = None,
    path_params: Optional[Dict[str, str]] = None,
    stage: str = "$default",
) -> Dict[str, Any]:
    """API Gateway HTTP API (v2) proxy event. The default for Mangum/FastAPI."""
    resolved = resolve_path(path, path_params)
    qs = {k: str(v) for k, v in (query or {}).items()}
    raw_query = urlencode(qs)
    now = datetime.now(timezone.utc)
    return {
        "version": "2.0",
        "routeKey": f"{method.upper()} {path}",
        "rawPath": resolved,
        "rawQueryString": raw_query,
        "headers": _normalize_headers(headers),
        "queryStringParameters": qs or None,
        "pathParameters": dict(path_params) if path_params else None,
        "stageVariables": None,
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "test-api",
            "domainName": "test.example.com",
            "domainPrefix": "test",
            "http": {
                "method": method.upper(),
                "path": resolved,
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "lambda-local-test/1.0",
            },
            "requestId": "test-request-id",
            "routeKey": f"{method.upper()} {path}",
            "stage": stage,
            "time": now.strftime("%d/%b/%Y:%H:%M:%S +0000"),
            "timeEpoch": int(now.timestamp() * 1000),
        },
        "body": _serialize_body(body),
        "isBase64Encoded": False,
    }


def build_event(
    shape: str,
    method: str,
    path: str,
    query: Optional[Dict[str, Any]] = None,
    body: Any = None,
    headers: Optional[Dict[str, str]] = None,
    path_params: Optional[Dict[str, str]] = None,
    stage: Optional[str] = None,
) -> Dict[str, Any]:
    shape = (shape or "apigw_v2").lower()
    if shape == "alb":
        return build_alb_event(method, path, query, body, headers, path_params)
    if shape == "apigw_v1":
        return build_apigw_v1_event(
            method, path, query, body, headers, path_params, stage or "dev"
        )
    if shape == "apigw_v2":
        return build_apigw_v2_event(
            method, path, query, body, headers, path_params, stage or "$default"
        )
    raise ValueError(f"Unknown event shape: {shape!r}")


class MockLambdaContext:
    """Mimics the AWS Lambda context object enough for handlers to feel at home."""

    def __init__(self, timeout_ms: int = 60000, function_name: str = "local-test"):
        self.function_name = function_name
        self.function_version = "$LATEST"
        self.invoked_function_arn = (
            f"arn:aws:lambda:us-east-1:123456789012:function:{function_name}"
        )
        self.memory_limit_in_mb = 1024
        self.aws_request_id = "test-request-id"
        self.request_id = "test-request-id"
        self.log_group_name = f"/aws/lambda/{function_name}"
        self.log_stream_name = "2026/01/01/[$LATEST]test"
        self._remaining_time = timeout_ms

    def get_remaining_time_in_millis(self) -> int:
        return self._remaining_time
