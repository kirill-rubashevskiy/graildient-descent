import altair as alt
import pandas as pd
import streamlit as st
from modules.data_utils import load_data_from_s3


SAMPLE_SIZE = 1000
PRICE_MAX = 1000


def display_ml_experiments_setup():
    # load datasets
    train_df = load_data_from_s3(
        st.secrets.s3.bucket_name,
        f"{st.secrets.s3.data_path}/train_25k.csv",
        nrows=SAMPLE_SIZE,
    )
    train_df["dataset"] = "train"
    eval_df = load_data_from_s3(
        st.secrets.s3.bucket_name,
        f"{st.secrets.s3.data_path}/eval_25k.csv",
        nrows=SAMPLE_SIZE,
    )
    eval_df["dataset"] = "eval"
    test_df = load_data_from_s3(
        st.secrets.s3.bucket_name,
        f"{st.secrets.s3.data_path}/test_25k.csv",
        nrows=SAMPLE_SIZE,
    )
    test_df["dataset"] = "test"
    data = pd.concat([train_df, eval_df, test_df])

    st.markdown(
        """
        ## Baseline Model

        To establish a benchmark for our ML experiments, we'll start with a baseline
        model. Given the positive skew of the target distribution, our baseline model
        predicts the **median sold price** for every item.

        ## Experiment Stages

        Our ML experiments will be structured in five stages to ensure a thorough
        exploration of modeling options:

        1. **Determine Estimator Type**: Test various models (e.g., linear, tree-based,
        ensemble) to identify promising candidates.
        2. **Feature Type Impact**: Evaluate performance using tabular features alone,
        text features alone, and a combination of both.
        3. **Categorical Features Encoding Optimization**: Experiment with different
        encoding techniques like One-Hot Encoding, Target Encoding, and CatBoost
        Encoding.
        4. **Text Feature Optimization**: Experiment with various vectorizers (TF-IDF,
        BoW) and dimensionality reduction techniques (e.g., PCA, UMAP).
        5. **Model Hyperparameter Tuning**: Fine-tune the hyperparameters of the
        best-performing models to optimize performance.

        ## Evaluation Strategy

        With a mid-sized dataset (~25K items), we've opted for a single evaluation set
        instead of cross-validation to streamline the experiment process. Given the
        dataset's size, this approach provides sufficient data for training and
        validation while allowing us to assess model performance consistently across
        iterations.

        - **60%** for training
        - **20%** for evaluation
        - **20%** for testing

        To see the data splitting process, refer to this [Jupyter Notebook](https://github.com/kirill-rubashevskiy/graildient-descent/blob/main/notebooks/prepare_datasets.ipynb).
        """
    )

    base = (
        alt.Chart(data)
        .transform_density(
            "sold_price", as_=["sold_price", "density"], groupby=["dataset"]
        )
        .mark_area(opacity=0.7)
        .encode(
            x=alt.X("sold_price:Q")
            .axis(title="Sold Price", format="$.0f")
            .scale(domainMax=PRICE_MAX, clamp=True),
            y="density:Q",
            color=alt.Color("dataset"),
        )
        .properties(height=300)
    )
    train_chart = base.transform_filter(alt.datum.dataset == "train")
    eval_chart = base.transform_filter(alt.datum.dataset == "eval")
    test_chart = base.transform_filter(alt.datum.dataset == "test")

    st.altair_chart(
        (train_chart + eval_chart + test_chart)
        .resolve_scale(x="shared", y="shared", color="shared")
        .properties(title="Sold Price Distribution, by Dataset")
        .configure_title(anchor="middle"),
        use_container_width=True,
    )

    st.markdown(
        """
        ## Evaluation Metrics

        Given the positive skew of the target distribution, we will use **Root Mean
        Squared Logarithmic Error (RMSLE)** as the primary evaluation metric to account
        for outliers and large variances. **Weighted Absolute Percentage Error (WAPE)**
        will serve as a secondary metric to provide additional insight.

        Unless specifically stated, a minimum improvement of **0.01 in evaluation
        RMSLE** was considered significant for model advancement.

        ## Experiment Tracking

        All experiments have been tracked using **Weights & Biases (wandb)** for
        organized logging and comparison of configurations. Experiments are performed
        using wandb sweeps.

        Configuration for each experiment is defined in YAML files under the [**sweeps/**](https://github.com/kirill-rubashevskiy/graildient-descent/blob/main/sweeps/)
        directory.

        Here is the link to the project page on wandb: [Graildient Descent Project on W&B](https://wandb.ai/kirill-rubashevskiy/graildient-descent?nw=nwuserkirillrubashevskiy)

        ## Default Data Preprocessing and Feature Engineering

        - **Category Features Encoding Strategy**:
          - **One-Hot Encoding**: For low-cardinality features (department and category)
          - **Ordinal Encoding**: For condition feature
          - **Target Encoding**: For mid-cardinality features (size and subcategory) and
          high-cardinality features (designer and color)
        - **Text Features Processing**: Convert to lowercase, apply lemmatization, and
        remove stop words
        - **Text Features Embeddings**: BoW with PCA ((1,2) ngram range, 5000 max
        features, 100 PCA components)
        - **Feature Engineering**: Extract text-based statistics such as character
        length, word count, average word length, sentiment scores and hashtags usage
        - **Target Preprocessing**: Given the positive skew of the target distribution,
        the train set target was log-transformed. Metrics were calculated using
        exponentially transformed predictions
        """
    )
