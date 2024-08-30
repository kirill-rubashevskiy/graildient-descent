# Graildient Descent

## Overview

**Graildient Descent** is a machine learning project focused on predicting the sold
prices of items listed on [Grailed](https://www.grailed.com/), an online marketplace for
high-end, pre-owned, and limited edition fashion. The project aims to build a
comprehensive pipeline that includes data collection, preprocessing, and model training
to make accurate sold price predictions based on various features.

This README provides a brief overview of the project and instructions on setting up the
development environment.

## Project Structure

The project is organized into the following main components (some of which are still
under development):

- **graildient_descent/**: The core machine learning pipeline and related modules.
- **data_collection/**: Contains the scraping scripts and utilities to collect data from
  Grailed.
- **airflow/**: (To be added) Will contain the ETL pipeline scripts and configurations
  for Apache Airflow.
- **streamlit_app/**: (To be developed) A Streamlit application to showcase the project
  and its predictions.
- **fastapi_app/**: (To be developed) A FastAPI application for deploying the model as a
  service.
- **tests/**: Contains unit tests for various project components.

## Getting Started

### Prerequisites

- **Python 3.11**: Ensure you have Python 3.11 installed.
- **Poetry**: The project uses Poetry for dependency management. If you haven't
  installed Poetry, you can do so by
- following the
  [Poetry installation guide](https://python-poetry.org/docs/#installation).

### Installation

To set up the project, follow these steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/graildient-descent.git
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

### Overview

The `GrailedScraper` is a Python class designed to scrape sold item listings from
[Grailed](https://www.grailed.com/). It collects details such as item names,
descriptions, details, sold prices, and images, which are then used for further
processing and analysis.

### Configuration

The scraper requires Grailed user credentials. Set these up as needed, typically through
environment variables.

### Example Usage

Here is an example of how to use the `GrailedScraper` in a Python script:

```python
from data_collection.scraper import GrailedScraper

scraper = GrailedScraper(email='grailed_email', password='grailed_password')
listings_data, cover_imgs, errors = scraper.scrape()
```

## Project Status

The project has progressed beyond its initial setup phase. The following components have
been implemented and are under development:

- **Scraper**: The web scraper, `GrailedScraper`, has been implemented to collect data
  from Grailed. It is capable of extracting sold item details such as names,
  descriptions, details, sold prices, and images.
- **Pipeline**: An ETL pipeline using Apache Airflow to process and clean the collected
  data.
- **Machine Learning Models**: Models to predict the sold prices of items based on
  various features.

## Roadmap

- **Completed**: Implement the web scraper for Grailed sold listings.
- **Next Steps**:
  - Set up the Airflow ETL pipeline.
  - Develop and train the machine learning models.
  - Create a Streamlit application for model visualization.
  - Deploy the model using FastAPI for real-time predictions.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if
you have any suggestions or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for
details.
