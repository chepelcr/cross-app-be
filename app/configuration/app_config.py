"""
Configuration client — env vars first (local/Docker), SSM Parameter Store in Lambda.

Resolution order per key:
  1. Environment variable  (DATABASE_HOST, S3_BUCKET, etc.)
  2. SSM Parameter Store   (only when running in AWS Lambda)
  3. default argument

SSM base path is read from app/settings.cfg per stage:
  DEVELOPMENT -> /jcampos/dev/cd-backend
  STAGING     -> /jcampos/stag/cd-backend
  PRODUCTION  -> /jcampos/prod/cd-backend

Dot-notation key mapping:
  "s3.bucket"           -> /jcampos/{env}/cd-backend/s3/bucket
  "api.services.url"    -> /jcampos/{env}/cd-backend/api/services/url
  "cloudfront.distribution.id" -> /jcampos/{env}/cd-backend/cloudfront/distribution/id
"""
import os
import time
import configparser
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# SSM is only attempted when running inside Lambda
_IN_LAMBDA = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


class AppConfig:
    _instance: Optional["AppConfig"] = None
    _base_path: str = ""
    _cache: Dict[str, Tuple[Any, float]] = {}
    _cache_ttl: int = 300  # 5 minutes
    _ssm_client = None

    def __new__(cls) -> "AppConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        stage = os.environ.get("STAGE", "DEVELOPMENT").upper()
        stage_mapping = {
            "DEV": "DEVELOPMENT", "DEVELOPMENT": "DEVELOPMENT",
            "STAG": "STAGING",    "STAGING": "STAGING",
            "PROD": "PRODUCTION", "PRODUCTION": "PRODUCTION",
        }
        section = stage_mapping.get(stage, "DEVELOPMENT")
        stage_lower = {"DEVELOPMENT": "dev", "STAGING": "stag", "PRODUCTION": "prod"}.get(section, "dev")

        parser = configparser.ConfigParser()
        for path in ["app/settings.cfg", "settings.cfg", "../settings.cfg"]:
            if os.path.exists(path):
                parser.read(path)
                break

        self._base_path = (
            parser.get(section, "ssmpath", fallback=None)
            if section in parser
            else None
        ) or f"/jcampos/{stage_lower}/cd-backend"

        logger.debug(f"AppConfig initialized: base_path={self._base_path}, lambda={_IN_LAMBDA}")

    def _get_ssm_client(self):
        if self._ssm_client is None:
            import boto3
            self._ssm_client = boto3.client("ssm")
        return self._ssm_client

    def _dot_to_ssm_path(self, key: str) -> str:
        return f"{self._base_path}/{key.replace('.', '/')}"

    @classmethod
    def get_key(cls, key: str, default: Any = None) -> Any:
        # 1. Environment variable (local dev / Docker — always wins)
        env_key = key.replace(".", "_").upper()
        value = os.getenv(env_key)
        if value is not None:
            if isinstance(default, int) and value.isdigit():
                return int(value)
            return value

        # 2. SSM Parameter Store (Lambda only)
        if not _IN_LAMBDA:
            return default

        instance = cls()
        now = time.time()
        cached = instance._cache.get(key)
        if cached is not None:
            val, ts = cached
            if now - ts < instance._cache_ttl:
                return val if val is not None else default

        ssm_path = instance._dot_to_ssm_path(key)
        try:
            resp = instance._get_ssm_client().get_parameter(Name=ssm_path)
            val = resp["Parameter"]["Value"]
            instance._cache[key] = (val, now)
            if isinstance(default, int) and val.isdigit():
                return int(val)
            return val
        except Exception as e:
            logger.debug(f"SSM parameter not found: {ssm_path} — {e}")
            instance._cache[key] = (None, now)
            return default
