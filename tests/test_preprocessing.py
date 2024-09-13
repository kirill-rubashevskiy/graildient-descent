from unittest import mock

import numpy as np
import pandas as pd
import pytest
from category_encoders import (
    CatBoostEncoder,
    OneHotEncoder,
    OrdinalEncoder,
    TargetEncoder,
)
from sklearn.utils.validation import check_is_fitted

from graildient_descent.preprocessing import (
    FeatureTransformer,
    SizeTransformer,
    TextPreprocessor,
    preprocess_text,
)


class TestPreprocessText:

    @pytest.mark.parametrize(
        "text, expected_output",
        [
            (
                "The quick brown fox jumps over the lazy dog.",
                "quick brown fox jump lazy dog",
            ),  # General case
            ("", "missing"),  # Empty string
            (None, "missing"),  # None input
            (
                "a123 4567 !@#$%",
                "missing",
            ),  # Non-alphabetical characters should be removed
            (
                "Running faster than the wind",
                "running faster wind",
            ),  # Lemmatization and stop words removal
        ],
    )
    def test_preprocess_text(self, text, expected_output):
        """
        Test the preprocess_text function to ensure it handles various inputs correctly.
        """
        assert preprocess_text(text) == expected_output

    def test_preprocess_text_custom_placeholder(self):
        """
        Test that preprocess_text returns a custom placeholder when input is empty or non-string.
        """
        assert preprocess_text("", placeholder="no_data") == "no_data"
        assert preprocess_text(None, placeholder="no_data") == "no_data"


class TestTextPreprocessor:
    def test_text_preprocessor_initialization(self):
        """
        Test that the TextPreprocessor initializes with the correct placeholder.
        """
        preprocessor = TextPreprocessor(placeholder="no_data")
        assert (
            preprocessor.placeholder == "no_data"
        ), "Placeholder was not set correctly"

    def test_text_preprocessor_transform(self):
        """
        Test that the TextPreprocessor applies preprocess_text correctly during transformation.
        """
        preprocessor = TextPreprocessor(placeholder="no_data")
        sample_data = pd.DataFrame(
            {"text": ["The quick brown fox.", "", None, "Over the lazy dog!"]}
        )

        # Mock the preprocess_text function to isolate this test
        with mock.patch(
            "graildient_descent.preprocessing.preprocess_text",
            side_effect=lambda x, p: f"processed_{x}" if x else p,
        ):
            transformed = preprocessor.transform(sample_data)

        expected = pd.DataFrame(
            {
                "text": [
                    "processed_The quick brown fox.",
                    "no_data",
                    "no_data",
                    "processed_Over the lazy dog!",
                ]
            }
        )

        assert transformed.equals(expected), "Transformation was not successful"

    def test_text_preprocessor_feature_names_out(self):
        """
        Test that the TextPreprocessor returns the correct column names after fitting.
        """
        preprocessor = TextPreprocessor()
        sample_data = pd.DataFrame(
            {"text": ["The quick brown fox.", "", None, "Over the lazy dog!"]}
        )

        preprocessor.fit(sample_data)
        feature_names = preprocessor.get_feature_names_out()

        assert feature_names.equals(
            sample_data.columns
        ), "Feature names out were not returned correctly"


class TestSizeTransformer:
    def test_size_transformer_normalize_size(self, sample_data):
        """
        Test that SizeTransformer correctly normalizes the size feature.
        """
        transformer = SizeTransformer(normalize_size=True)
        transformed = transformer.transform(sample_data)

        assert all(transformed >= 0) & all(transformed <= 1)

    def test_size_transformer_feature_names_out(self, sample_data):
        """
        Test that the SizeTransformer returns the correct column names after fitting.
        """
        transformer = SizeTransformer()
        transformer.fit(sample_data)
        feature_names = transformer.get_feature_names_out()

        assert feature_names == [
            "size"
        ], "Feature names out were not returned correctly"


