import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

from dotenv import load_dotenv

load_dotenv()

from mangum import Mangum

from app.configuration.fast_api_config import FastApiConfig
from app.handlers.sqs_handler import SqsHandler
from app.utils.lambda_utils import is_warmup_event, warmup_response

app = FastApiConfig().get_app()

# Mangum handler for AWS Lambda (API Gateway events)
handler = Mangum(app)
sqs_handler = SqsHandler()


def lambda_handler(event, context):
    """AWS Lambda entry point for API Gateway and branch discovery SQS events."""
    if is_warmup_event(event):
        return warmup_response()

    if "Records" in event:
        return sqs_handler.handle(event, context)

    return handler(event, context)


# Local execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
