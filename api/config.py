import logging
import os


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
S3_MODEL_PATH = os.getenv("S3_MODEL_PATH")
S3_MODELS_BUCKET = "graildient-models"
TEXT_COLS = ["item_name", "description", "hashtags"]
