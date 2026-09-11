"""Helpers for Lambda handler event routing."""
import logging

logger = logging.getLogger(__name__)

# Payload sent by the keep-warm EventBridge rule in cloudformation/template.yml.
# The rule sets a constant ``Input``, which replaces the whole event, so a warm
# ping can never be confused with a real HTTP event or an SQS batch.
WARMUP_EVENT = {"warmup": True}


def is_warmup_event(event) -> bool:
    """Return True when ``event`` is a keep-warm ping rather than real work.

    Container-image Lambdas that sit idle for ~14 days lose their cached image
    and the next invoke fails with a 409 ``CodeArtifactUserPendingException``,
    which API Gateway surfaces to the caller as a 500. A periodic ping keeps
    the image cache alive; the handler short-circuits on it so the ping costs
    one init and nothing else.
    """
    return isinstance(event, dict) and event.get("warmup") is True


def warmup_response() -> dict:
    """Standard response for a keep-warm ping."""
    logger.info("Keep-warm ping received; container is warm")
    return {"status": "warm"}
