import os
from io import BytesIO

import boto3
import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import (
    ElasticNet,
    HuberRegressor,
    Lasso,
    LinearRegression,
    Ridge,
)
from sklearn.metrics import mean_absolute_percentage_error, root_mean_squared_log_error
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.tree import DecisionTreeRegressor

from graildient_descent.feature_extraction import TextFeatureExtractor
from graildient_descent.preprocessing import FeatureTransformer


MAX_ITER = 20000
RANDOM_STATE = 42

estimators = {
    "c-median": (DummyRegressor, dict(strategy="median")),
    "lr": (LinearRegression, {}),
    "ridge": (Ridge, dict(random_state=RANDOM_STATE, max_iter=MAX_ITER)),
    "lasso": (Lasso, dict(random_state=RANDOM_STATE, max_iter=MAX_ITER)),
    "enet": (ElasticNet, dict(random_state=RANDOM_STATE, max_iter=MAX_ITER)),
    "huber": (HuberRegressor, dict(max_iter=MAX_ITER)),
    "dtree": (DecisionTreeRegressor, dict(random_state=RANDOM_STATE)),
    "rforest": (RandomForestRegressor, dict(random_state=RANDOM_STATE)),
    "xtrees": (ExtraTreesRegressor, dict(random_state=RANDOM_STATE)),
    "gboost": (GradientBoostingRegressor, dict(random_state=RANDOM_STATE)),
    "catboost": (CatBoostRegressor, dict(random_state=RANDOM_STATE, verbose=0)),
    "knn": (KNeighborsRegressor, {}),
}


