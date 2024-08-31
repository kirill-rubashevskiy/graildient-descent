import re


def extract_size(description: str) -> str:
    """
    Extracts a size pattern from a given string.

    The function searches for common size patterns such as:
    - "ONE SIZE"
    - Alphanumeric sizes like "M", "XL", "42R"
    - Numeric sizes like "42"
    - Decimal sizes like 10.5

    If a size pattern is found, it is returned. Otherwise, the original string is returned.

    Args:
        description (str): The string from which to extract the size.

    Returns:
        str: The extracted size or the original string if no match is found.
    """
    # Define the regex pattern for various size formats
    pattern = (
        r"(ONE SIZE)"  # Matches 'ONE SIZE'
        r"|(\b\d+\.\d+\b)"  # Matches decimal sizes like '10.5'
        r"|\b(?:US\s)?([34SMLX]+(?:-[A-Z]+)?)\b"  # Matches sizes like 'M', 'XL', '3XL'
        r"|(\b\d+[SRL]?\b)"  # Matches numeric sizes like '42', '42R' or '42L'
    )

    # Search for the pattern in the string
    match = re.search(pattern, description)

    # Return the first matched group, or the original string if no match is found
    return (
        match.group(1) or match.group(2) or match.group(3) or match.group(4)
        if match
        else description
    )
