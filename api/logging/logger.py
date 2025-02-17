import logging
from typing import Optional

from fastapi import Request, Response
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from api.config import DATABASE_URL

from .models import APIRequest, Base


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


class RequestLogger:
    """Handles logging of FastAPI requests to PostgreSQL"""

    def __init__(self):
        self.db = SessionLocal()

    async def log_request(
        self,
        request: Request,
        response: Response,
        response_time: float,
        error_detail: Optional[str] = None,
    ):
        """
        Log the API request details to PostgreSQL

        Args:
            request: FastAPI request object
            response: FastAPI response object
            response_time: Time taken to process the request in seconds
            error_detail: Optional error message if request failed
        """
        try:
            # Extract client IP, handling potential proxy headers
            client_ip = request.client.host
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0]

            # Create log entry
            log_entry = APIRequest(
                client_ip=client_ip,
                request_path=request.url.path,
                method=request.method,
                response_time=response_time,
                status_code=response.status_code,
                error_detail=error_detail,
                user_agent=request.headers.get("User-Agent", "Unknown"),
            )

            # Save to database
            self.db.add(log_entry)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")
            self.db.rollback()
        finally:
            self.db.close()

    def get_usage_stats(self, days: int = 7) -> dict:
        """
        Get basic usage statistics for the specified number of days

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary containing usage statistics
        """
        try:
            # Calculate stats using SQL
            stats = {
                "total_requests": self.db.query(APIRequest).count(),
                "avg_response_time": self.db.query(
                    func.avg(APIRequest.response_time)
                ).scalar(),
                "error_rate": (
                    self.db.query(APIRequest)
                    .filter(APIRequest.status_code >= 400)
                    .count()
                    / self.db.query(APIRequest).count()
                )
                * 100,
                "endpoint_usage": {
                    path: count
                    for path, count in self.db.query(
                        APIRequest.request_path, func.count(APIRequest.id)
                    )
                    .group_by(APIRequest.request_path)
                    .all()
                },
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get usage stats: {str(e)}")
            return {}
        finally:
            self.db.close()
