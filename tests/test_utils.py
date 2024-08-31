import pytest

from data_collection.utils import extract_size


@pytest.mark.parametrize(
    "description, expected",
    [
        ("Women's / ONE SIZE", "ONE SIZE"),  # Test for exact match with 'ONE SIZE'
        ("Women's / XXS / US 00 / IT 34", "XXS"),  # Test for alphanumeric size
        ("Women's / 3XL / US 20-22", "3XL"),  # Test for alphanumeric size 3XL
        ("Men's / US 28 / EU 44", "28"),  # Test for numeric size
        ("Men's / US 10.5 / EU 43-44", "10.5"),  # Test for decimal size
        ("Men's / 52S", "52S"),  # Test for numeric size with suffix 'S'
        ("Men's / 36R", "36R"),  # Test for numeric size with suffix 'R'
        ("Men's / 44L", "44L"),  # Test for numeric size with suffix 'L'
        ("Random Text", "Random Text"),  # Test with no matching size pattern
    ],
)
def test_extract_size(description, expected):
    """
    Tests various size extraction scenarios from descriptive text using the extract_size function.
    """
    assert extract_size(description) == expected
