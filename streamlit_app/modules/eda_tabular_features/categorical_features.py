import altair as alt
import streamlit as st
from modules.data_utils import get_unique_values
from modules.visualization import (
    draw_bar_chart,
    draw_distribution_price_chart,
    draw_interactive_distribution_price_chart,
    draw_pie_chart,
    draw_quantile_charts,
)


def display_categorical_features(data, q_low, q_high):
    unique_values = get_unique_values(data, ["department", "category"])

    department_selection = alt.selection_point(
        fields=["department"],
        bind=alt.binding_select(
            options=unique_values["department"], name="Department "
        ),
        value=unique_values["department"][0],
    )

    category_selection = alt.selection_point(
        fields=["category"],
        bind=alt.binding_select(options=unique_values["category"], name="Category "),
        value=unique_values["category"][0],
    )

    st.header("Categorical Features")

    st.write(
        """
    Our dataset includes seven categorical features:
    - Designer
    - Department
    - Category
    - Subcategory
    - Color
    - Size
    - Condition
    """
    )

    # Cardinality Section
    st.subheader("Unique Values")

    cat_features = [
        "designer",
        "color",
        "subcategory",
        "size",
        "category",
        "condition",
        "department",
    ]

    for col, feature in zip(st.columns(len(cat_features)), cat_features):
        with col:
            n_unique = data[feature].nunique()
            st.metric(value=n_unique, label=f"{feature}")

    st.write(
        """
    **What we see:**
    - High-cardinality features: designer, color, subcategory, size.
    - Low-cardinality features: category, condition, department.

    **What it means:**
    - Target encoding is a good fit for high-cardinality features, one-hot encoding is
    better for low-cardinality features.
    - Grouping less frequent designers/colors into an "Other" category might reduce
    noise.
    """
    )

    # Designer Section
    st.subheader("Designer")

    st.write(
        """
        When listing an item, sellers pick a designer from a dropdown menu. New
        designers can be added by request, which means handling unseen designers is
        important for model robustness.
    """
    )

    st.altair_chart(
        draw_quantile_charts(
            data,
            "designer",
            q_low=q_low,
            q_high=q_high,
            title="Top 10 Designers by Sold Price",
        )
    )

    st.write(
        """
    **What we see:**
    - **25% most expensive sold items:** The top 10 designers include luxury brands
    (Louis Vuitton, Dior) and community favorites (Chrome Hearts, Supreme).
    - **25% least expensive sold items:** The top 10 designers feature mass-market
    brands (Nike, Adidas) and generic names like "Streetwear" and "Japanese Brand".
    - Among the 25% most expensive sold items, there is greater variation in average
    sold prices, indicating that luxury brands have a wider price range compared to
    mass-market brands.
    - "Vintage" is popular in both categories.

    **What it means:**
    - Designer is a strong predictor given the price differences.
    - Given the price differences between luxury and mass-market brands, separate
    models or preprocessing for these categories could improve performance by allowing
    the model to better capture the distinct pricing behaviors of each group.
    """
    )

    # Department Section
    st.subheader("Department")

    st.altair_chart(
        draw_distribution_price_chart(data, "department"), use_container_width=True
    )

    st.write(
        """
    **What we see:**
    - Menswear overwhelmingly dominates the platform, accounting for about 95% of
    listings.
    - Womenswear items tend to have higher average prices, likely due to higher-priced
    categories (e.g., designer bags) but remain underrepresented.

    **What it means:**
    - Separate models or metrics for menswear and womenswear could improve performance,
    given the distinct price ranges and limited data available for womenswear.
    - For now, menswear is likely the best focus for robust modeling, though more data
    on womenswear could help in the future.
    """
    )

    with st.expander("Why So Little Womenswear on Grailed?"):
        st.write(
            """
        From its founding in 2013, Grailed was a menswear-only platform. Between 2017
        and 2021, the team operated Heroine, a womenswear offshoot. After Heroine was
        closed in December 2021, Grailed introduced a womenswear section in October
        2022.

        As Grailed continues to expand its womenswear offerings following the October
        2022 reintroduction, we may see more growth in this category, leading to a more
        balanced distribution over time. However, the secondhand womenswear market
        remains highly competitive (Vestiaire Collective, Depop, The RealReal, etc.).
        """
        )

    # Category Section
    st.subheader("Category")

    left = (
        draw_pie_chart(data, width=400)
        .add_params(department_selection)
        .transform_filter(department_selection)
        .transform_aggregate(count="count()", groupby=["category"])
        .transform_joinaggregate(total="sum(count)")
        .transform_calculate(percentage="datum.count / datum.total")
        .encode(
            color=alt.Color("category:N").legend(title=None, orient="none"),
            tooltip=["category", alt.Tooltip("percentage:Q", format=".0%")],
        )
        .properties(title="Category Distribution")
    )

    right = (
        draw_bar_chart(data, direction="horizontal")
        .add_params(department_selection)
        .transform_filter(department_selection)
        .encode(y=alt.Y("category:N").axis(title=None, labelAngle=0).sort("-x"))
        .properties(title="Sold Price by Category")
    )

    st.altair_chart(
        alt.hconcat(left, right).properties(spacing=0).configure_title(anchor="middle"),
        use_container_width=True,
    )

    st.write(
        """
    **What we see:**
    - Grailed uses different category structures for menswear and womenswear (e.g.,
    menswear has tailoring, while womenswear has dresses).
    - Some categories (e.g., tailoring, jewelry) are underrepresented.
    - There’s significant variation in average sold price across categories for both
    departments.

    **What it means:**
    - Predictions might be less accurate for underrepresented categories like tailoring
    and jewelry, so gathering more data or applying techniques like upsampling could
    help.
    - Category is a strong predictor of price, with categories like footwear and
    outerwear typically commanding higher retail prices.
    """
    )

    # Subcategory Section
    st.subheader("Subcategory")

    draw_interactive_distribution_price_chart(
        data,
        "subcategory",
        alt.SortField("mean", "descending"),
        category_selection,
        department_selection,
        270,
        200,
    )

    st.write(
        """
    **What we see:**
    - Some subcategories (e.g., ties, pocket squares) are underrepresented.
    - There’s notable variation in average sold prices within categories. For example,
    leather jackets tend to sell for more than cloaks or capes, which can skew category
    averages.

    **What it means:**
    - Underrepresented subcategories might lead to less accurate predictions. Grouping
    similar subcategories could improve model performance.
    - The variation in sold prices indicates good predictive potential.
    """
    )

    # Size Section
    st.subheader("Size")

    size_order = (
        [str(i) for i in range(47)]
        + ["XXS", "XS", "S", "M", "L", "XL", "XXL, 3XL, 4XL"]
        + [str(i) + j for i in range(34, 55, 2) for j in ["S", "R", "L"]]
        + ["ONE_SIZE"]
    )

    draw_interactive_distribution_price_chart(
        data, "size", size_order, category_selection, department_selection, 300, 250
    )

    st.write(
        """
    **What we see:**
    - Some categories (e.g., bags and luggage) don’t have size charts.
    - Given menswear accessories subcategory structure, accessories size chart provided
    by Grailed can be misleading.
    - Sizes at the extremes of the size chart are underrepresented.
    - There are different size charts within a single size feature.
    - Mid-range sizes generally sell for more than sizes at the extremes.

    **What it means:**
    - Scaling sizes to a 0 to 1 range can help models better handle different size
    charts.
    - Underrepresented sizes at the extremes might need more data or specific handling,
    such as upsampling, to improve prediction accuracy.
    - Replace menswear accessories sizes with "ONE SIZE".
    """
    )

    # Color Section
    st.subheader("Color")

    st.write(
        """
    Sellers can enter any color name when listing an item, though suggestions appear as
    they type. Therefore, handling unseen colors is key.
    """
    )

    st.altair_chart(
        draw_quantile_charts(
            data,
            "color",
            q_low=q_low,
            q_high=q_high,
            title="Top 10 Designers by Sold Price",
        )
    )

    st.write(
        """
    **What we see:**
    - Black is the most popular color by far (especially in the 25% most expensive sold
    items).
    - Colors do not differ significantly between the 25% most and 25% least expensive
    sold items (beige is common among the most expensive, multicolor among the least).
    - While most colors don’t show significant differences in average sold prices,
    silver stands out, likely due to its association with high-value jewelry items.

    **What it means:**
    - In later experiments, treating color as a text feature and extracting embeddings
    could be interesting.
    - Silver might require special handling due to its association with high-value
    jewelry items. Feature engineering techniques like creating a binary flag for silver
    or applying target encoding for color could improve predictions.
    """
    )

    # Condition Section
    st.subheader("Condition")

    st.altair_chart(
        draw_distribution_price_chart(data, "condition"), use_container_width=True
    )

    st.write(
        """
    **What we see:**
    - About 25% of items are new, likely due to resellers.
    - Only 1% of items are well-worn.
    - Condition has a big impact on price — better condition means higher prices.

    **What it means:**
    - Ordinal encoding is the best approach here, given the clear order of conditions.
    Gathering more data on well-worn items could help improve predictions, and using
    techniques like target encoding might offer additional insights into price patterns
    across conditions.
    """
    )
