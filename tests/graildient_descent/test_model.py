import os
import tempfile
from io import BytesIO
from unittest import mock

import joblib
import pandas as pd
import pytest
from sklearn.utils.validation import check_is_fitted

from graildient_descent.model import Model


class TestModel:
    """
    Test suite for the Model class, including initialization, fitting, saving, loading,
    and error handling tests.
    """

    @pytest.fixture
    def model(self) -> Model:
        """
        Fixture for initializing the Model with default settings.
        """
        return Model(model_name="test_model")

    # ----- Model Initialization and Configuration Tests -----

    def test_model_initialization(self, model: Model):
        """
        Test that the model initializes correctly with default settings.
        """
        assert isinstance(model, Model)
        assert model.estimator_class == "lr"
        assert model.use_tab_features is True
        assert model.use_text_features is False

    def test_invalid_estimator_raises_error(self):
        """
        Test that an unsupported estimator raises a ValueError during model initialization.
        """
        with pytest.raises(
            ValueError, match="Estimator 'invalid_estimator' is not supported"
        ):
            Model(model_name="invalid_model", estimator_class="invalid_estimator")

    # ----- Model Fitting and Prediction Tests -----

    def test_fit(
        self, model: Model, sample_data: pd.DataFrame, sample_targets: pd.Series
    ):
        """
        Test that the model correctly fits the pipeline without errors.
        """
        model.fit(sample_data, sample_targets)
        check_is_fitted(model.pipeline)

    def test_predict_positive_values(
        self, model: Model, sample_data: pd.DataFrame, sample_targets: pd.Series
    ):
        """
        Test that the predict method returns non-negative values only after fitting.
        """
        model.fit(sample_data, sample_targets)
        predictions = model.predict(sample_data)
        assert all(predictions >= 0), "Predictions should be non-negative."

    def test_evaluate_method(
        self, model: Model, sample_data: pd.DataFrame, sample_targets: pd.Series
    ):
        """
        Test that the evaluate method returns expected metrics (RMSLE and WAPE).
        """
        model.fit(sample_data, sample_targets)
        metrics = model.evaluate(sample_data, sample_targets)
        assert "rmsle" in metrics and "wape" in metrics
        assert metrics["rmsle"] >= 0, "RMSLE should be non-negative."
        assert metrics["wape"] >= 0, "WAPE should be non-negative."

    # ----- Model Saving and Loading Tests -----

    def test_save_and_load_model(
        self, model: Model, sample_data: pd.DataFrame, sample_targets: pd.Series
    ):
        """
        Test that the model is saved and loaded correctly from a local path.
        """
        model.fit(sample_data, sample_targets)
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "test_model.pkl")
            model.save_model(tmpdir)
            loaded_model, _ = Model.load_model(model_path)
            assert isinstance(loaded_model, Model)
            assert (
                loaded_model.predict(sample_data).all()
                == model.predict(sample_data).all()
            ), "Predictions should match after loading."

    def test_load_model_local_file_not_found(self):
        """
        Test that load_model raises FileNotFoundError when the file is not found locally.
        """
        with pytest.raises(
            FileNotFoundError, match="was not found in the local directory"
        ):
            Model.load_model("non_existent.pkl")

    def test_load_model_s3(self, model, s3, create_bucket):
        """
        Test that the model is loaded correctly from S3.
        """
        bucket_name = "my-bucket"
        buffer = BytesIO()
        joblib.dump(model, buffer)
        buffer.seek(0)
        s3.put_object(Bucket=bucket_name, Key="model.pkl", Body=buffer)
        loaded_model = Model.load_model(
            path="model.pkl", from_s3=True, bucket_name=bucket_name
        )

        assert model.model_name == loaded_model.model_name

    def test_load_model_s3_file_not_found(self, create_bucket):
        """
        Test that load_model raises FileNotFoundError when the file is not found in S3.
        """
        bucket_name = "my-bucket"
        with pytest.raises(FileNotFoundError, match="was not found in the S3 bucket"):
            Model.load_model("non_existent.pkl", from_s3=True, bucket_name=bucket_name)

    def test_load_model_s3_missing_bucket(self, aws_credentials):
        """
        Test that load_model raises ValueError when the S3 bucket name is missing.
        """
        with pytest.raises(
            ValueError, match="Bucket name must be provided when using S3."
        ):
            Model.load_model("test.csv", from_s3=True)

    @mock.patch("os.getenv")
    def test_load_model_s3_missing_credentials(self, mock_getenv):
        """
        Test that load_model raises EnvironmentError when S3 credentials are missing.
        """
        mock_getenv.return_value = None
        with pytest.raises(EnvironmentError, match="AWS credentials not found"):
            Model.load_model(path="model.pkl", from_s3=True, bucket_name="my-bucket")

    # ----- Model Parameter Handling Tests -----

    @pytest.mark.parametrize(
        "estimator_class, estimator_param",
        [("lr", "fit_intercept"), ("rforest", "n_estimators")],
    )
    def test_get_params_deep(self, estimator_class, estimator_param):
        """
        Test that the get_params method returns the correct parameters for different estimators.
        """
        model = Model(model_name="test_model", estimator_class=estimator_class)
        params = model.get_params()

        assert "model_name" in params
        assert "estimator_class" in params
        assert "use_tab_features" in params
        assert "use_text_features" in params
        assert "transformer_weights" in params
        assert estimator_param in params

    def test_get_params_shallow(self, model: Model):
        """
        Test that the get_params method returns only shallow parameters.
        """
        params = model.get_params(deep=False)
        assert "model_name" in params
        assert "estimator_class" in params
        assert "use_tab_features" in params
        assert "use_text_features" in params

    def test_set_params_updates_pipeline(self):
        """
        Test that dynamically updating model parameters with set_params works as expected.
        """
        model = Model(model_name="test_model", estimator_class="rforest")
        model.set_params(estimator_params={"n_estimators": 50})
        assert (
            model.pipeline.named_steps["estimator"].get_params()["n_estimators"] == 50
        )

    # ----- Model Handling of Tabular and Text Features -----

    def test_model_with_both_tab_and_text_features(
        self, sample_data: pd.DataFrame, sample_targets: pd.Series
    ):
        """
        Test that the model works correctly when both tabular and text features are enabled.
        """
        model = Model(
            model_name="tab_and_text_model",
            estimator_class="rforest",
            use_tab_features=True,
            use_text_features=True,
            transformer_params={"numeric_cols": ["n_photos"], "ohe_cols": ["color"]},
            extractor_params={
                "text_cols": ["description"],
                "reducer_params": {"n_components": 2},
            },
        )
        model.fit(sample_data, sample_targets)
        check_is_fitted(model.pipeline)
        predictions = model.predict(sample_data)
        assert all(predictions >= 0), "Predictions should be non-negative."

    def test_model_with_only_text_features(
        self, sample_data: pd.DataFrame, sample_targets: pd.Series
    ):
        """
        Test that the model works correctly when only text features are enabled.
        """
        model = Model(
            model_name="text_only_model",
            use_tab_features=False,
            use_text_features=True,
            extractor_params={
                "text_cols": ["description"],
                "reducer_params": {"n_components": 2},
            },
        )
        model.fit(sample_data, sample_targets)
        check_is_fitted(model.pipeline)

    def test_no_features_enabled_raises_error(self):
        """
        Test that a ValueError is raised if neither tabular nor text features are enabled.
        """
        with pytest.raises(
            ValueError,
            match="At least one of 'use_tab_features' or 'use_text_features' must be True",
        ):
            Model(
                model_name="no_features_model",
                use_tab_features=False,
                use_text_features=False,
            )
