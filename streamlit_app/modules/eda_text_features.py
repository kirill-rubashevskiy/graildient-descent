import altair as alt
import streamlit as st


@st.cache_data
def display_text_features(data, text_stats, text_ngrams, text_sentiment, q_low, q_high):
    text_features = ["item_name", "description", "hashtags"]
    stats = ["word_count", "char_count", "avg_word_length"]
    ngrams = ["unigrams", "bigrams", "trigrams"]

    feature_selection = alt.selection_point(
        fields=["text_feature"],
        bind=alt.binding_select(options=text_features, name="Feature "),
        value=text_features[0],
    )

    stat_selection = alt.selection_point(
        fields=["stat"],
        bind=alt.binding_select(options=stats, name="Statistic "),
        value=stats[0],
    )

    ngram_selection = alt.selection_point(
        fields=["ngram"],
        bind=alt.binding_select(options=ngrams, name="N-gram "),
        value=ngrams[0],
    )

    st.write(
        """
    Our dataset includes three text features:

    - Item name
    - Description
    - Hashtags
    """
    )

    # Text Statistics Section

    st.write(
        """
    *Note*: For this section, text data was preprocessed. This included
    tokenization, lemmatization, the removal of stopwords, and features extraction.
    You can explore the preprocessing steps in detail in the
    [Jupyter notebook](https://github.com/kirill-rubashevskiy/graildient-descent/blob/main/notebooks/eda_preprocess_text.ipynb)
    used for this process.
    """
    )

    st.header("Text Statistics")

    st.write(
        """
        - **Item name**: Currently Grailed does not allow item names longer than 60
        characters.
        - **Hashtags**: Grailed allows up to 10 hashtags.
        """
    )

    base = (
        alt.Chart(text_stats)
        .add_params(stat_selection, feature_selection)
        .transform_filter(feature_selection & stat_selection)
        .transform_filter(alt.datum.value != 0)
        .transform_aggregate(
            count="count()", mean="mean(sold_price)", groupby=["value"]
        )
        .properties(height=150)
    )

    top = (
        base.mark_bar()
        .encode(
            x=alt.X("value:Q").axis(title=None),
            y=alt.Y("count:Q").axis(title="Count of Records"),
            color=alt.value("#bab0ac"),
        )
        .properties(title="Statistic Distribution")
    )

    bottom = (
        base.mark_circle()
        .encode(
            x=alt.X("value:Q").axis(title="Statistic"),
            y=alt.Y("mean:Q").axis(title="Average Sold Price", format="$.0f"),
            color=alt.value("#e15759"),
            size="count:Q",
        )
        .properties(title="Sold Price by Statistic")
    )

    bottom_reg = bottom.transform_regression("value", "mean").mark_line()

    st.altair_chart(
        (top & bottom + bottom_reg)
        .resolve_scale(x="shared")
        .resolve_legend(size="independent")
        .configure_title(anchor="middle"),
        use_container_width=True,
    )

    st.write(
        """
    **What we see:**
    - **Word Count**:
        - Item name word count follows a normal distribution. Sellers often maximize the
        number of hashtags.
        - All three features show negative correlation between the number of words
        and sold price.
    - **Character Count**:
        - The multimodal distribution of item name character count suggests that
        Grailed may have changed the maximum item name length over time. A few item
        names exceed the 60-character limit, either because they were posted before
        this rule was introduced or because sellers found a way to bypass the limit.
        - Item name show negative correlation between the number of characters and
        sold price. With description and hashtags trend is not clear, probably due
        to outliers.
    - **Average Word Length**: Both item name and hashtags show positive correlation
    between average word length and sold price.

    **What it means:**
    - Text stats can be useful in predicting sold price, especially for item names
    and hashtags. The positive correlation between average word length and sold
    price might indicate that buyers prefer more descriptive titles and hashtags.
    """
    )

    # N-grams Section
    st.header("N-grams")

    base = (
        alt.Chart(text_ngrams)
        .add_params(ngram_selection, feature_selection)
        .transform_filter(
            feature_selection & ngram_selection & (alt.datum.value != "missing")
        )
        .mark_bar()
        .encode(
            y=alt.Y("value:N").sort(alt.SortField("count", "descending")).axis(None),
        )
        .properties(width=300, height=150)
    )

    top = (
        base.transform_filter(alt.datum.sold_price > q_high)
        .transform_aggregate(
            mean="mean(sold_price)", count="count()", groupby=["value"]
        )
        .transform_window(
            rank="row_number(value)",
            sort=[alt.SortField("count", order="descending")],
        )
        .transform_filter(alt.datum.rank <= 10)
        .mark_bar()
        .encode(
            y=alt.Y("value:N").sort(alt.SortField("count", "descending")).axis(None),
        )
        .properties(width=300)
    )

    top_left = top.encode(
        x=alt.X("count:Q").sort("descending").axis(title=None, labels=False),
        y=alt.Y("value:N")
        .sort(alt.SortField("count", "descending"))
        .axis(title="Top 25% Listings", labels=False),
        color=alt.value("#bab0ac"),
    )

    top_middle = (
        top.encode(alt.Text("value:N"), color=alt.value("white"))
        .mark_text()
        .properties(width=20)
    )

    top_right = top.encode(
        x=alt.X("mean:Q")
        .axis(title=None, labels=False, format="$.0f")
        .scale(type="log"),
        color=alt.value("#76b7b2"),
    )

    bottom = (
        base.transform_filter(alt.datum.sold_price < q_low)
        .transform_aggregate(
            mean="mean(sold_price)", count="count()", groupby=["value"]
        )
        .transform_window(
            rank="row_number(value)",
            sort=[alt.SortField("count", order="descending")],
        )
        .transform_filter(alt.datum.rank <= 10)
        .mark_bar()
        .encode(
            y=alt.Y("value:N").sort(alt.SortField("count", "descending")).axis(None),
        )
        .properties(width=300)
    )

    bottom_left = bottom.encode(
        x=alt.X("count:Q").sort("descending").axis(title="Count of Records"),
        y=alt.Y("value:N")
        .sort(alt.SortField("count", "descending"))
        .axis(title="Bottom 25% Listings", labels=False),
        color=alt.value("#bab0ac"),
    )

    bottom_middle = (
        bottom.encode(alt.Text("value:N"), color=alt.value("white"))
        .mark_text()
        .properties(width=20)
    )

    bottom_right = bottom.encode(
        x=alt.X("mean:Q")
        .axis(title="Average Sold Price", format="$.0f")
        .scale(type="log"),
        color=alt.value("#76b7b2"),
    )

    st.altair_chart(
        (
            (top_left & bottom_left).resolve_scale(x="shared")
            | (top_middle & bottom_middle)
            | (top_right & bottom_right).resolve_scale(x="shared")
        )
        .properties(title="Top 10 N-grams by Sold Price")
        .configure_title(anchor="middle")
    )

    st.write(
        """
    **What we see:**
    - **Item Name and Hashtags**:
        - Among the 25% most expensive sold items, we see more expensive materials
        (leather), subcategories (jacket), collaborations ("x"), luxury designers
        (Louis Vuitton, Maison Margiela), and markers of item exclusivity (archive).
        - Among the 25% least expensive sold items, we see mass-market designers (Nike),
        less expensive subcategories (polo shirt).
        - Not enough trigrams to make good generalizations.

    - **Description**:
        - Among the 25% most expensive sold items, we see better condition (brand new,
        great condition, never worn), more expensive designers (Chrome Hearts), and
        information on international buyers' responsibility for tax duty.
        - Among the 25% least expensive sold items, we see buyers' willingness to accept
        lower price offers (offers) and information on quick shipping
        (within working/business day, within-hour payment).

    **What it means:**
    - BoW or TF-IDF embeddings of text features may improve model performance.
    - Experiment with n-gram range (bigrams, trigrams).
    - Engineer a feature for **Collaborations** (e.g., identifying "x" as a marker of
    brand partnerships).
    """
    )

    # Hashtag Usage Section
    st.header("Hashtag Usage")

    st.write("Hastags are an optional field when making a new listing.")

    base = (
        alt.Chart(data)
        .transform_calculate(
            "hashtag_usage", alt.expr.if_(alt.datum.hashtags == "missing", "no", "yes")
        )
        .transform_aggregate(
            count="count()", mean="mean(sold_price)", groupby=["hashtag_usage"]
        )
        .properties(height=200)
    )

    left = (
        base.mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta("count:Q", stack="normalize"),
            color=alt.Color("hashtag_usage:N").legend(
                title="hashtag usage", orient="none"
            ),
        )
        .properties(title="Hashtag Usage")
    )

    right = (
        base.mark_bar()
        .encode(
            x=alt.X("hashtag_usage:N").axis(None),
            y=alt.Y("mean:Q").axis(title="Average Sold Price", format="$.0f"),
            color=alt.Color("hashtag_usage:N").legend(None),
        )
        .properties(title="Sold Price by Hashtag Usage", width=200)
    )

    st.altair_chart((left | right).configure_title(anchor="middle"))

    st.write(
        """
    **What we see:**
    - A quarter of listings do not use hashtags.
    - Sold items without hashtags tend to be more expensive. This might suggest that
    high-end or luxury items, which already have strong brand recognition, do not rely
    on hashtags for visibility.

    **What it means:**
    - Engineer a feature for "Hashtag Usage".
    """
    )

    # Sentiment Analysis Section
    st.header("Sentiment Analysis")

    base = (
        alt.Chart(text_sentiment)
        .transform_bin(
            "description_sentiment_binned",
            "description_sentiment",
            alt.Bin(maxbins=20),
        )
        .properties(height=150)
    )

    top = (
        base.mark_bar()
        .encode(
            x=alt.X("description_sentiment_binned:Q").axis(title=None, labels=False),
            y=alt.Y("count():Q"),
            color=alt.value("#bab0ac"),
        )
        .properties(title="Description Sentiment Score Distribution", width=630)
    )

    bottom = (
        base.mark_circle()
        .encode(
            x=alt.X("description_sentiment_binned:Q").axis(
                title="Vader Compound Score (binned)", labelAngle=0, format=".1f"
            ),
            y=alt.Y("mean(sold_price):Q").axis(
                title="Average Sold Price", format="$.0f"
            ),
            color=alt.value("#e15759"),
            size="count():Q",
        )
        .properties(title="Sold Price by Description Sentiment Score")
    )

    bottom_reg = bottom.transform_regression(
        "description_sentiment_binned", "sold_price", method="poly", order=2
    ).mark_line()

    st.altair_chart(
        (top & bottom + bottom_reg)
        .resolve_scale(x="shared")
        .resolve_legend(size="independent")
        .configure_title(anchor="middle"),
        use_container_width=True,
    )

    st.write(
        """
        **What we see:**
        - Sellers prefer either neutral or positive descriptions.
        - On average, the sold price of items with neutral descriptions is higher than
        those with overly positive or negative sentiment. Neutral descriptions may be
        perceived as more factual and trustworthy by buyers.

        **What it means:**
        - Try using the sentiment score as a feature.
        - Experiment with different sentiment score calculation methods and explore text
        preprocessing techniques, such as handling negations ("never worn"), to improve
        sentiment extraction.
        - Consider testing deep learning sentiment models (e.g., BERT, RoBERTa) to see
        if they provide more nuanced insights compared to traditional sentiment analysis
        approaches.
        """
    )

    # Parts-of-Speech Section
    st.header("Parts-of-Speech")

    st.write(
        """
        - **POS Tag Distribution in High vs. Low Priced Listings**: We found no
        significant differences, suggesting that the type of language used (nouns,
        verbs, adjectives) does not directly influence sold price.
        - **Noun and Adjective Usage**: The usage of nouns and adjectives follows
        the same pattern as text feature length, with both showing a negative
        correlation to sold price, indicating that more detailed and descriptive
        listings do not necessarily result in higher prices.

        *Note*: Since the conclusions of this section mirror those of previous
        sections (e.g., text feature length) or lack insights, I have decided to
        omit the inclusion of plots here.
        """
    )
