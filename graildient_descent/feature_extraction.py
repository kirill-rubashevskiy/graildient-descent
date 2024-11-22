import numpy as np
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.pipeline import make_pipeline
from umap import UMAP


RANDOM_STATE = 42

vectorizers = {
    "count": CountVectorizer(),
    "tfidf": TfidfVectorizer(),
}

reducers = {
    "pca": PCA(svd_solver="arpack", random_state=RANDOM_STATE),
    "umap": UMAP(random_state=RANDOM_STATE),
}


class TextStatsExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [self._extract_text_stats(text) for text in X]

    @staticmethod
    def _extract_text_stats(text: str) -> dict:
        """
        Extract basic statistics from text, such as length and word count.

        Parameters:
            text: text string.

        Returns:
            A dictionary containing text statistics.
        """
        if isinstance(text, str) and text != "missing":
            return {
                "length": len(text),
                "num_words": len(text.split()),
                "avg_word_length": len(text) / len(text.split()),
            }
        return {"length": 0, "num_words": 0, "avg_word_length": 0}


class SentimentExtractor(BaseEstimator, TransformerMixin):
    """
    Extracts a sentiment score from the input text using the VADER sentiment analyzer.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return pd.DataFrame([[self._get_sentiment(text)] for text in X])

    @staticmethod
    def _get_sentiment(text: str) -> float:
        if isinstance(text, str) and text != "missing":
            return SentimentIntensityAnalyzer().polarity_scores(text)["compound"]
        return 0.0


class MissingHashtagsExtractor(BaseEstimator, TransformerMixin):
    """
    Creates a binary feature indicating if the 'hashtags' column has the value 'missing'.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return pd.DataFrame([[self._is_missing(text)] for text in X])

    @staticmethod
    def _is_missing(text: str) -> int:
        return 1 if text == "missing" else 0


class TextFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        text_cols: list[str] = ["item_name", "description", "hashtags"],
        use_stats: bool = True,
        use_embeddings: bool = True,
        use_sentiment: bool = True,
        use_missing_hashtags: bool = True,
        vectorizer_class: str = "count",
        vectorizer_params: dict = {"ngram_range": (1, 2), "max_features": 5000},
        reducer_class: str = "pca",
        reducer_params: dict = {"n_components": 100},
    ):
        """
        Initialize the TextFeatureExtractor.

        Parameters:
            text_cols: text column to process.
            use_stats: Whether to include text statistics in the output.
            use_embeddings: Whether to include text embeddings (with PCA) in the output.
            use_sentiment: Extracts a sentiment score from the text column.
                           The sentiment score is computed using the VADER sentiment analyzer,
                           and it measures the polarity of the text, ranging from -1
                           (negative) to 1 (positive).
            use_missing_hashtags: Creates a binary feature indicating whether the 'hashtags'
                                  column is marked as 'missing'.
            vectorizer_class: Vectorizer class.
            vectorizer_params: Parameters for the vectorizer.
            pca_n_components: Number of PCA components.
        """
        self.text_cols = text_cols
        self.use_stats = use_stats
        self.use_embeddings = use_embeddings
        self.use_sentiment = use_sentiment
        self.use_missing_hashtags = use_missing_hashtags
        self.vectorizer_class = vectorizer_class
        self.vectorizer_params = vectorizer_params
        self.reducer_class = reducer_class
        self.reducer_params = reducer_params
        self.transformer = self._initialize_transformer()

    def _create_embedding_pipeline(self):
        """
        Create a pipeline for text embedding including preprocessing, vectorization, and PCA.

        Parameters:
            vectorizer_class: The vectorizer class to use ('tfidf' or 'count').
            vectorizer_params: The parameters for the vectorizer.
            pca_n_components: Number of PCA components.

        Returns:
            A scikit-learn Pipeline.
        """
        if "ngram_range" in self.vectorizer_params and isinstance(
            self.vectorizer_params["ngram_range"], list
        ):
            self.vectorizer_params["ngram_range"] = tuple(
                self.vectorizer_params["ngram_range"]
            )
        vectorizer = vectorizers[self.vectorizer_class]
        vectorizer.set_params(**self.vectorizer_params)
        reducer = reducers[self.reducer_class]
        reducer.set_params(**self.reducer_params)

        steps = [
            vectorizer,
            reducer,
        ]

        return make_pipeline(*steps)

    def _create_stats_pipeline(self):
        """
        Create a pipeline for extracting text statistics.

        Returns:
            A scikit-learn Pipeline.
        """
        return make_pipeline(TextStatsExtractor(), DictVectorizer())

    def _initialize_transformer(self):
        """
        Initialize the internal transformer pipeline based on configuration.
        """
        transformers = []

        if self.use_embeddings:
            for text_col in self.text_cols:
                transformers.append(
                    (
                        f"{text_col}_embeds",
                        self._create_embedding_pipeline(),
                        text_col,
                    )
                )

        if self.use_stats:
            for text_col in self.text_cols:
                transformers.append(
                    (f"{text_col}_stats", self._create_stats_pipeline(), text_col)
                )

        if self.use_sentiment:
            transformers.append(
                ("sentiment_score", SentimentExtractor(), "description")
            )

        if self.use_missing_hashtags:
            transformers.append(
                ("is_hashtags_missing", MissingHashtagsExtractor(), "hashtags")
            )

        return ColumnTransformer(transformers=transformers, remainder="drop")

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        """
        Fit the transformers to the data.

        Parameters:
            X: DataFrame containing the text columns to fit.
            y: Ignored, only included for compatibility.

        Returns:
            Fitted TextFeatureExtractor instance.
        """
        self.transformer.fit(X, y)
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform the input data using the fitted transformers.

        Parameters:
            X: DataFrame containing the text columns to transform.

        Returns:
            Transformed DataFrame.
        """
        transformed_data = self.transformer.transform(X)
        return transformed_data

    def get_params(self, deep: bool = True) -> dict:
        """
        Get the parameters of the TextFeatureExtractor.

        Parameters:
            deep: Whether to include parameters of nested objects.

        Returns:
            Dictionary of parameters.
        """
        params = super().get_params(deep)
        if deep:
            params.update(self.transformer.get_params(deep))
        return params

    def set_params(self, **params):
        """
        Set the parameters of the TextFeatureExtractor.

        Parameters:
            params: Dictionary of parameters to set.

        Returns:
            The updated TextFeatureExtractor instance.
        """
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Reinitialize the transformer only if any relevant parameter is updated
        if any(
            param in params
            for param in [
                "text_cols",
                "vectorizer_class",
                "vectorizer_params",
                "reducer_class",
                "reducer_params",
                "use_stats",
                "use_embeddings",
                "use_sentiment",
                "use_missing_hashtags",
            ]
        ):
            self.transformer = self._initialize_transformer()

        return self
