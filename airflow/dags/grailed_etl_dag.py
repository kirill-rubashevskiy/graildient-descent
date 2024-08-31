import json
import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

default_args = {
    "owner": "airflow",
    "email": "kirill.rubashevskiy@gmail.com",
    "depends_on_past": False,
    "start_date": datetime(2024, 8, 28),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


@dag(
    default_args=default_args,
    description="Scrape sold listings from grailed.com and save to S3",
    schedule="0 12 * * *",  # Daily at noon UTC
    catchup=False,
)
def grailed_etl():

    @task
    def scrape_data():
        """
        Scrape data from grailed.com and save it temporarily.
        """

        from scraper import GrailedScraper

        # Retrieve Grailed credentials from Airflow variables
        GRAILED_EMAIL = Variable.get("GRAILED_EMAIL")
        GRAILED_PASSWORD = Variable.get("GRAILED_PASSWORD")

        logger.info("Starting the scraping process.")

        try:
            scraper = GrailedScraper(email=GRAILED_EMAIL, password=GRAILED_PASSWORD)
            listings_data, cover_imgs, errors = scraper.scrape(n_listings=800)
            logger.info(
                f"Scraped {len(listings_data)} listings and {len(cover_imgs)} images"
            )

            # Save data to a temporary directory
            temp_dir = tempfile.mkdtemp()

            # Save listings data as JSON
            listings_data_path = os.path.join(temp_dir, "listings_data.json")
            with open(listings_data_path, "w") as f:
                json.dump(listings_data, f, indent=4)

            logger.info(f"Listings data saved to {listings_data_path}.")

            # Save images
            idxs = [listing_data["id"] for listing_data in listings_data]
            image_paths = []
            for idx, image_bytes in zip(idxs, cover_imgs, strict=True):
                file_path = os.path.join(temp_dir, f"{idx}.webp")
                with open(file_path, "wb") as f:
                    f.write(image_bytes)
                image_paths.append(file_path)

            logger.info(f"Scraped data saved to temporary directory: {temp_dir}")

            return {
                "temp_dir": temp_dir,
                "listings_data_path": listings_data_path,
                "errors": errors,
                "image_paths": image_paths,
            }

        except Exception as e:
            logger.error("Error during scraping: %s", str(e))
            raise

    @task
    def transform_data(scraped_data: dict):
        """
        Transform the scraped data if needed (e.g., data cleaning, processing).
        """

        import pandas as pd
        import utils

        logger.info("Starting the data transformation process.")

        try:
            # Retrieve scraped data
            temp_dir = scraped_data["temp_dir"]
            listings_data_path = scraped_data["listings_data_path"]
            errors = scraped_data["errors"]
            image_paths = scraped_data["image_paths"]

            listings_df = pd.read_json(listings_data_path)
            listings_df["size"] = listings_df["size"].apply(
                lambda x: utils.extract_size(x)
            )
            listings_df.fillna({"hashtags": "missing"}, inplace=True)
            transformed_listings_data_path = os.path.join(
                temp_dir, "transformed_listings_data.json"
            )
            listings_df.to_json(
                transformed_listings_data_path, orient="records", lines=True
            )

            logger.info("Data transformation completed.")

            return {
                "temp_dir": temp_dir,
                "transformed_listings_data_path": transformed_listings_data_path,
                "errors": errors,
                "image_paths": image_paths,
            }

        except Exception as e:
            logger.error("Error during data transformation: %s", str(e))
            raise

    @task
    def upload_to_s3(transformed_data: dict):
        """
        Upload scraped data to S3, including new listings and error logs.
        """

        import pandas as pd

        # AWS S3 configuration from Airflow variables
        S3_BUCKET = Variable.get("S3_BUCKET")
        LISTINGS_KEY = Variable.get("LISTINGS_KEY")
        ERRORS_KEY = Variable.get("ERRORS_KEY")
        IMAGES_ARCHIVE_KEY = Variable.get("IMAGES_ARCHIVE_KEY")
        DATA_PREFIX = Variable.get("DATA_PREFIX")
        S3_CONN_ID = Variable.get("S3_CONN_ID")

        logger.info("Starting upload to S3.")

        try:
            s3_hook = S3Hook(aws_conn_id=S3_CONN_ID)

            logger.info("Downloading existing data from S3")

            # Check and download existing listings data from S3
            if s3_hook.check_for_key(
                os.path.join(DATA_PREFIX, LISTINGS_KEY), bucket_name=S3_BUCKET
            ):
                listings_obj = s3_hook.get_key(
                    os.path.join(DATA_PREFIX, LISTINGS_KEY), bucket_name=S3_BUCKET
                )
                listings_df = pd.read_csv(listings_obj.get()["Body"])
                logger.info("Existing listings data downloaded from S3")
            else:
                listings_df = (
                    pd.DataFrame()
                )  # Create an empty DataFrame if the file doesn't exist
                logger.warning(
                    "No existing listings data found in S3. Creating a new DataFrame."
                )

            # Check and download existing errors log
            if s3_hook.check_for_key(
                os.path.join(DATA_PREFIX, ERRORS_KEY), bucket_name=S3_BUCKET
            ):
                errors_obj = s3_hook.get_key(
                    os.path.join(DATA_PREFIX, ERRORS_KEY), bucket_name=S3_BUCKET
                )
                errors_df = pd.read_csv(errors_obj.get()["Body"])
                logger.info("Existing errors log downloaded from S3")
            else:
                errors_df = (
                    pd.DataFrame()
                )  # Create an empty DataFrame if the file doesn't exist
                logger.warning(
                    "No existing errors log found in S3. Creating a new DataFrame."
                )

            # Retrieve transformed data
            temp_dir = transformed_data["temp_dir"]
            transformed_listings_data_path = transformed_data[
                "transformed_listings_data_path"
            ]
            errors = transformed_data["errors"]
            image_paths = transformed_data["image_paths"]

            # Append new data
            new_listings_df = pd.read_json(transformed_listings_data_path, lines=True)
            updated_listings_df = pd.concat(
                [listings_df, new_listings_df], ignore_index=True
            )

            # Append new errors
            new_errors_df = pd.DataFrame(errors)
            updated_errors_df = pd.concat([errors_df, new_errors_df], ignore_index=True)

            logger.info("Uploading data to S3")

            # Upload updated listings data to S3
            if not new_listings_df.empty:
                updated_listings_df_path = os.path.join(temp_dir, LISTINGS_KEY)
                updated_listings_df.to_csv(updated_listings_df_path, index=False)
                updated_listings_key = os.path.join(DATA_PREFIX, LISTINGS_KEY)
                s3_hook.load_file(
                    filename=updated_listings_df_path,
                    key=updated_listings_key,
                    bucket_name=S3_BUCKET,
                    replace=True,
                )
                logger.info(
                    f"Updated listings data uploaded to S3 at key: {updated_listings_key}"
                )
            else:
                logger.warning("No new listings to upload to S3")

            # Upload updated errors log to S3
            if not new_errors_df.empty:
                updated_errors_df_path = os.path.join(temp_dir, ERRORS_KEY)
                updated_errors_df.to_csv(updated_errors_df_path, index=False)
                updated_errors_key = os.path.join(DATA_PREFIX, ERRORS_KEY)
                s3_hook.load_file(
                    filename=updated_errors_df_path,
                    key=updated_errors_key,
                    bucket_name=S3_BUCKET,
                    replace=True,
                )
                logger.info(
                    f"Updated errors log uploaded to S3 at key: {updated_errors_key}"
                )
            else:
                logger.info("No new errors to upload to S3")

            # Handle image archive
            image_archive_path = os.path.join(temp_dir, IMAGES_ARCHIVE_KEY)
            existing_images = set()

            # Download the existing image archive from S3
            if s3_hook.check_for_key(
                os.path.join(DATA_PREFIX, IMAGES_ARCHIVE_KEY), bucket_name=S3_BUCKET
            ):
                s3_hook.download_file(
                    key=os.path.join(DATA_PREFIX, IMAGES_ARCHIVE_KEY),
                    bucket_name=S3_BUCKET,
                    local_path=temp_dir,
                    preserve_file_name=True,
                    use_autogenerated_subdir=False,
                )
                logger.info("Existing images archive downloaded from S3.")

                # Read the existing archive and note the contents
                with zipfile.ZipFile(image_archive_path, "r") as zipf:
                    existing_images = set(zipf.namelist())
            else:
                logger.warning(
                    "No existing images archive found in S3. Creating a new archive."
                )

            # Add new images to the archive if they do not exist
            with zipfile.ZipFile(image_archive_path, "a") as zipf:
                for image_path in image_paths:
                    image_name = os.path.basename(image_path)
                    if image_name not in existing_images:
                        zipf.write(image_path, arcname=image_name)
                        logger.info(f"Added new image to archive: {image_name}")
                    else:
                        logger.info(
                            f"Image {image_name} already exists in the archive. Skipping."
                        )

            # Upload the updated images archive to S3
            s3_hook.load_file(
                filename=image_archive_path,
                key=os.path.join(DATA_PREFIX, IMAGES_ARCHIVE_KEY),
                bucket_name=S3_BUCKET,
                replace=True,
            )
            logger.info(
                f"Updated image archive uploaded to S3 at key: {IMAGES_ARCHIVE_KEY}."
            )

            # Clean up and delete temporary directory
            shutil.rmtree(temp_dir)
            logger.info("Temporary folder cleaned up and deleted")

        except Exception as e:
            logger.error("Error during S3 upload: %s", str(e))
            raise

    scraped_data = scrape_data()
    transformed_data = transform_data(scraped_data)
    upload_to_s3(transformed_data)


grailed_etl()
