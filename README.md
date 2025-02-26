# Graildient Descent

[![Python Tests](https://github.com/kirill-rubashevskiy/graildient-descent/actions/workflows/tests.yml/badge.svg)](https://github.com/kirill-rubashevskiy/graildient-descent/actions/workflows/tests.yml)

## Overview

**Graildient Descent** is a machine learning project focused on predicting the sold
prices of items listed on [Grailed](https://www.grailed.com/), an online marketplace for
high-end, pre-owned, and limited edition fashion. The project aims to build a
comprehensive pipeline that includes data collection, preprocessing, model training, and
deployment.

You can explore the project’s interactive results on the
[Streamlit app](https://graildient-descent.streamlit.app).

### Multimodal Data

This project works with multimodal data:

- **Tabular Features**: Item attributes like brand, category, and size
- **Text Features**: Descriptions, titles of items, and hashtags
- **Images**: Collected cover images of items (future work in progress)

## Project Structure

The project is organized into the following main components (some of which are still
under development):

- **graildient_descent/**: Contains the core machine learning pipeline, including:
  - `experiment.py`: Script to run machine learning experiments
  - `model.py`: Model definition and related logic
  - `preprocessing.py`: Data preprocessing steps and utilities
  - `feature_extraction.py`: Text feature extraction utilities
  - `utils.py`: Helper functions used across the project
- **data_collection/**: Contains the scraping scripts and utilities to collect and clean
  data from Grailed
- **airflow/**: Contains the ETL pipeline scripts for Apache Airflow
- **sweeps/**: Contains Weights & Biases (wandb) sweep configurations for ML experiments
- **streamlit_app/**: A Streamlit application to showcase the project with pages for
  EDA, data collection, and predictions
- **api/**: FastAPI application for real-time price predictions, including:
  - `models.py`: Pydantic models and enums for data validation
  - `config.py`: Configuration settings and constants
  - `services.py`: Business logic for predictions
  - `utils.py`: Helper functions
  - `routes.py`: API endpoint definitions
  - `main.py`: Application entry point
  - `logging/`: Request logging and analytics: - `models.py`: Database models for
    request logging - `logger.py`: Request logging functionality - `middleware.py`:
    FastAPI middleware for automatic request logging **celery_tasks/**: Handles
    distributed task processing:
  - `worker.py`: Celery app configuration and prediction tasks
- **tests/**: Contains unit tests for various project components

## Testing and CI/CD

This project implements automated testing using GitHub Actions. The CI pipeline runs on
all pull requests to the main branch and includes a comprehensive test suite covering:

- Data collection and web scraping functionality
- Data preprocessing and feature engineering pipeline
- Model training and evaluation components
- FastAPI application endpoints and services
- Utility functions and helpers

Code quality is maintained through pre-commit hooks that run locally at commit time.

## Getting Started

### Prerequisites

- **Python 3.11**: Ensure you have Python 3.11 installed.
- **Poetry**: The project uses Poetry for dependency management. If you haven't
  installed Poetry, you can do so by following the
  [Poetry installation guide](https://python-poetry.org/docs/#installation).

### Installation

To set up the project, follow these steps:

1. **Clone the repository**:

```bash
git clone https://github.com/kirill-rubashevskiy/graildient-descent.git
cd graildient-descent
```

2. **Install the dependencies and set up pre-commit hooks (for Contributors)**:

For End Users:

```bash
poetry install --without dev
```

For Contributors:

```bash
poetry install --with dev
poetry run pre-commit install
```

## Scraper

### Overview

The `GrailedScraper` is a Python class designed to scrape sold item listings from
[Grailed](https://www.grailed.com/). It collects details such as item names,
descriptions, details, sold prices, and images, which are then used for further
processing and analysis.

<details>

### Setup

Ensure your environment variables for Grailed credentials are set up, or pass them
directly when initializing the `GrailedScraper`.

### Example Usage

```python
from data_collection.scraper import GrailedScraper

scraper = GrailedScraper(email='grailed_email', password='grailed_password')
listings_data, cover_imgs, errors = scraper.scrape()
```

### Notes

Ensure you comply with Grailed’s [Terms of Service](https://www.grailed.com/about/terms)
when scraping data.

</details>

## ETL Pipeline

### Overview

The ETL (Extract, Transform, Load) pipeline is designed to collect, process and manage
data from the Grailed website. The pipeline is implemented using Apache Airflow and
performs the following tasks:

- **Extract**: Collect data from Grailed using the `GrailedScraper`
- **Transform**: Process and clean the collected data
- **Load**: Load the cleaned data into the target data storage

Refer to the Airflow documentation for more details on managing and configuring DAGs.

<details>

### Setup

1. **Install Dependencies**:

   Ensure that you have all necessary dependencies installed. Run the following command
   to install the required Python packages via Poetry:

   ```bash
   poetry install
   ```

2. **Install Apache Airflow**:

   Apache Airflow must be installed using pip as Poetry installation is not supported by
   Apache Airflow. Install Airflow with the following command:

   ```bash
   pip install apache-airflow
   ```

3. **Configure Airflow**:

   Airflow requires a proper configuration. Set up your Airflow environment by
   initializing the database and starting the web server and scheduler.

   ```bash
   airflow db init
   airflow webserver
   airflow scheduler
   ```

4. **Set Up Airflow Variables**:

   Define any required Airflow variables (e.g., connection strings, paths) using the
   Airflow UI or command line.

### Running the ETL Pipeline

1. **Start Airflow**:

   ```bash
   airflow webserver
   airflow scheduler
   ```

2. **Trigger the DAG**:

   ```bash
   airflow dags trigger grailed_etl_dag
   ```

</details>

## ML Experiments

### Running ML Experiments

<details>

You can run machine learning experiments either as single runs or as multiple runs using
wandb sweeps.

#### Single Experiment Run

To run a single experiment with custom arguments, use the following command:

```bash
python3 -m fire graildient_descent/experiment.py run_experiment --arg1 value1 --arg2 value2
```

Replace --arg1, --arg2, etc., with actual arguments and their values specific to the
experiment configuration.

#### Running Multiple Experiments with Wandb Sweeps

For running multiple experiments using Weights & Biases (wandb) sweeps, configure your
sweep in the wandb sweep configuration file, then initiate the sweep:

1. **Create a Sweep**:

   First, define your sweep configuration (e.g., in sweeps/config.yaml).

2. **Run the Sweep**:

   Start the sweep using:

   ```bash
   wandb sweep sweeps/config.yaml
   ```

3. **Launch Agents**:

   After starting the sweep, you can launch multiple agents to run the experiments:

   ```bash
   PYTHONPATH=. wandb agent <sweep_id>
   ```

</details>

### Experiment Results

The ML experiments achieved significant improvements over the baseline model:

- Best performing model: CatBoost with combined tabular and text features
- Final RMSLE: 0.64 (37.1% improvement over baseline)
- Key improvements came from:
  - Using CatBoost model (31% improvement over baseline)
  - Combining tabular and text features (7% improvement over tabular-only model)

For detailed experiment setup and results, visit the ML Experiments section in
[Streamlit App](https://graildient-descent.streamlit.app).

## Streamlit Application

The **Streamlit App** allows users to explore the project's data analysis and prediction
results interactively. It includes the following pages:

- **Intro**: Overview of the project and personal insights into Grailed
- **Data Collection**: Describes the scraping process, collected data, and the building
  of the ETL pipeline (work in progress)
- **EDA**: Explores the data through visualizations and statistics. Currently, the EDA
  page includes:
  - **Numerical Features**: Sold price and photo count analysis
  - **Categorical Features**: Department, category, designer, size, and more
  - **Text Features**: Item name, description, and hashtags
  - **Images**: Planned for a future stage
- **ML Experiments**: Details the machine learning experiment setup, methodology, and
  results
- **Price Predictor**: Interactive form to get price predictions for Grailed listings

The app is deployed on the Streamlit Community Hub, and you can explore it
[here](https://graildient-descent.streamlit.app).

The **FastAPI Service** provides asynchronous price predictions for Grailed listings
through a distributed task processing system. The service is integrated with Celery and
RabbitMQ for handling prediction requests.

### Architecture

- **FastAPI Service**: Handles HTTP requests and submits prediction tasks
- **Celery Worker**: Processes prediction tasks in the background with ML models
- **RabbitMQ**: Message broker for distributing tasks
- **PostgreSQL**: Stores request logs and usage statistics

### Key Endpoints

- **POST /api/v1/predictions/form/submit**: Submit a form-based prediction task
- **POST /api/v1/predictions/url/submit**: Submit a URL-based prediction task
- **GET /api/v1/predictions/{task_id}**: Get prediction results
- **GET /api/v1/tasks/{task_id}/status**: Check task status
- **GET /api/v1/docs/options**: Get valid options for all categorical fields
- **GET /api/v1/models/info**: Get information about the deployed model architecture
  (under construction)
- **GET /api/stats**: Get API usage statistics
- **GET /api/health**: Health check endpoint

### Running with Docker Compose

<details>

1. **Create .env file**:

Create a .env file in the project root with the following variables:

```python
# AWS/S3 Configuration
S3_MODEL_PATH=benchmarks/catboost_v1.pkl
S3_MODELS_BUCKET=graildient-models

# Database Configuration
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=graildient_stats
DATABASE_URL=postgresql://user:password@db:5432/graildient_stats
```

2. **Build and start services**:

```bash
docker compose up --build
```

3. **Access the services**:

- API Documentation: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672 (guest/guest)
- API Health Check: http://localhost:8000/api/health
- API Statistics: http://localhost:8000/api/stats

</details>

## Project Status

The project has made significant progress:

### Completed Steps

- **Data Collection Pipeline**:
  - Implemented web scraper for Grailed sold listings
  - Developed and integrated ETL pipeline using Apache Airflow
  - Built data cleaning and processing workflow
- **Data Analysis & Modeling**:
  - Completed extensive EDA for tabular and text features
  - Conducted ML experiments, achieving 37.1% improvement over baseline
  - Documented experiment methodology and results
- **Deployment**:
  - Deployed Streamlit app showcasing:
    - Data collection process
    - EDA visualizations and insights
    - ML experiment results and methodology
    - Interactive price prediction interface
  - Implemented FastAPI service for real-time predictions
  - Integrated frontend and backend for seamless price predictions
  - Added prediction history tracking
  - Implemented distributed task processing with Celery and RabbitMQ
  - Added asynchronous API endpoints for handling prediction requests

### Next Steps

- Enhance prediction interface with:
  - Price range estimates
  - More detailed prediction explanations
- Complete image feature analysis and integration
- Explore deep learning approaches for potential improvements

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if
you have any suggestions or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for
details.
