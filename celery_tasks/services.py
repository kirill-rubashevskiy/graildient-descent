import pandas as pd
from fastapi import HTTPException, status

from celery_tasks.config import TEXT_COLS
from graildient_descent.preprocessing import preprocess_text


class PredictionService:
    def __init__(self, model, metrics, scraper):
        self.model = model
        self.metrics = metrics
        self.scraper = scraper

    def predict_from_url(self, listing_url: str) -> float:
        listing_data = self.scraper.get_listing_data(str(listing_url), sold=False)

        if "error" in listing_data:
            error_details = []
            error_details.append(f"Error type: {listing_data['error']}")

            if "status_code" in listing_data:
                error_details.append(f"Status code: {listing_data['status_code']}")

            if "message" in listing_data:
                error_details.append(f"Message: {listing_data['message']}")

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=" | ".join(error_details),
            )

        listing_data_df = pd.DataFrame([listing_data])
        listing_data_df[TEXT_COLS] = listing_data_df[TEXT_COLS].map(preprocess_text)

        return self.model.predict(listing_data_df)[0]

    def predict_from_form(self, listing_data: dict) -> float:
        listing_data_df = pd.DataFrame([listing_data])
        listing_data_df[TEXT_COLS] = listing_data_df[TEXT_COLS].map(preprocess_text)

        return self.model.predict(listing_data_df)[0]