class Model(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        model_name: str,
        estimator_class: str = "lr",
        use_tab_features: bool = True,
        use_text_features: bool = False,
        estimator_params: dict = None,
        transformer_params: dict = None,
        extractor_params: dict = None,
    ):
        """
        Initialize the Model class with a specific model and its hyperparameters.

        Parameters:
            model_name: The name of the model to initialize (used for saving/loading).
            estimator_class: The key representing the estimator class (e.g., 'rf' for RandomForestRegressor).
            use_tab_features: Whether to include tabular feature preprocessing.
            use_text_features: Whether to include text feature extraction.
            estimator_params: Optional dictionary of hyperparameters to configure the estimator.
            transformer_params: Optional dictionary of hyperparameters to configure the tabular transformer.
            extractor_params: Optional dictionary of hyperparameters to configure the text feature extractor.
        """
        self.model_name = model_name
        self.estimator_class = estimator_class
        self.use_tab_features = use_tab_features
        self.use_text_features = use_text_features
        self.estimator_params = estimator_params or {}
        self.transformer_params = transformer_params or {}
        self.extractor_params = extractor_params or {}
        self.transformer = None
        self.extractor = None
        self.estimator = None
        self.pipeline = self._initialize_pipeline()

    @classmethod
    def load_model(cls, path: str, from_s3: bool = False, bucket_name: str = None):
        """
        Load a model and its associated metrics from the specified path or S3 bucket.

        Parameters:
            path: The file path or S3 path from where to load the model.
            from_s3: Whether to load the model from an S3 bucket.
            bucket_name: The name of the S3 bucket (required if from_s3 is True).

        Returns:
            tuple: (Model instance, metrics dictionary)
        """
        if from_s3:
            # Fetch AWS S3 credentials from environment variables
            AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
            AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
            AWS_REGION = os.getenv("AWS_REGION", "ru-central1")  # Default region
            AWS_ENDPOINT_URL = os.getenv(
                "AWS_ENDPOINT_URL", "https://storage.yandexcloud.net"
            )

            if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
                raise EnvironmentError(
                    "AWS Cloud credentials not found in environment variables."
                )

            if not bucket_name:
                raise ValueError("Bucket name must be provided when using S3.")

            # Load model from S3 bucket
            s3 = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION,
                endpoint_url=AWS_ENDPOINT_URL,
            )
            try:
                response = s3.get_object(Bucket=bucket_name, Key=path)
                return joblib.load(BytesIO(response["Body"].read()))
            except s3.exceptions.NoSuchKey:
                raise FileNotFoundError(
                    f"The file {path} was not found in the S3 bucket {bucket_name}."
                )
        else:
            # Load model from local file system
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"The file {path} was not found in the local directory."
                )
            return joblib.load(path)

    def _initialize_pipeline(self) -> Pipeline:
        """
        Initialize the model pipeline based on the selected model and hyperparameters.

        Returns:
            A scikit-learn pipeline object.

        Raises:
            ValueError: If selected estimator class is not supported.
        """
        if self.estimator_class not in estimators.keys():
            raise ValueError(
                f"Estimator '{self.estimator_class}' is not supported. "
                f"Supported estimators are {list(estimators.keys())}"
            )
        estimator_class, estimator_default_params = estimators[self.estimator_class]
        self.estimator = estimator_class(**estimator_default_params)
        self.estimator.set_params(**self.estimator_params)

        if self.use_tab_features:
            self.transformer = FeatureTransformer(**self.transformer_params)
        if self.use_text_features:
            self.extractor = TextFeatureExtractor(**self.extractor_params)

        if not self.use_tab_features and not self.use_text_features:
            raise ValueError(
                "At least one of 'use_tab_features' or 'use_text_features' must be True."
            )

        if self.use_tab_features and self.use_text_features:
            preprocessor = FeatureUnion(
                [("transformer", self.transformer), ("extractor", self.extractor)]
            )
        elif self.use_tab_features:
            preprocessor = self.transformer
        else:
            preprocessor = self.extractor

        return Pipeline([("preprocessor", preprocessor), ("estimator", self.estimator)])

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **params):
        """
        Train the model on the provided training data.

        Parameters:
            X_train: The training features.
            y_train: The training target labels.
        """
        self.pipeline.fit(X_train, y_train, **params)

    def evaluate(self, X_eval: pd.DataFrame, y_eval: pd.Series) -> dict:
        """
        Evaluate the model on the provided evaluation data.

        Parameters:
            X_eval: The evaluation features.
            y_eval: The evaluation target labels.

        Returns:
            A dictionary containing evaluation metrics: RMSLE (3 decimal places) and WAPE (2 decimal places).
        """
        y_pred = self.predict(X_eval)
        rmsle = np.round(root_mean_squared_log_error(y_eval, y_pred), 3)
        wape = np.round(
            mean_absolute_percentage_error(y_eval, y_pred, sample_weight=y_eval), 2
        )
        return {"rmsle": rmsle, "wape": wape}

    def predict(self, X: pd.DataFrame):
        """
        Make predictions on new data.

        Parameters:
            X: The features to predict on.

        Returns:
            The predicted labels after exponential transformation.
        """

        predictions = self.pipeline.predict(X)
        return np.expm1(predictions)

    def save_model(self, path: str, metrics: dict = None) -> None:
        """
        Save the trained model along with its performance metrics as a tuple.

        Saves a tuple containing:
        1. The model instance
        2. A dictionary containing:
            - Model configuration
            - Performance metrics
            - Timestamp and model name

        Parameters:
            path: The file path to save the model.
            metrics: Dictionary containing training set metrics (optional).
        """

        # Create the directory if it doesn't exist
        os.makedirs(path, exist_ok=True)

        # Prepare metrics and configuration data
        metrics_data = {
            "model_name": self.model_name,
            "model_config": {
                "estimator_class": self.estimator_class,
                "use_tab_features": self.use_tab_features,
                "use_text_features": self.use_text_features,
                "estimator_params": self.estimator_params,
                "transformer_params": self.transformer_params,
                "extractor_params": self.extractor_params,
            },
            "metrics": metrics,
            "timestamp": pd.Timestamp.now().isoformat(),
        }

        # Save model and metrics as a tuple
        model_path = os.path.join(path, f"{self.model_name}.pkl")
        joblib.dump((self, metrics_data), model_path)

    def get_params(self, deep: bool = True) -> dict:
        """
        Get the parameters of the Model class and its internal pipeline.

        Parameters:
            deep: Whether to include the parameters of the internal objects (transformer and/or extractor and estimator).

        Returns:
            A dictionary of parameters.
        """
        params = super().get_params(deep)
        if deep:
            params.update(self.pipeline.named_steps["preprocessor"].get_params(deep))
            params.update(self.pipeline.named_steps["estimator"].get_params(deep))
        return params

    def set_params(self, **params):
        """
        Set the parameters for the Model class and its internal pipeline.

        Parameters:
            params: Dictionary of parameters to set.

        Returns:
            The updated Model object.
        """
        for param_group in [
            "model_name",
            "estimator_class",
            "use_tab_features",
            "use_text_features",
            "estimator_params",
            "transformer_params",
            "extractor_params",
        ]:
            if param_group in params:
                setattr(self, param_group, params.pop(param_group))
        super().set_params(**params)
        self.pipeline = (
            self._initialize_pipeline()
        )  # Reinitialize with updated parameters
        return self
