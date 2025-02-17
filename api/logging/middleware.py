import time

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from .logger import RequestLogger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all API requests"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = RequestLogger()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Record start time
        start_time = time.time()
        error_detail = None
        response = None

        try:
            # Process the request
            response = await call_next(request)
            return response
        except Exception as e:
            error_detail = str(e)
            raise
        finally:
            # Calculate response time
            response_time = time.time() - start_time

            # Log the request asynchronously
            if response:  # Only log if we got a response
                await self.logger.log_request(
                    request=request,
                    response=response,
                    response_time=response_time,
                    error_detail=error_detail,
                )


def setup_request_logging(app: FastAPI):
    """Add request logging middleware to FastAPI app"""
    app.add_middleware(LoggingMiddleware)

    # Add endpoint for viewing usage statistics
    @app.get("/api/stats")
    async def get_api_stats(days: int = 7):
        logger = RequestLogger()
        return logger.get_usage_stats(days=days)
