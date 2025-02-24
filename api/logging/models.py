from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class APIRequest(Base):
    """Model for storing API request data"""

    __tablename__ = "api_requests"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    client_ip = Column(String)
    request_path = Column(String)
    method = Column(String)
    response_time = Column(Float)  # in seconds
    status_code = Column(Integer)
    error_detail = Column(String, nullable=True)
    user_agent = Column(String)
