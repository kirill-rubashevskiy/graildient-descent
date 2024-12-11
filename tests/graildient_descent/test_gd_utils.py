import random
from unittest import mock

import numpy as np
import pandas as pd
import pytest

from graildient_descent.utils import load_data, set_random_seed, unflatten


class TestLoadData:
    """
    Test suite for the load_data function.
    """

    @mock.patch("os.walk")
    @mock.patch("pandas.read_csv")
    def test_load_data_local(self, mock_read_csv, mock_os_walk):
        """
        Test that load_data successfully loads a CSV file from the local data/ directory.
        """
        # Mock the os.walk to return a specific file structure
        mock_os_walk.return_value = [
            ("data/", ["subfolder"], ["test.csv"]),
        ]

        # Mock the pd.read_csv function
        mock_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        mock_read_csv.return_value = mock_df

        # Call the function and assert correct data loading
        result = load_data("test.csv")
        mock_read_csv.assert_called_once_with("data/test.csv")
        pd.testing.assert_frame_equal(result, mock_df)

    @mock.patch("os.walk")
    def test_load_data_local_file_not_found(self, mock_os_walk):
        """
        Test that load_data raises FileNotFoundError when the CSV file is not found locally.
        """
        mock_os_walk.return_value = []
        with pytest.raises(
            FileNotFoundError, match="was not found in the data/ directory"
        ):
            load_data("non_existent.csv")

    def test_load_data_s3(self, s3, create_bucket):
        """
        Test that load_data successfully loads a CSV file from a mocked S3 bucket.
        """
        bucket_name = "my-bucket"

        # Add a fake CSV file to the mock S3 bucket
        csv_data = "col1,col2\n1,3\n2,4"
        s3.put_object(Bucket=bucket_name, Key="test.csv", Body=csv_data)

        # Call the function with S3 loading enabled
        result = load_data("test.csv", from_s3=True, bucket_name=bucket_name)
        expected_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

        # Assert the data was read correctly
        pd.testing.assert_frame_equal(result, expected_df)

    @mock.patch("os.getenv")
    def test_load_data_s3_missing_credentials(self, mock_getenv):
        """
        Test that load_data raises EnvironmentError when S3 credentials are missing.
        """
        mock_getenv.return_value = None
        with pytest.raises(EnvironmentError, match="AWS credentials not found"):
            load_data("test.csv", from_s3=True, bucket_name="my-bucket")

    def test_load_data_s3_file_not_found(self, create_bucket):
        """
        Test that load_data raises FileNotFoundError when the file is not found in a mocked S3 bucket.
        """
        bucket_name = "my-bucket"

        # Do not upload any file, simulating a missing file
        with pytest.raises(FileNotFoundError, match="was not found in the S3 bucket"):
            load_data("non_existent.csv", from_s3=True, bucket_name=bucket_name)

    def test_load_data_s3_missing_bucket(self, aws_credentials):
        """
        Test that load_data raises ValueError when the S3 bucket name is missing.
        """
        with pytest.raises(
            ValueError, match="Bucket name must be provided when using S3."
        ):
            load_data("test.csv", from_s3=True)


def test_set_random_seed():
    """
    Test that set_random_seed sets the same seed for random and numpy random number generation.
    """

    # Set the seed and generate numbers with the random module
    set_random_seed(42)
    random_numbers_python_1 = [random.random() for _ in range(5)]
    random_numbers_numpy_1 = np.random.rand(5)

    # Set the seed again and regenerate the numbers
    set_random_seed(42)
    random_numbers_python_2 = [random.random() for _ in range(5)]
    random_numbers_numpy_2 = np.random.rand(5)

    # Check that the numbers are the same when the seed is set to the same value
    assert (
        random_numbers_python_1 == random_numbers_python_2
    ), "Random module numbers are not reproducible"
    np.testing.assert_array_equal(
        random_numbers_numpy_1,
        random_numbers_numpy_2,
        "NumPy random numbers are not reproducible",
    )


class TestUnflatten:
    """
    Test suite for the unflatten function.
    """

    def test_unflatten_simple(self):
        """
        Test a simple flat dictionary with no nested keys.
        """
        flat_dict = {"a": 1, "b": 2}
        expected_output = {"a": 1, "b": 2}
        assert unflatten(flat_dict) == expected_output

    def test_unflatten_nested_single_level(self):
        """
        Test a flat dictionary with one level of nested keys.
        """
        flat_dict = {
            "a.b": 1,
            "a.c": 2,
        }
        expected_output = {"a": {"b": 1, "c": 2}}
        assert unflatten(flat_dict) == expected_output

    def test_unflatten_nested_multi_level(self):
        """
        Test a flat dictionary with multiple levels of nested keys.
        """
        flat_dict = {"a.b.c": 1, "a.b.d": 2, "a.e": 3, "f": 4}
        expected_output = {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4}
        assert unflatten(flat_dict) == expected_output

    def test_unflatten_with_empty_dict(self):
        """
        Test the case where the input is an empty dictionary.
        """
        flat_dict = {}
        expected_output = {}
        assert unflatten(flat_dict) == expected_output

    def test_unflatten_with_mixed_nesting(self):
        """
        Test a flat dictionary with a mix of nested and non-nested keys.
        """
        flat_dict = {"a": 1, "b.c.d": 2, "b.c.e": 3}
        expected_output = {"a": 1, "b": {"c": {"d": 2, "e": 3}}}
        assert unflatten(flat_dict) == expected_output

    def test_unflatten_with_merge_conflict(self):
        """
        Test that the function handles merging when different branches
        of the dictionary contain the same prefix.
        """
        flat_dict = {
            "user.name.first": "John",
            "user.name.last": "Doe",
            "user.age": 30,
            "user.address.city": "New York",
            "user.address.zip": "10001",
        }
        expected_output = {
            "user": {
                "name": {"first": "John", "last": "Doe"},
                "age": 30,
                "address": {"city": "New York", "zip": "10001"},
            }
        }
        assert unflatten(flat_dict) == expected_output

    def test_unflatten_with_single_key(self):
        """
        Test a flat dictionary with only one key-value pair.
        """
        flat_dict = {"a.b.c": 42}
        expected_output = {"a": {"b": {"c": 42}}}
        assert unflatten(flat_dict) == expected_output
