# Graildient Descent

## Overview

**Graildient Descent** is a machine learning project focused on predicting the sold
prices of items listed on [Grailed](https://www.grailed.com/), an online marketplace for
high-end, pre-owned, and limited edition fashion. The project aims to build a
comprehensive pipeline that includes data collection, preprocessing, model training, and
deployment.

You can explore the project’s interactive results on the
[Streamlit App](https://graildient-descent.streamlit.app).

### Multimodal Data

This project works with multimodal data:

- **Tabular Features**: Item attributes like brand, category, and size.
- **Text Features**: Descriptions, titles of items, and hashtags.
- **Images**: Collected cover images of items (future work in progress).

## Project Structure

The project is organized into the following main components (some of which are still
under development):

- **graildient_descent/**: Contains the core machine learning pipeline, including:
  - `experiment.py`: Script to run machine learning experiments.
  - `model.py`: Model definition and related logic.
  - `preprocessing.py`: Data preprocessing steps and utilities.
  - `feature_extraction.py`: Text feature extraction utilities.
  - `utils.py`: Helper functions used across the project.
- **data_collection/**: Contains the scraping scripts and utilities to collect and clean
  data from Grailed.
- **airflow/**: Contains the ETL pipeline scripts for Apache Airflow.
- **streamlit_app/**: A Streamlit application to showcase the project with pages for
  EDA, data collection, and predictions.
- **fastapi_app/**: (To be developed) A FastAPI application for deploying the model as a
  service.
- **tests/**: Contains unit tests for various project components.

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

## Scraper Usage

<details>

### Overview

The `GrailedScraper` is a Python class designed to scrape sold item listings from
[Grailed](https://www.grailed.com/). It collects details such as item names,
descriptions, details, sold prices, and images, which are then used for further
processing and analysis.

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

## ETL Pipeline Usage

<details>

### Overview

The ETL (Extract, Transform, Load) pipeline is designed to collect, process and manage
data from the Grailed website. The pipeline is implemented using Apache Airflow and
performs the following tasks:

- **Extract**: Collect data from Grailed using the `GrailedScraper`.
- **Transform**: Process and clean the collected data.
- **Load**: Load the cleaned data into the target data storage.

Refer to the Airflow documentation for more details on managing and configuring DAGs.

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

## Running ML Experiments

You can run machine learning experiments either as single runs or as multiple runs using
Weights & Biases (wandb) sweeps.

### Single Experiment Run

To run a single experiment with custom arguments, use the following command:

```bash
python3 -m fire graildient_descent/experiment.py run_experiment --arg1 value1 --arg2 value2
```

Replace --arg1, --arg2, etc., with actual arguments and their values specific to the
experiment configuration.

### Running Multiple Experiments with Wandb Sweeps

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

## Streamlit Application

The **Streamlit App** allows users to explore the project's data analysis and prediction
results interactively. It includes the following pages:

- **Intro**: Overview of the project and personal insights into Grailed.
- **Data Collection**: Describes the scraping process, collected data, and the building
  of the ETL pipeline (work in progress).
- **EDA**: Explores the data through visualizations and statistics. Currently, the EDA
  page includes:
  - **Numerical Features**: Sold price and photo count analysis.
  - **Categorical Features**: Department, category, designer, size, and more.
  - **Text Features**: Item name, description, and hashtags.
  - **Images**: Planned for a future stage.
- **Predict**: Demonstrates the current model's prediction capabilities (work in
  progress).

The app is deployed on the Streamlit Community Hub, and you can explore it
[here](https://graildient-descent.streamlit.app).

## Project Status

The project has advanced significantly beyond its initial setup phase. The following
components have been implemented and are actively being developed:

- **Scraper**: The web scraper, `GrailedScraper`, is in place to collect data from
  Grailed. It can extract details of sold items, including names, descriptions, details,
  sold prices, and images.
- **ETL Pipeline**: The ETL pipeline, now implemented using Apache Airflow, processes
  and cleans the collected data. The pipeline includes the necessary components to
  manage data extraction, transformation, and loading effectively.
- **Exploratory Data Analysis (EDA)**: A comprehensive analysis of tabular and text
  features has been implemented. A section for image features is planned for future
  stages.
- **ML Experiments**: The machine learning experiments have been set up with necessary
  configurations, preprocessing, and feature extraction.
- **Streamlit App**: The app is currently under development to showcase EDA results and
  prediction functionalities.

## Roadmap

- **Completed**:

  - Implemented the web scraper for Grailed sold listings.
  - Developed and integrated the ETL pipeline using Apache Airflow.
  - Initial Exploratory Data Analysis (EDA) completed for tabular and text features.
  - Machine learning experiment setup, including configurations, preprocessing, and
    feature extraction.

- **Next Steps**:
  - Finalize and enhance EDA, especially for image features.
  - Develop and train machine learning models for price prediction.
  - Build and deploy a Streamlit application for model visualization.
  - Implement a FastAPI service for real-time predictions.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if
you have any suggestions or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for
details.
