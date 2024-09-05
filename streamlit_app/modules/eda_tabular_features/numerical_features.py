import altair as alt
import streamlit as st
from modules.visualization import draw_bar_chart


def display_numerical_features(data):

    st.header("Numerical Features")

    st.write(
        """
    Our dataset includes two numerical features:

    - Sold Price (target feature)
    - Photo Count
    """
    )

    # Sold Price Section
    st.subheader("Sold Price")

    chart = (
        draw_bar_chart(data, height=300, display="count")
        .encode(
            x=alt.X("sold_price:Q")
            .bin(maxbins=400)
            .axis(title="Sold Price (binned)", format="$.0f"),
        )
        .properties(title="Sold Price Distribution")
        .configure_title(anchor="middle")
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)

    st.write(
        """
    **What we see:**
    - Most items sell within $35-135.
    - The distribution is heavily skewed to the right with some very high-price
    outliers. Grailed even
    [publishes](https://www.grailed.com/drycleanonly/tags/most-expensive) a monthly list
    of the priciest items sold.

    **What it means:**
    - We should use metrics that handle outliers well (like RMSLE, WAPE).
    - Models assuming a normal distribution (like linear regression) may struggle.
    - A log transformation might help make the target variable more normal.
    - Extreme outliers may signal luxury sales, experimenting with separate models for
    different price ranges could be worthwhile.
    """
    )

    # Photo Count Section
    st.subheader("Photo Count")

    st.write(
        """
    Grailed UI doesn’t set a hard limit for the number of photos per listing (though at
    least one is required).
    According to an official Grailed account in [this Reddit thread](
    https://www.reddit.com/r/Grailed/comments/9wxbpr/is_there_now_a_cap_for_the_number_of_photos_per/),
    the maximum is 25 photos.
    """
    )

    base = (
        alt.Chart(data)
        .transform_aggregate(
            count="count()", mean="mean(sold_price)", groupby=["n_photos"]
        )
        .properties(height=150)
    )

    top = (
        base.mark_bar()
        .encode(
            x=alt.X("n_photos:Q").axis(title=None),
            y=alt.Y("count:Q").axis(title="Count of Records"),
            color=alt.value("#bab0ac"),
        )
        .properties(title="Photo Count Distribution")
    )

    bottom = (
        base.mark_circle()
        .encode(
            x=alt.X("n_photos:Q").axis(title="Photo Count").scale(domainMin=0),
            y=alt.Y("mean:Q").axis(format="$.0f"),
            color=alt.value("#76b7b2"),
            size="count:Q",
        )
        .properties(title="Sold Price by Photo Count")
    )

    bottom_reg = bottom.transform_regression("n_photos", "mean").mark_line()

    bottom_bar = (
        alt.Chart(data)
        .mark_errorbar(ticks=alt.TickConfig(width=5), extent="ci")
        .encode(
            x=alt.X("n_photos:Q").scale(domainMin=0),
            y=alt.Y("sold_price:Q").axis(title="Average Sold Price", format="$.0f"),
            color=alt.value("#FFFFFF"),
        )
    )

    st.altair_chart(
        (top & bottom + bottom_bar + bottom_reg)
        .resolve_scale(x="shared")
        .resolve_legend(size="independent")
        .configure_title(anchor="middle"),
        use_container_width=True,
    )

    st.write(
        """
    **What we see:**
    - Most listings have 5-10 photos.
    - The distribution is right-skewed.
    - There are anomalies (e.g., 0 photos) due to scraper limitations, with listings
    displayed as carousels.
    - There’s a positive correlation between the number of photos and sold price up to
    13 photos; after that, the trend gets inconsistent. This might mean that adding more
    photos has less impact on the price, or it could be because there are fewer listings
    with higher photo counts.

    **What it means:**
    - We should impute 0 photos with the median value.
    - The number of photos seems to have predictive value, but it might be better to
    treat it as an ordinal feature
    rather than purely numeric.
    """
    )
