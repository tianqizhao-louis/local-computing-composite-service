from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
import time
import uuid
from fastapi import Request
from fastapi.exceptions import HTTPException
from app.api.auth import verify_jwt_token
from contextvars import ContextVar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("composite-service")

correlation_id = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """Helper function to get current correlation ID"""
    return correlation_id.get()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        cor_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id.set(cor_id)
        request.state.correlation_id = cor_id

        # Log request details with correlation ID
        logger.info(f"[{cor_id}] Request started: {request.method} {request.url}")
        logger.info(f"[{cor_id}] Query parameters: {request.query_params}")

        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Log response details with correlation ID and timing
        process_time = time.time() - start_time
        logger.info(
            f"[{cor_id}] Request completed in {process_time:.4f} seconds with status code {response.status_code}"
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = cor_id

        return response


class JWTMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, excluded_paths: list[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or []

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        # Exclude paths from middleware
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        try:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=401, detail="Authorization header is missing"
                )

            # Check if it is a Bearer token
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Invalid Authorization header format"
                )

            # Extract the token
            token = auth_header.split("Bearer ")[1]

            # Validate the token using the custom function
            if not verify_jwt_token(token):
                raise HTTPException(status_code=401, detail="Invalid or expired token")

            # Proceed to the next middleware or route handler
            response = await call_next(request)
            return response

        except HTTPException as http_exc:
            # Handle HTTPException explicitly and return a JSON response
            return JSONResponse(
                status_code=http_exc.status_code,
                content={"detail": http_exc.detail},
            )
        except Exception as exc:
            # Handle unexpected exceptions and return a 500 response
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal server error occurred"},
            )
