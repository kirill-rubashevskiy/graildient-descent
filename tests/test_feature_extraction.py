import pandas as pd
import pytest
from sklearn.utils.validation import check_is_fitted

from graildient_descent.feature_extraction import TextFeatureExtractor


class TestTextFeatureExtractor:
    """
    Test suite for the TextFeatureExtractor class.
    """

    @pytest.fixture
    def extractor(self) -> TextFeatureExtractor:
        return TextFeatureExtractor(
            item_name_pca_n_components=2,
            description_pca_n_components=2,
            hashtags_pca_n_components=2,
        )

    @pytest.fixture
    def params(self):
        """
        Parameters fixture for initializing the TextFeatureExtractor with custom settings.
        """
        return {
            "text_cols": ["item_name", "description"],
            "pca_params": {
                "n_components": 2,
            },
            "vectorizer_params": {
                "lowercase": False,
            },
        }

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

        # Calculate expected number of output columns (5 stats + 2 PCA components per text column)
        expected_num_columns = len(extractor.get_params()["text_cols"]) * 5

        assert isinstance(transformed, pd.DataFrame)
        assert transformed.shape == (sample_data.shape[0], expected_num_columns)

    def test_invalid_vectorizer_raises_error(self):
        """
        Test that an invalid vectorizer class raises a ValueError.
        """
        with pytest.raises(
            ValueError, match=("Vectorizer 'invalid_vectorizer' is not supported. ")
        ):
            TextFeatureExtractor(item_name_vectorizer_class="invalid_vectorizer")

    def test_get_params(self, extractor):
        """
        Test that the get_params method returns the correct parameters.
        """
        params = extractor.get_params()

        assert "item_name_vectorizer_class" in params
        assert "transformers" in params

    def test_set_params(self, extractor):
        """
        Test that the set_params method correctly updates the extractor's configuration.
        """
        item_name_pca_n_components = 20
        extractor.set_params(item_name_pca_n_components=item_name_pca_n_components)
        assert (
            extractor.get_params()["item_name_pca_n_components"]
            == item_name_pca_n_components
        )

    def test_ngram_range_as_list(self):
        extractor = TextFeatureExtractor(
            item_name_vectorizer_params={"ngram_range": [1, 1], "max_features": 5000}
        )
        params = extractor.get_params()

        assert params["item_name_vectorizer_params"]["ngram_range"] == (1, 1)

    def test_embeddings_as_list(self, extractor, sample_data):
        extractor.set_params(use_stats=False, return_embeddings_as_list=True)
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)
        assert transformed.shape == (sample_data.shape[0], len(extractor.text_cols))

    def test_stats_only(self, sample_data):
        extractor = TextFeatureExtractor(use_embeddings=False)
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)

        assert transformed.shape == (sample_data.shape[0], len(extractor.text_cols) * 3)

    @pytest.mark.parametrize(
        "text_cols",
        [["item_name"], ["description"], ["hashtags"], ["item_name", "description"]],
    )
    def test_text_cols(self, text_cols, extractor, sample_data):
        extractor.set_params(text_cols=text_cols)
        extractor.fit(sample_data)
        transformed = extractor.transform(sample_data)

        # Calculate expected number of output columns (3 stats + 2 PCA components per text column)
        expected_num_columns = len(extractor.get_params()["text_cols"]) * 5

        assert isinstance(transformed, pd.DataFrame)
        assert transformed.shape == (sample_data.shape[0], expected_num_columns)
