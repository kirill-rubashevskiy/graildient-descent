import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.pipeline import make_pipeline


vectorizers = {
    "count": CountVectorizer,
    "tfidf": TfidfVectorizer,
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

    def get_feature_names_out(self, input_features=None):
        return ["length", "num_words", "avg_word_length"]


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

    def get_feature_names_out(self, input_features=None):
        return ["sentiment_score"]


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

    def get_feature_names_out(self, input_features=None):
        return ["is_hashtags_missing"]


class ListTransformer(TransformerMixin):
    """
    Custom transformer to convert array output into a list.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Convert each row (which is currently a numpy array) into a list
        return pd.DataFrame([[list(row)] for row in X])

    def get_feature_names_out(self, input_features=None):
        return ["list"]


class TextFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        text_cols: list[str] = ("item_name", "description", "hashtags"),
        use_stats: bool = True,
        use_embeddings: bool = True,
        use_sentiment: bool = True,
        use_missing_hashtags: bool = True,
        item_name_vectorizer_class: str = "count",
        item_name_vectorizer_params: dict = None,
        item_name_pca_n_components: int = 100,
        description_vectorizer_class: str = "tfidf",
        description_vectorizer_params: dict = None,
        description_pca_n_components: int = 200,
        hashtags_vectorizer_class: str = "count",
        hashtags_vectorizer_params: dict = None,
        hashtags_pca_n_components: int = 50,
        return_embeddings_as_list: bool = False,
    ):
        """
        Initialize the TextFeatureExtractor.

        Parameters:
            text_cols: List of text columns to process.
            use_stats: Whether to include text statistics in the output.
            use_embeddings: Whether to include text embeddings (with PCA) in the output.
            use_sentiment: Extracts a sentiment score from the 'description' text column.
                           The sentiment score is computed using the VADER sentiment analyzer,
                           and it measures the polarity of the text, ranging from -1
                           (negative) to 1 (positive).
            use_missing_hashtags: Creates a binary feature indicating whether the 'hashtags'
                                  column is marked as 'missing'. If the 'hashtags' value
                                  is 'missing', the feature is set to 1; otherwise, it
                                  is set to 0.
            item_name_vectorizer_class: Vectorizer class for the 'item_name' column.
            item_name_vectorizer_params: Parameters for the vectorizer for 'item_name'.
            item_name_pca_n_components: Number of PCA components for 'item_name' embeddings.
            description_vectorizer_class: Vectorizer class for the 'description' column.
            description_vectorizer_params: Parameters for the vectorizer for 'description'.
            description_pca_n_components: Number of PCA components for 'description' embeddings.
            hashtags_vectorizer_class: Vectorizer class for the 'hashtags' column.
            hashtags_vectorizer_params: Parameters for the vectorizer for 'hashtags'.
            hashtags_pca_n_components: Number of PCA components for 'hashtags' embeddings.
            return_embeddings_as_list: If True, return embeddings as separate lists in separate columns (for CatBoost compatibility).
        """
        self.text_cols = text_cols
        self.use_stats = use_stats
        self.use_embeddings = use_embeddings
        self.use_sentiment = use_sentiment
        self.use_missing_hashtags = use_missing_hashtags
        self.item_name_vectorizer_class = item_name_vectorizer_class
        self.item_name_vectorizer_params = item_name_vectorizer_params or {
            "ngram_range": (1, 1),
            "max_features": 5000,
        }
        self.item_name_pca_n_components = item_name_pca_n_components
        self.description_vectorizer_class = description_vectorizer_class
        self.description_vectorizer_params = description_vectorizer_params or {
            "ngram_range": (1, 3),
            "max_features": 10000,
        }
        self.description_pca_n_components = description_pca_n_components
        self.hashtags_vectorizer_class = hashtags_vectorizer_class
        self.hashtags_vectorizer_params = hashtags_vectorizer_params or {
            "ngram_range": (1, 1),
            "max_features": 2000,
        }
        self.hashtags_pca_n_components = hashtags_pca_n_components
        self.return_embeddings_as_list = return_embeddings_as_list
        self.transformer = self._initialize_transformer()

    def _create_embedding_pipeline(
        self, vectorizer_class, vectorizer_params, pca_n_components
    ):
        """
        Create a pipeline for text embedding including preprocessing, vectorization, and PCA.

        Parameters:
            vectorizer_class: The vectorizer class to use ('tfidf' or 'count').
            vectorizer_params: The parameters for the vectorizer.
            pca_n_components: Number of PCA components.

        Returns:
            A scikit-learn Pipeline.
        """
        if "ngram_range" in vectorizer_params and isinstance(
            vectorizer_params["ngram_range"], list
        ):
            vectorizer_params["ngram_range"] = tuple(vectorizer_params["ngram_range"])
        steps = [
            vectorizers[vectorizer_class](**vectorizer_params),
            PCA(n_components=pca_n_components, svd_solver="arpack", random_state=42),
        ]
        if self.return_embeddings_as_list:
            steps.append(ListTransformer())

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

        for vectorizer_class in [
            self.item_name_vectorizer_class,
            self.description_vectorizer_class,
            self.hashtags_vectorizer_class,
        ]:
            if (
                vectorizer_class is not None
                and vectorizer_class not in vectorizers.keys()
            ):
                raise ValueError(
                    f"Vectorizer '{vectorizer_class}' is not supported. "
                    f"Supported vectorizers are {list(vectorizers.keys())}"
                )

        transformers = []

        if self.use_embeddings:
            if "item_name" in self.text_cols:
                transformers.append(
                    (
                        "item_name_embeds",
                        self._create_embedding_pipeline(
                            self.item_name_vectorizer_class,
                            self.item_name_vectorizer_params,
                            self.item_name_pca_n_components,
                        ),
                        "item_name",
                    )
                )
            if "description" in self.text_cols:
                transformers.append(
                    (
                        "description_embeds",
                        self._create_embedding_pipeline(
                            self.description_vectorizer_class,
                            self.description_vectorizer_params,
                            self.description_pca_n_components,
                        ),
                        "description",
                    )
                )
            if "hashtags" in self.text_cols:
                transformers.append(
                    (
                        "hashtags_embeds",
                        self._create_embedding_pipeline(
                            self.hashtags_vectorizer_class,
                            self.hashtags_vectorizer_params,
                            self.hashtags_pca_n_components,
                        ),
                        "hashtags",
                    )
                )

        if self.use_stats:
            for text_col in self.text_cols:
                transformers.append(
                    (f"{text_col}_stats", self._create_stats_pipeline(), text_col)
                )

        if self.use_sentiment:
            if "description" in self.text_cols:
                transformers.append(
                    ("description_sentiment", SentimentExtractor(), "description")
                )

        if self.use_missing_hashtags:
            if "hashtags" in self.text_cols:
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

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input data using the fitted transformers.

        Parameters:
            X: DataFrame containing the text columns to transform.

        Returns:
            Transformed DataFrame.
        """
        transformed_data = self.transformer.transform(X)
        return pd.DataFrame(transformed_data, columns=self.get_feature_names_out())

    def get_feature_names_out(self, input_features=None):
        """
        Get the feature names output by the transformers.

        Parameters:
            input_features: Not used. Included for compatibility with scikit-learn API.

        Returns:
            List of feature names.
        """
        return self.transformer.get_feature_names_out()

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
                "item_name_vectorizer_class",
                "item_name_vectorizer_params",
                "item_name_pca_n_components",
                "description_vectorizer_class",
                "description_vectorizer_params",
                "description_pca_n_components",
                "hashtags_vectorizer_class",
                "hashtags_vectorizer_params",
                "hashtags_pca_n_components",
                "use_stats",
                "use_embeddings",
                "return_embeddings_as_list",
            ]
        ):
            self.transformer = self._initialize_transformer()

        return self
