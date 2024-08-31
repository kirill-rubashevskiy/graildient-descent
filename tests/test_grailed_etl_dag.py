import os
from unittest import mock

import pandas as pd
import pytest
from airflow.models import DagBag


@pytest.fixture
def dagbag():
    """
    Fixture that loads the DAGs from the DagBag.
    """
    return DagBag()


def test_dag_loaded(dagbag):
    """
    Test if the DAG is loaded properly.
    """
    dag = dagbag.get_dag(dag_id="grailed_etl")
    assert dagbag.import_errors == {}
    assert dag is not None
    assert len(dag.tasks) > 0


def test_task_dependencies(dagbag):
    """
    Test task dependencies for the DAG.
    """
    dag = dagbag.get_dag(dag_id="grailed_etl")

    # Check if all tasks are present
    expected_tasks = {"scrape_data", "transform_data", "upload_to_s3"}
    assert expected_tasks.issubset(set(dag.task_ids))

    # Check the task sequence
    assert dag.get_task("transform_data").upstream_task_ids == {"scrape_data"}
    assert dag.get_task("upload_to_s3").upstream_task_ids == {"transform_data"}


@mock.patch("tempfile.mkdtemp")
@mock.patch("scraper.GrailedScraper.scrape")
def test_scrape_data_task(mock_scrape, mock_mkdtemp, dagbag, tmpdir):
    """
    Test the scrape_data task using pytest's temporary directory by patching tempfile.mkdtemp.
    """
    # Mock the return value of the scraper
    mock_scrape.return_value = ([{"id": "test1"}], [b"image_bytes"], [])

    # Mock tempfile.mkdtemp to return pytest's tmpdir path
    mock_mkdtemp.return_value = str(tmpdir)

    # Load the DAG and get the task
    dag = dagbag.get_dag(dag_id="grailed_etl")
    scrape_data_task = dag.get_task("scrape_data")

    # Run the task
    scrape_data_task.python_callable()

    # Ensure the scraper was called
    mock_scrape.assert_called_once()

    # Check that the files were created in the tmpdir
    listings_data_path = tmpdir.join("listings_data.json")
    assert listings_data_path.check(file=1)  # Ensure the file exists

    image_path = tmpdir.join("test1.webp")
    assert image_path.check(file=1)  # Ensure the image file exists


@mock.patch("utils.extract_size")
@mock.patch("pandas.read_json")
def test_transform_data(mock_read_json, mock_extract_size, dagbag, tmpdir):
    """
    Test the transform_data task when it succeeds.
    """
    # Mock the return values of pandas read_json and pandas Series apply
    mock_read_json.return_value = pd.DataFrame(
        {"id": ["test1"], "size": ["large"], "hashtags": [None]}
    )

    mock_extract_size.return_value = "L"

    # Mock scraped data input
    scraped_data = {
        "temp_dir": tmpdir,
        "listings_data_path": os.path.join(tmpdir, "listings_data.json"),
        "errors": [],
        "image_paths": os.path.join(tmpdir, "test1.webp"),
    }

    # Load the DAG and get the task
    dag = dagbag.get_dag(dag_id="grailed_etl")
    transform_data_task = dag.get_task("transform_data")

    # Run the task
    result = transform_data_task.python_callable(scraped_data=scraped_data)

    # Ensure the data transformation logic was called
    mock_read_json.assert_called_once_with(scraped_data["listings_data_path"])
    mock_extract_size.assert_called()

    # Check the output
    assert result["temp_dir"] == scraped_data["temp_dir"]
    assert result["transformed_listings_data_path"].endswith(
        "transformed_listings_data.json"
    )
    assert result["errors"] == scraped_data["errors"]
    assert result["image_paths"] == scraped_data["image_paths"]

    # Ensure the transformed data file exists
    transformed_listings_data_path = tmpdir.join("transformed_listings_data.json")
    assert transformed_listings_data_path.check(file=1)
