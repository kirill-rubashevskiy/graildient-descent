import numpy as np
import pandas as pd
import pytest
from sklearn.utils.validation import check_is_fitted

from graildient_descent.feature_extraction import TextFeatureExtractor


@pytest.fixture
def sample_data():
    """Create sample text data for testing."""
    return pd.DataFrame(
        {
            "item_name": [
                "Test Item 1",
                "Test Item 2",
                "Test Item 3",
                "Test Item 4",
                "Test Item 5",
            ],
            "description": [
                "Sample description 1",
                "Sample description 2",
                "Sample description 3",
                "Sample description 4",
                "Sample description 5",
            ],
            "hashtags": [
                "tag1 tag2",
                "tag3 tag4",
                "tag5 tag6",
                "tag7 tag8",
                "tag9 tag10",
            ],
        }
    )


class TestTextFeatureExtractor:
    """Test suite for the TextFeatureExtractor class."""

    @pytest.fixture
    def extractor(self) -> TextFeatureExtractor:
        return TextFeatureExtractor(reducer_params={"n_components": 2})

    # @pytest.fixture
    # def params(self):
    #     """
    #     Parameters fixture for initializing the TextFeatureExtractor with custom settings.
    #     """
    #     return {
    #         "text_cols": ["item_name", "description"],
    #         "pca_params": {
    #             "n_components": 2,
    #         },
    #         "vectorizer_params": {
    #             "lowercase": False,
    #         },
    #     }

    def test_fit(self, extractor, sample_data):
        """
        Test that the TextFeatureExtractor correctly fits the transformer pipeline.
        """
        extractor.fit(sample_data)

        # Check if the transformer is fitted
        check_is_fitted(extractor.transformer)

    def test_transform(self, extractor, sample_data):
        """
        Test that the TextFeatureExtractor correctly transforms the input data.
        """
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)

        # Calculate expected number of output columns
        # (3 stats + 2 PCA components per text column + sentiment + is_hashtags_missing)
        expected_num_columns = len(extractor.get_params()["text_cols"]) * 5 + 2

        assert isinstance(transformed, np.ndarray)
        assert transformed.shape == (sample_data.shape[0], expected_num_columns)

    @pytest.mark.parametrize("vectorizer_class", ["count", "tfidf"])
    def test_valid_vectorizers(self, extractor, vectorizer_class, sample_data):
        """Test valid vectorizer configurations."""
        extractor.set_params(vectorizer_class=vectorizer_class)
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)
        assert transformed.shape[0] == sample_data.shape[0]

    def test_invalid_vectorizer_raises_error(self):
        """
        Test that an invalid vectorizer class raises a ValueError.
        """
        with pytest.raises(ValueError, match=("Vectorizer 'invalid' is not supported")):
            TextFeatureExtractor(vectorizer_class="invalid")

    @pytest.mark.parametrize("reducer_class", ["pca", "umap"])
    def test_valid_reducers(self, extractor, reducer_class, sample_data):
        """Test valid dimensionality reduction configurations."""
        extractor.set_params(reducer_class=reducer_class)
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)
        assert transformed.shape[0] == sample_data.shape[0]

    def test_invalid_reducer_raises_error(self):
        """Test that an invalid reducer class raises a ValueError."""
        with pytest.raises(ValueError, match="Reducer 'invalid' is not supported"):
            TextFeatureExtractor(reducer_class="invalid")

    def test_get_params(self, extractor):
        """Test that the get_params method returns the correct parameters."""
        params = extractor.get_params()
        expected_params = {
            "text_cols",
            "use_stats",
            "use_embeddings",
            "use_sentiment",
            "use_missing_hashtags",
            "vectorizer_class",
            "vectorizer_params",
            "reducer_class",
            "reducer_params",
        }
        assert all(param in params for param in expected_params)

    def test_set_params(self, extractor):
        """
        Test that the set_params method correctly updates the extractor's configuration.
        """
        new_params = {
            "reducer_params": {"n_components": 10},
            "vectorizer_params": {"max_features": 1000},
        }
        extractor.set_params(**new_params)
        current_params = extractor.get_params()
        assert current_params["reducer_params"]["n_components"] == 10
        assert current_params["vectorizer_params"]["max_features"] == 1000

    def test_stats_only(self, sample_data):
        extractor = TextFeatureExtractor(
            use_embeddings=False, use_sentiment=False, use_missing_hashtags=False
        )
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)
        # 3 stats per text column
        assert transformed.shape == (sample_data.shape[0], len(extractor.text_cols) * 3)

    def test_embeddings_only(self, extractor, sample_data):
        """Test extractor with only embeddings enabled."""
        extractor.set_params(
            use_stats=False,
            use_sentiment=False,
            use_missing_hashtags=False,
        )
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)
        # 2 components per text column
        assert transformed.shape[1] == len(extractor.text_cols) * 2

    def test_sentiment_feature_only(self, sample_data):
        """Test extractor with only sentiment analysis feature."""
        extractor = TextFeatureExtractor(
            use_stats=False,
            use_embeddings=False,
            use_missing_hashtags=False,
            use_sentiment=True,
        )
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)
        assert transformed.shape[1] == 1  # Only sentiment score

    def test_missing_hashtags_feature_only(self, sample_data):
        """Test extractor with only missing hashtags feature."""
        extractor = TextFeatureExtractor(
            use_stats=False,
            use_embeddings=False,
            use_sentiment=False,
            use_missing_hashtags=True,
        )
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)
        assert transformed.shape[1] == 1  # Only missing hashtags indicator

    @pytest.mark.parametrize(
        "text_cols",
        [
            ["item_name"],
            ["description"],
            ["hashtags"],
            ["item_name", "description"],
            ["item_name", "description", "hashtags"],
        ],
    )
    def test_different_text_columns(self, extractor, text_cols, sample_data):
        """Test extractor with different combinations of text columns."""
        extractor.set_params(
            text_cols=text_cols, use_sentiment=False, use_missing_hashtags=False
        )
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)
        # 5 features per text column (3 stats + 2 components)
        assert transformed.shape[1] == len(text_cols) * 5
