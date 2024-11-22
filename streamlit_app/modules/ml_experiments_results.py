import altair as alt
import pandas as pd
import streamlit as st
from modules.data_utils import get_sweep_data


def display_ml_experiments_results():

    models = ["catboost", "ridge"]
    model_selection = alt.selection_point(
        fields=["estimator_class"],
        bind=alt.binding_select(options=models, name="Model "),
        value=models[0],
    )

    st.markdown(
        """
        ## Executive Summary

        Starting from a baseline median predictor (RMSLE: 1.02), we achieved best
        performance with a CatBoost model using both tabular and text features
        (RMSLE: 0.64). Key improvements came from:

        - Using CatBoost model (RMSLE: 0.70, 31% improvement over baseline)
        - Combining tabular and text features (RMSLE: 0.65, 7% improvement over
        tabular-only model)

        ## Determining Estimator Type

        We began by evaluating different model families using only tabular features with
        default preprocessing.
        """
    )

    source = get_sweep_data("gs3a8u6n")

    chart = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x=alt.X("estimator_class:N").sort("y").axis(title=None, labelAngle=0),
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.5, clamp=True),
        )
        .properties(height=250, title="Metrics, by Estimator")
    )
    text = chart.mark_text(baseline="bottom", dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )

    st.altair_chart(
        (chart + text).configure_title(anchor="middle"), use_container_width=True
    )

    st.markdown(
        """
        **What we see:**
        - Our baseline median predictor achieved an RMSLE of 1.017
        - CatBoost achieved RMSLE of 0.70, a 30.9% improvement over baseline
        - Random Forest achieved RMSLE of 0.74, a 27.2% improvement over baseline
        - Linear models performed well, with Ridge achieving RMSLE of 0.74, a 26.8%
        improvement over baseline
        - All tested models outperformed our baseline median predictor

        **What it means:**
        - The strong performance of both linear and tree-based models suggests our
        features have both linear and non-linear relationships with price
        - We should focus on CatBoost (best performer) and Ridge (best linear model) for
        subsequent experiments, as they represent different model families and provide
        complementary strengths
        """
    )

    st.markdown(
        """
        ## Feature Type Impact

        We next investigated how different feature types (tabular, text, or combined)
        affect model performance.
        """
    )

    source = get_sweep_data("82onjiqa")
    source.rename(columns={"rmsle_train": "train", "rmsle_eval": "eval"}, inplace=True)
    source["features_used"] = source.apply(
        lambda row: (
            "both"
            if row["use_tab_features"] and row["use_text_features"]
            else "tabular" if row["use_tab_features"] else "text"
        ),
        axis=1,
    )
    source = pd.melt(
        source,
        id_vars=["features_used", "estimator_class"],
        value_vars=["train", "eval"],
        var_name="rmsle",
        value_name="rmsle_value",
    ).join(
        pd.melt(
            source,
            id_vars=["features_used", "estimator_class"],
            value_vars=["wape_train", "wape_eval"],
            var_name="wape",
            value_name="wape_value",
        ).drop(columns=["features_used", "estimator_class"])
    )

    base = (
        alt.Chart(source)
        .add_selection(model_selection)
        .transform_filter(model_selection)
        .mark_bar()
        .properties(height=150)
    )

    left = (
        base.transform_filter(alt.datum.rmsle == "eval")
        .encode(
            x=alt.X("features_used:N").axis(title="Used Features", labelAngle=0),
            y=alt.Y("rmsle_value:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.4, clamp=True),
        )
        .properties(width=150)
    )

    left_text = left.mark_text(baseline="bottom", dy=-3).encode(
        text=alt.Text("rmsle_value:Q", format=",.2f"), color=alt.value("white")
    )

    right = base.encode(
        x=alt.X("features_used:N").axis(title="Used Features", labelAngle=0),
        y=alt.Y("rmsle_value:Q").axis(title="RMSLE").scale(domainMin=0.4, clamp=True),
        xOffset=alt.XOffset("rmsle:N").sort("descending"),
        color=alt.Color("rmsle:N").legend(title="RMSLE"),
    ).properties(width=300)

    right_text = right.mark_text(baseline="bottom", dx=3, dy=-3).encode(
        text=alt.Text("rmsle_value:Q", format=",.2f"), color=alt.value("white")
    )

    chart = (
        (left + left_text | right + right_text)
        .properties(title="Metrics, by Used Features")
        .configure_title(anchor="middle")
    )

    st.altair_chart(chart, use_container_width=True)

    st.write(
        """
        **What we see:**
        - CatBoost using both tabular and text features achieved RMSLE of 0.65, a 7.1% improvement over tabular-only model (RMSLE: 0.70)
        - Tabular features alone performed better than text features alone (CatBoost model RMSLE: 0.70 vs 0.73)
        - CatBoost showed more overfitting when using text features (RMSLE difference between train and eval: 0.12 with tabular only vs 0.25 with text only)

        **What it means:**
        - The complementary nature of tabular and text features suggests they capture different aspects of price determination
        - We need to implement overfitting mitigation strategies for CatBoost when using text features
        - The combined feature approach should be maintained for subsequent experiments
        """
    )

    st.write(
        """
        ## Categorical Features Encoding Optimization

        ### Successful Approaches

        We experimented with using CatBoost encoder (instead of Target encoder) to encode:
        - Mid-cardinality features (size and subcategory)
        - High-cardinality features (designer and color)
        - Both mid- and high-cardinality features
        - All categorical features
        """
    )

    cboost_none_source = get_sweep_data("82onjiqa")
    cboost_none_source = cboost_none_source[
        (cboost_none_source.use_tab_features is True)
        & (cboost_none_source.use_text_features is True)
    ]
    cboost_none_source["cboost_encoder_cols"] = "none"
    cboost_mid_high_source = get_sweep_data("2wyuq27i")
    cboost_mid_high_source["cboost_encoder_cols"] = cboost_mid_high_source[
        "transformer_params.catboost_cols"
    ].apply(
        lambda cols: (
            "mid_high" if len(cols) == 4 else "high" if "color" in cols else "mid"
        )
    )
    cboost_all_source = get_sweep_data("42rw45mi")
    cboost_all_source["cboost_encoder_cols"] = "all"
    source = pd.concat([cboost_none_source, cboost_mid_high_source, cboost_all_source])

    chart = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x=alt.X("cboost_encoder_cols")
            .sort("y")
            .axis(title="Features Encoded with CatBoost Encoder", labelAngle=0),
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE", format=".2f")
            .scale(domainMin=0.6, clamp=True),
        )
        .properties(width=280, height=200)
    )
    chart += chart.mark_text(baseline="bottom", dx=3, dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )
    chart = chart.facet(column=alt.Column("estimator_class:N", title=None))

    st.altair_chart(
        chart.properties(title="Eval RMSLE, by CatBoost Encoder Usage").configure_title(
            anchor="middle"
        ),
        use_container_width=True,
    )

    st.write(
        """
        **What we see:**
        - Using CatBoost encoding for mid- and high-cardinality features achieved RMSLE
        of 0.645, a 1.1% improvement over using Target encoding (RMSLE: 0.652)

        **What it means:**
        - We should maintain the hybrid encoding approach: CatBoost encoder for
        mid/high-cardinality features, one-hot for low-cardinality features
        """
    )

    st.write(
        """
        ### Unsuccessful Approaches

        We tested several other encoding variations, including:
        - One-hot encoding (instead of ordinal) for the condition feature
        - Size feature normalization
        - CatBoost encoder hyperparameter tuning
        """
    )

    ohe_source = get_sweep_data("snyty911")
    ohe_source["condition_encoder"] = "ohe"
    ordinal_source = get_sweep_data("2wyuq27i")
    ordinal_source = ordinal_source[
        ordinal_source["transformer_params.catboost_cols"].apply(lambda x: len(x) == 4)
    ]
    ordinal_source["condition_encoder"] = "ordinal"
    source = pd.concat([ohe_source, ordinal_source])

    left = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x=alt.X("condition_encoder:N").axis(labelAngle=0),
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.5, clamp=True),
        )
        .properties(width=125, height=200)
    )
    left += left.mark_text(baseline="bottom", dx=3, dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )
    left = left.facet(column=alt.Column("estimator_class:N", title=None)).properties(
        title="Metrics by Condition Encoder"
    )

    source = get_sweep_data("471imb4x")
    source.rename(
        columns={"transformer_params.normalize_size": "normalize_size"}, inplace=True
    )

    right = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x=alt.X("normalize_size:N").axis(labelAngle=0),
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.5, clamp=True),
        )
        .properties(width=125, height=200)
    )
    right += right.mark_text(baseline="bottom", dx=3, dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )
    right = right.facet(column=alt.Column("estimator_class:N", title=None)).properties(
        title="Metrics by Normalizing Size"
    )

    st.altair_chart((left | right).configure_title(anchor="middle"))

    source = get_sweep_data("hiyg1fjw")
    source.rename(columns={"transformer_params.catboost_params.a": "a"}, inplace=True)

    chart = (
        alt.Chart(source)
        .mark_line()
        .encode(
            x=alt.X("a:O").axis(labelAngle=0),
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.64, clamp=True),
            color="estimator_class:N",
        )
        .properties(height=300, title="Metrics by Catboost Encoder a Hyperparameter")
    )

    text = chart.mark_text(baseline="bottom", dx=3, dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )

    st.altair_chart(
        (chart + text).configure_title(anchor="middle"), use_container_width=True
    )

    st.write(
        """
        **What we see:**
        - None of these modifications produced statistically significant improvements

        **What it means:**
        - The original ordinal encoding for condition appropriately captures the natural
        order of item conditions
        - Raw size values contain more meaningful information than normalized ones
        - We should maintain the default CatBoost encoder configuration
        """
    )

    st.write(
        """
        ## Text Feature Optimization

        ### Vectorization Method

        We experimented with replacin BoW with TF-IDF.
        """
    )

    source = get_sweep_data("y9mh4q84")
    source.rename(
        columns={"extractor_params.vectorizer_class": "vectorizer_class"}, inplace=True
    )
    chart = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x=alt.X("vectorizer_class:N").axis(labelAngle=0),
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.64, clamp=True),
        )
        .properties(width=300, height=200)
    )

    chart += chart.mark_text(baseline="bottom", dx=3, dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )

    chart = chart.facet(column=alt.Column("estimator_class:N", title=None))

    st.altair_chart(
        chart.properties(title="Metrics, by Vectorizer").configure_title(
            anchor="middle"
        )
    )

    st.write(
        """
        **What we see:**
        - TF-IDF vectorization improved both CatBoost and Ridge models RMSLE
        - These improvements were consistent across both models but relatively modest
        (0.001-0.004 RMSLE improvement)

        **What it means:**
        - Term frequency weighting helps capture the relative importance of descriptive
        terms
        """
    )

    st.write(
        """
        ### Vectorizer Configuration

        We performed a shallow grid search over TF-IDF vectorizer hyperparameters:
        ngram_range and min_df.
        """
    )

    source = get_sweep_data("c97c2w57")
    source.rename(
        columns={
            "extractor_params.vectorizer_params.min_df": "min_df",
            "extractor_params.vectorizer_params.ngram_range": "ngram_range",
        },
        inplace=True,
    )
    source["ngram_range"] = source["ngram_range"].apply(lambda x: str(x))

    chart = (
        alt.Chart(source)
        .mark_rect()
        .encode(
            x=alt.X("min_df:O").axis(labelAngle=0),
            y="ngram_range:N",
            color="rmsle_eval:Q",
            column=alt.Column("estimator_class:N", title=None),
        )
        .properties(
            width=260, height=260, title="Metrics by Vectorizer Hyperparameters"
        )
        .configure_title(anchor="middle")
    )

    st.altair_chart(chart)

    st.write(
        """
        **What we see:**
        - Expanding to trigrams (1,3 n-gram range) improved both CatBoost and Ridge
        models RMSLE
        - A minimum document frequency of 5 provided optimal balance between feature
        coverage and noise reduction
        - These improvements were consistent across both models but relatively modest
        (0.002-0.004 RMSLE improvement)

        **What it means:**
        - Longer n-grams capture valuable phrases
        - The minimum document frequency threshold effectively filters noise without
        losing important signals
        """
    )

    st.write(
        """
        ### Dimensionality Reduction

        We experimented with replacing PCA with UMAP and performed a shallow grid search
        for n_components hyperparameter.
        """
    )

    source = get_sweep_data("ztx4ewq2")
    source.rename(
        columns={
            "extractor_params.reducer_class": "reducer_class",
            "extractor_params.reducer_params.n_components": "n_components",
        },
        inplace=True,
    )

    chart = (
        alt.Chart(source)
        .mark_line()
        .encode(
            x=alt.X("n_components:O").axis(labelAngle=0),
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.64, clamp=True),
            color="reducer_class:N",
        )
        .properties(width=260, height=260, title="Metrics by Reducer")
    )

    chart += chart.mark_text(baseline="bottom", dx=3, dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )
    chart = chart.facet(column=alt.Column("estimator_class:N", title=None))

    st.altair_chart(chart.configure_title(anchor="middle"))

    st.write(
        """
        **What we see:**
        - PCA consistently outperformed UMAP across all configurations
        - Ridge benefited from more components (150), while CatBoost performed best with fewer (100)

        **What it means:**
        - Linear dimensionality reduction appears more suitable for our text features
        - We should maintain model-specific dimensionality reduction configurations
        """
    )

    st.write(
        """
        ## Model Hyperparameter Tuning

        Using Bayesian optimization with 50 iterations, we tuned key hyperparameters for
        both models:

        - **CatBoost**:
          - **Learning Rate:** we sampled values from log-uniform distribution between
          values 0.001 and 0.3
          - **Tree Depth:** we sampled values from uniform distribution between
          values 4 and 10 (as [suggested](https://catboost.ai/docs/en/concepts/parameter-tuning)
          by CatBoost documentation)
          - **L2 Regularization:** we sampled values from log-uniform distribution between
          values 1 and 10
        - **Ridge**:
          - **L2 Regularization (alpha):** we sampled values from log-uniform distribution between
          values 1 and 100
        """
    )

    source = get_sweep_data("ec9aexam")
    source.sort_values(by="_timestamp", inplace=True)
    source = (
        source.reset_index(drop="True").reset_index().rename(columns={"index": "try"})
    )
    source["running_rmsle_eval"] = source["rmsle_eval"].cummin()

    base = (
        alt.Chart(source)
        .encode(x=alt.X("try:O").axis(labelAngle=0))
        .properties(height=300, title="Metric, by Tuning Try")
    )
    left_scatter = (
        base.mark_circle()
        .encode(
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.63, clamp=True),
        )
        .properties(width=500)
    )
    left_line = base.mark_line(strokeWidth=1).encode(
        y=alt.Y("running_rmsle_eval:Q")
        .axis(title="Eval RMSLE")
        .scale(domainMin=0.63, clamp=True),
        color=alt.value("white"),
    )

    before_tuning_source = get_sweep_data("ztx4ewq2")
    before_tuning_score = before_tuning_source[
        before_tuning_source.estimator_class == "catboost"
    ]["rmsle_eval"].min()

    source = pd.DataFrame(
        {
            "tuning": ["before", "after"],
            "rmsle_eval": [before_tuning_score, source["rmsle_eval"].min()],
        }
    )

    right = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x=alt.X("tuning:N").axis(labelAngle=0).sort("descending"),
            y=alt.Y("rmsle_eval:Q").axis(title=None, labels=False),
        )
        .properties(height=300, width=100, title="Metrics, by Tuning")
    )
    right_text = right.mark_text(baseline="bottom", dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )
    chart = (
        ((left_scatter + left_line) | right + right_text)
        .resolve_scale(y="shared")
        .properties(title="CatBoost Hyperparameters Tuning")
        .configure_title(anchor="middle")
    )

    st.altair_chart(chart, use_container_width=True)

    source = get_sweep_data("8mg77elq")
    source.sort_values(by="_timestamp", inplace=True)
    source = (
        source.reset_index(drop="True").reset_index().rename(columns={"index": "try"})
    )
    source["running_rmsle_eval"] = source["rmsle_eval"].cummin()

    base = (
        alt.Chart(source)
        .encode(x=alt.X("try:O").axis(labelAngle=0))
        .properties(height=300, title="Metric, by Tuning Try")
    )
    left_scatter = (
        base.mark_circle()
        .encode(
            y=alt.Y("rmsle_eval:Q")
            .axis(title="Eval RMSLE")
            .scale(domainMin=0.67, clamp=True),
        )
        .properties(width=500)
    )
    left_line = base.mark_line(strokeWidth=1).encode(
        y=alt.Y("running_rmsle_eval:Q").axis(title="Eval RMSLE"),
        color=alt.value("white"),
    )

    before_tuning_source = get_sweep_data("ztx4ewq2")
    before_tuning_score = before_tuning_source[
        before_tuning_source.estimator_class == "ridge"
    ]["rmsle_eval"].min()

    source = pd.DataFrame(
        {
            "tuning": ["before", "after"],
            "rmsle_eval": [before_tuning_score, source["rmsle_eval"].min()],
        }
    )

    right = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x=alt.X("tuning:N").axis(labelAngle=0).sort("descending"),
            y=alt.Y("rmsle_eval:Q").axis(title=None, labels=False),
        )
        .properties(height=300, width=100, title="Metrics, by Tuning")
    )
    right_text = right.mark_text(baseline="bottom", dy=-3).encode(
        text=alt.Text("rmsle_eval:Q", format=",.3f"), color=alt.value("white")
    )
    chart = (
        ((left_scatter + left_line) | right + right_text)
        .resolve_scale(y="shared")
        .properties(title="Ridge Hyperparameters Tuning")
        .configure_title(anchor="middle")
    )

    st.altair_chart(chart, use_container_width=True)

    st.write(
        """
        **What we see:**
        - Neither model showed significant improvement from hyperparameter tuning

        **What it means:**
        - The default hyperparameters are well-suited for our problem
        - Feature engineering and preprocessing had more impact than model tuning
        - The stability across configurations suggests our models are robust
        """
    )

    st.write(
        """
        ## Final Model Configuration

        Best performing setup:
        - Model: CatBoost with default hyperparameters
        - Final Metrics: RMSLE: 0.64 (37.1% improvement over baseline)
        - Features: Combined tabular and text
        - Categorical Encoding: CatBoost encoder for mid/high-cardinality features
        - Text Processing: TF-IDF vectorizer (ngram_range=(1,3), min_df=5)
        - Dimensionality Reduction: PCA (n_components=100)

        ## Next Steps

        - Building web service with current best performing model
        - Exploring deep learning approaches for potential further improvements
        """
    )