class TestFeatureTransformer:
    """
    Test suite for the FeatureTransformer class.
    """

    @pytest.fixture
    def feature_transformer(self) -> FeatureTransformer:
        """
        Fixture for initializing the FeatureTransformer with default settings.
        """
        return FeatureTransformer()

    @pytest.fixture
    def feature_transformer_params(self) -> dict:
        """
        Parameters fixture for initializing the FeatureTransformer with custom settings.
        """
        return {
            "numeric_cols": ["n_photos"],
            "ohe_cols": ["color"],
            "oe_cols": ["condition"],
            "scaler_params": {"with_mean": False},
            "ohe_params": {"handle_unknown": "ignore"},
            "oe_params": {"handle_unknown": "ignore"},
        }

    def test_feature_transformer_catboost_cols(self):
        """
        Test that FeatureTransformer correctly includes CatBoostEncoder when catboost columns are specified.
        """
        feature_transformer = FeatureTransformer(catboost_cols=["designer"])
        steps, _, _ = zip(*feature_transformer.transformer.transformers)

        assert "catboostencoder" in steps

    def test_feature_transformer_fit(
        self,
        feature_transformer: FeatureTransformer,
        sample_data: pd.DataFrame,
        sample_targets: pd.Series,
    ):
        """
        Test that the FeatureTransformer correctly fits the transformer pipeline.
        """
        feature_transformer.fit(sample_data, sample_targets)

        # Check if the transformer is fitted
        check_is_fitted(feature_transformer.transformer)

    def test_feature_transformer_transform(
        self,
        feature_transformer: FeatureTransformer,
        sample_data: pd.DataFrame,
        sample_targets: pd.Series,
    ):
        """
        Test that the FeatureTransformer correctly transforms the input data.
        """
        feature_transformer.fit(sample_data, sample_targets)
        transformed = feature_transformer.transform(sample_data)

        # Calculate expected number of output columns
        expected_num_columns = (
            1 + 7 + 1 + 4
        )  # 1 numeric + 7 one-hot encoded + 1 ordinal encoded + 4 target encoded
        assert isinstance(transformed, np.ndarray)
        assert transformed.shape == (sample_data.shape[0], expected_num_columns)

    def test_feature_transformer_get_params(
        self, feature_transformer: FeatureTransformer
    ):
        """
        Test that the get_params method returns the correct parameters.
        """
        assert feature_transformer.get_params()["numeric_cols"] == ["n_photos"]

    def test_feature_transformer_get_params_no_encoding(self):
        """
        Test that the get_params method returns correct parameters for no encoding case.
        """
        feature_transformer = FeatureTransformer(no_encoding=True)
        params = feature_transformer.get_params()

        assert "no_encoding" in params
        assert len(params["transformers"]) == 2

    def test_feature_transformer_set_params(
        self, feature_transformer: FeatureTransformer, feature_transformer_params: dict
    ):
        """
        Test that the set_params method correctly updates the transformer's configuration.
        """
        feature_transformer.set_params(**feature_transformer_params)
        assert (
            feature_transformer.get_params()["numeric_cols"]
            == feature_transformer_params["numeric_cols"]
        )
        assert (
            feature_transformer.get_params()["ohe_cols"]
            == feature_transformer_params["ohe_cols"]
        )
        assert (
            feature_transformer.get_params()["oe_cols"]
            == feature_transformer_params["oe_cols"]
        )
        assert (
            feature_transformer.get_params()["scaler_params"]
            == feature_transformer_params["scaler_params"]
        )
        assert (
            feature_transformer.get_params()["ohe_params"]
            == feature_transformer_params["ohe_params"]
        )
        assert (
            feature_transformer.get_params()["oe_params"]
            == feature_transformer_params["oe_params"]
        )

    @pytest.mark.parametrize(
        "encoding_type, encoder_class",
        [
            ("ohe_cols", OneHotEncoder),
            ("oe_cols", OrdinalEncoder),
            ("catboost_cols", CatBoostEncoder),
            ("te_cols", TargetEncoder),
        ],
    )
    def test_feature_transformer_size_encoders(self, encoding_type, encoder_class):
        """
        Test that FeatureTransformer assigns the correct encoder for the 'size' column.
        """
        transformer = FeatureTransformer(**{encoding_type: ["size"]})
        assert isinstance(transformer.size_encoder, encoder_class)

    def test_feature_transformer_feature_names_out(self, sample_data, sample_targets):
        """
        Test that FeatureTransformer returns correct feature names after fitting.
        """
        text_cols = ["item_name", "description", "hashtags"]
        feature_transformer = FeatureTransformer(oe_cols=[], ohe_cols=[])
        feature_transformer.fit(sample_data, sample_targets)
        assert set(feature_transformer.get_feature_names_out()) == set(
            sample_data.columns
        ) - set(text_cols)
