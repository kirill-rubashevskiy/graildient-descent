import nltk
import numpy as np
import pandas as pd
from category_encoders import (
    CatBoostEncoder,
    OneHotEncoder,
    OrdinalEncoder,
    TargetEncoder,
)
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import make_column_transformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


nltk.download("punkt", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("stopwords", quiet=True)


def preprocess_text(text, placeholder="missing"):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    if not isinstance(text, str) or not text.strip():
        return placeholder  # Return placeholder if the input is empty or non-string

    # Tokenize, lemmatize, and remove stop words
    words = word_tokenize(text.lower())
    words = [
        lemmatizer.lemmatize(word)
        for word in words
        if word.isalnum() and word not in stop_words
    ]
    processed_text = " ".join(words)

    return processed_text if processed_text else placeholder  # Ensure non-empty output


class TextPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, placeholder="missing"):
        self.placeholder = placeholder

    def fit(self, X, y=None):
        self.columns_ = X.columns
        return self

    def transform(self, X):
        # Apply the preprocessing function to each text feature
        return X.map(lambda x: preprocess_text(x, self.placeholder))

    def get_feature_names_out(self, *args, **params):
        return self.columns_


class SizeTransformer(BaseEstimator, TransformerMixin):
    """
    Custom transformer to adjust the 'size' feature based on the 'category'.
    For 'accessories', the 'size' is set to 'ONE SIZE'.
    """

    def __init__(self, normalize_size: bool = False):
        self.normalize_size = normalize_size
        self.tops_size_chart = tuple(
            ["XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "ONE SIZE"]
        )
        self.bottoms_size_chart = tuple([str(i) for i in range(22, 45)])
        self.footwear_size_chart = tuple([str(i) for i in range(4, 16)])
        self.tailoring_size_chart = tuple(
            [f"{i}{j}" for i in range(34, 55, 2) for j in ("S", "R", "L")]
        )
        self.size_map = {}
        for size_chart in [
            self.tops_size_chart,
            self.bottoms_size_chart,
            self.footwear_size_chart,
            self.tailoring_size_chart,
        ]:
            category_map = dict(zip(size_chart, np.linspace(0, 1, len(size_chart))))
            self.size_map.update(category_map)

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        # Apply the transformation in-place
        if self.normalize_size:
            X["size"] = X.apply(
                lambda row: str(
                    self.size_map["ONE SIZE"]
                    if row["category"] == "accessories"
                    else self.size_map.get(row["size"])
                ),
                axis=1,
            )
        else:
            X["size"] = X.apply(
                lambda row: (
                    "ONE SIZE" if row["category"] == "accessories" else row["size"]
                ),
                axis=1,
            )

        return X["size"].to_frame()

    def get_feature_names_out(self, *args, **params):
        return ["size"]


class FeatureTransformer(BaseEstimator, TransformerMixin):
    """
    A custom transformer designed for preprocessing features in a Grailed listing dataset.
    The transformer handles numeric features and various types of categorical features
    (one-hot encoding, ordinal encoding, target encoding, and CatBoost encoding).

    Parameters:
        numeric_cols: List of column names for numeric features.
        ohe_cols: List of column names for categorical features to be one-hot encoded.
        oe_cols: List of column names for categorical features to be ordinal encoded.
        catboost_cols: List of column names for categorical features to be encoded using CatBoostEncoder.
        te_cols: List of column names for categorical features to be target encoded.
                 By default, all categorical features not specified in `ohe_cols`, `oe_cols`, or `catboost_cols`
                 will be target encoded.
        scaler_params: Dictionary of parameters for StandardScaler.
        ohe_params: Dictionary of parameters for OneHotEncoder.
        oe_params: Dictionary of parameters for OrdinalEncoder.
        catboost_params: Dictionary of parameters for CatBoostEncoder.
        te_params: Dictionary of parameters for TargetEncoder.
    """

    def __init__(
        self,
        numeric_cols: list[str] = ["n_photos"],
        ohe_cols: list[str] = ["department", "category"],
        oe_cols: list[str] = ["condition"],
        catboost_cols: list[str] = None,
        te_cols: list[str] = None,
        scaler_params: dict = None,
        ohe_params: dict = None,
        oe_params: dict = None,
        catboost_params: dict = None,
        te_params: dict = None,
        normalize_size: bool = False,
        no_encoding: bool = False,
    ):
        # Initialize feature categories and set default lists if not provided
        self.numeric_cols = numeric_cols or []
        self.ohe_cols = ohe_cols or []
        self.oe_cols = oe_cols or []
        self.catboost_cols = catboost_cols or []
        self.scaler_params = scaler_params or {}
        self.ohe_params = ohe_params or {}
        self.oe_params = oe_params or {}
        self.catboost_params = catboost_params or {}
        self.te_params = te_params or {}
        self.normalize_size = normalize_size
        self.no_encoding = no_encoding

        # Default to target encoding for remaining categorical columns not specified in ohe_cols, oe_cols, or catboost_cols
        self.te_cols = te_cols or list(
            {
                "designer",
                "department",
                "category",
                "subcategory",
                "size",
                "color",
                "condition",
            }
            - set(self.ohe_cols)
            - set(self.oe_cols)
            - set(self.catboost_cols)
        )

        # Determine the appropriate encoder for the 'size' feature based on where it was originally specified
        self.size_encoder = None
        if "size" in self.ohe_cols:
            self.ohe_cols.remove("size")
            self.size_encoder = OneHotEncoder(**self.ohe_params)
        elif "size" in self.oe_cols:
            self.oe_cols.remove("size")
            self.size_encoder = OrdinalEncoder(**self.oe_params)
        elif "size" in self.catboost_cols:
            self.catboost_cols.remove("size")
            self.size_encoder = CatBoostEncoder(**self.catboost_params)
        elif "size" in self.te_cols:
            self.te_cols.remove("size")
            self.size_encoder = TargetEncoder(cols=["size"], **self.te_params)

        # Mapping for ordinal encoding the 'condition' feature
        self.oe_mapping = [
            {
                "col": "condition",
                "mapping": dict(zip(["Worn", "Used", "Gently Used", "New"], range(4))),
            }
        ]

        # Initialize the transformers
        self.transformer = self._initialize_transformer()

    def _initialize_transformer(self):
        """
        Initialize the ColumnTransformer with the selected feature transformers.
        """
        transformers = []

        # Drop the remainder columns
        remainder = "drop"

        if self.no_encoding:
            transformers.extend(
                [
                    (
                        "passthrough",
                        self.numeric_cols
                        + self.oe_cols
                        + self.ohe_cols
                        + self.catboost_cols
                        + self.te_cols,
                    ),
                    (SizeTransformer(self.normalize_size), ["size", "category"]),
                ]
            )
            return make_column_transformer(
                *transformers, remainder=remainder, verbose_feature_names_out=False
            )

        # Pipeline specifically for the size feature
        if self.size_encoder:
            size_pipeline = make_pipeline(
                SizeTransformer(self.normalize_size), self.size_encoder
            )
            transformers.append((size_pipeline, ["size", "category"]))

        if self.numeric_cols:
            transformers.append(
                (StandardScaler(**self.scaler_params), self.numeric_cols)
            )
        # Categorical features for one-hot encoding
        if self.ohe_cols:
            transformers.append((OneHotEncoder(**self.ohe_params), self.ohe_cols))
        # Categorical features for ordinal encoding
        if self.oe_cols:
            transformers.append(
                (
                    OrdinalEncoder(mapping=self.oe_mapping, **self.oe_params),
                    self.oe_cols,
                )
            )
        # Categorical features for CatBoost encoding
        if self.catboost_cols:
            transformers.append(
                (CatBoostEncoder(**self.catboost_params), self.catboost_cols)
            )
        # Categorical features for target encoding
        if self.te_cols:
            transformers.append(
                (TargetEncoder(cols=self.te_cols, **self.te_params), self.te_cols)
            )

        return make_column_transformer(
            *transformers, remainder=remainder, verbose_feature_names_out=False
        )

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        """
        Fit the transformers to the data.

        Parameters:
            X: The input data to fit the transformers on.
            y: The target variable.

        Returns:
            Fitted FeatureTransformer instance.
        """
        self.transformer.fit(X, y)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input data using the fitted transformers.

        Parameters:
            X: The input data to transform.

        Returns:
            The transformed data as a pandas DataFrame.
        """
        return self.transformer.transform(X)

    def get_params(self, deep: bool = True):
        """
        Get the parameters of the FeatureTransformer and its internal transformers.

        Parameters:
            deep: Whether to return the parameters of the internal transformers.

        Returns:
            A dictionary of parameters.
        """
        if self.no_encoding:
            params = {"no_encoding": True}
        else:
            params = super().get_params(deep)
        if deep:
            params.update(self.transformer.get_params(deep))
        return params

    def set_params(self, **params):
        """
        Set the parameters of the FeatureTransformer and its internal transformers.

        Parameters:
            params: Dictionary of parameters to update.

        Returns:
            The updated FeatureTransformer instance.
        """
        for param_group in [
            "scaler_params",
            "ohe_params",
            "oe_params",
            "catboost_params",
            "te_params",
            "no_encoding",
        ]:
            if param_group in params:
                setattr(self, param_group, params.pop(param_group))
        super().set_params(**params)
        self.transformer = (
            self._initialize_transformer()
        )  # Reinitialize with updated parameters
        return self

    def get_feature_names_out(self, *args, **params):
        return self.transformer.get_feature_names_out(*args, **params)
