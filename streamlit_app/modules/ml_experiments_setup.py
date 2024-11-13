import altair as alt
import streamlit as st
from modules.data_utils import load_data_from_s3
from modules.visualization import draw_price_kde_chart


def display_ml_experiments_setup():
    train_df = load_data_from_s3("grailed", "data/splits/25k/train_25k.csv", nrows=1000)
    train_df["dataset"] = "train"
    eval_df = load_data_from_s3("grailed", "data/splits/25k/eval_25k.csv", nrows=1000)
    eval_df["dataset"] = "eval"
    test_df = load_data_from_s3("grailed", "data/splits/25k/test_25k.csv", nrows=1000)
    test_df["dataset"] = "test"

    st.markdown(
        """
        ## Baseline Model

        To establish a benchmark for our ML experiments, we’ll start with a baseline
        model that predicts the **median sold price** for every item.

        ## Experiment Stages

        Our ML experiments will be structured in five stages to ensure a thorough
        exploration of modeling options:

        1. **Determine Estimator Type**: Test various models (e.g., linear, tree-based,
        ensemble) to identify promising candidates.
        2. **Explore Feature Types**: Evaluate performance using tabular features alone,
         text features alone, and a combination of both.
        3. **Test Different Encoding Strategies for Categorical Features**: Experiment with
        different encoding techniques like One-Hot Encoding, Target Encoding, and
        CatBoost Encoding for categorical features.
        4. **Optimize Text Feature Vectorization**: Experiment with various vectorizers
        (TF-IDF, Count) and dimensionality reduction techniques (e.g., PCA, UMAP) for
        text features.
        5. **Hyperparameter Tuning**: Fine-tune the hyperparameters of the
        best-performing models to optimize performance.

        ## Evaluation Strategy

        With a mid-sized dataset (~25K items), we’ve opted for a single evaluation set
        instead of cross-validation to streamline the experiment process. Given the
        dataset’s size, this approach provides sufficient data for training and
        validation while allowing us to assess model performance consistently across
        iterations.
        - **60%** for training
        - **20%** for evaluation
        - **20%** for testing

        To see the data splitting process, refer to this
        [Jupyter Notebook](https://github.com/kirill-rubashevskiy/graildient-descent/blob/main/notebooks/prepare_datasets.ipynb).
        Let's ensure that the target is similarly distributed across splits:
        """
    )

    top = draw_price_kde_chart(train_df).encode(
        x=alt.X("sold_price:Q").axis(title=None, labels=False),
    )
    middle = draw_price_kde_chart(eval_df).encode(
        x=alt.X("sold_price:Q").axis(title=None, labels=False),
    )
    bottom = draw_price_kde_chart(test_df).encode(
        x=alt.X("sold_price:Q").axis(title="Sold Price", format="$.0f"),
    )

    st.altair_chart(
        (top & middle & bottom)
        .resolve_scale(x="shared", y="shared", color="shared")
        .properties(title="Sold Price Distribution, by Dataset")
        .configure_title(anchor="middle"),
        use_container_width=True,
    )

    st.markdown(
        """
        ## Evaluation Metrics

        Given the positive skew of the target distribution, we will use **Root Mean Squared Logarithmic Error (RMSLE)** as the primary evaluation metric to account for outliers and large variances. **Weighted Absolute Percentage Error (WAPE)** will serve as a secondary metric to provide additional insight.

        A minimum improvement of **0.01 in evaluation RMSLE** will be considered significant for model advancement.

        ## Experiment Tracking

        All experiments will be tracked using **Weights & Biases (wandb)** for organized logging and comparison of configurations.
        Here is the link to the project page on wandb: [Graildient Descent Project on W&B](https://wandb.ai/kirill-rubashevskiy/graildient-descent?nw=nwuserkirillrubashevskiy)

        ## Default Data Preprocessing and Feature Engineering

        - **Text Processing**: Convert to lowercase, apply lemmatization, and remove
        stop words.
        - **Encoding Strategy**:
          - **One-Hot Encoding**: Low-cardinality features such as department and
          category.
          - **Ordinal Encoding**: For condition feature.
          - **Target Encoding**: For mid- and high-cardinality features like designer,
          size, color and subcategory.
        - **Text Embeddings**: **TF-IDF with PCA**:
          - **Item name**: (1,1) ngram range, 5000 max features, 100 PCA components.
          - **Description**: (1,3) ngram range, 10000 max features, 200 PCA components.
          - **Hashtags**: (1,1) ngram range, 2000 max features, 50 PCA components.
        - **Feature Engineering**: Extract text-based statistics such as character length, word count, average word length, and sentiment scores.
        """
    )
