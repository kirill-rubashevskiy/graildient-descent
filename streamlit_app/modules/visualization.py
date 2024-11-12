import altair as alt
import pandas as pd
import streamlit as st


def draw_pie_chart(
    data: pd.DataFrame, height: int = 200, width: int = 200
) -> alt.Chart:
    """
    Generate a pie chart for visualizing distributions.

    Parameters:
    data: The dataframe containing the data to plot.
    height: The height of the chart.
    width: The width of the chart.

    Returns:
    An Altair pie chart object.
    """
    return (
        alt.Chart(data)
        .mark_arc(innerRadius=50)
        .encode(theta="percentage:Q", color=alt.value("#bab0ac"))
        .properties(height=height, width=width)
    )


def draw_bar_chart(
    data: pd.DataFrame,
    direction: str = "vertical",
    display: str = "price",
    color: str = "#bab0ac",
    height: int = 200,
    width: int = 200,
) -> alt.Chart:
    """
    Generate a bar chart for visualizing distributions or averages.

    Parameters:
    data: The dataframe containing the data to plot.
    direction: The direction of the bar chart ('vertical' or 'horizontal').
    display: Whether to display the price ('price') or count ('count').
    color: Color for the bars in the chart.
    height: The height of the chart.
    width: The width of the chart.

    Returns:
    An Altair bar chart object.
    """
    chart = alt.Chart(data).properties(height=height, width=width)
    axis = (
        alt.Y("mean(sold_price):Q").axis(title="Average Sold Price", format="$.0f")
        if display == "price"
        else alt.Y("count()")
    )

    if direction == "vertical":
        return chart.mark_bar().encode(y=axis, color=alt.value(color))
    return chart.mark_bar().encode(x=axis, color=alt.value(color))


def draw_quantile_chart(
    data: pd.DataFrame,
    feature: str,
    price_filter: alt.expr,
    yaxis_title: str,
    xaxis: bool = True,
    width: int = 270,
    height: int = 150,
) -> tuple[alt.Chart, alt.Chart, alt.Chart]:
    """
    Draw a quantile-based chart showing the count and mean sold price for a given
    feature.

    Parameters:
    data: The dataframe containing the data to plot.
    feature: The categorical feature to visualize.
    price_filter: The filter condition applied to the price data.
    yaxis_title: Title for the y-axis of the chart.
    xaxis: Whether to show the x-axis (True or False).
    width: The width of each individual chart component.
    height: The height of each individual chart component.

    Returns:
    A tuple of three Altair chart objects: count chart, middle text chart, and mean sold
    price chart.
    """

    base = (
        alt.Chart(data)
        .transform_filter(price_filter)
        .transform_aggregate(
            mean="mean(sold_price)", count="count()", groupby=[f"{feature}"]
        )
        .transform_window(
            rank=f"row_number({feature})",
            sort=[alt.SortField("count", order="descending")],
        )
        .transform_filter(alt.datum.rank <= 10)
        .mark_bar()
        .encode(
            y=alt.Y(f"{feature}:N")
            .sort(alt.SortField("count", "descending"))
            .axis(None),
        )
        .properties(height=height, width=width)
    )

    left_xaxis = (
        alt.Axis(title="Count of Records")
        if xaxis
        else alt.Axis(title=None, labels=False)
    )
    right_xaxis = (
        alt.Axis(title="Average Sold Price", format="$.0f")
        if xaxis
        else alt.Axis(title=None, labels=False)
    )

    left = base.encode(
        x=alt.X("count:Q", axis=left_xaxis).sort("descending"),
        y=alt.Y(f"{feature}:N")
        .sort(alt.SortField("count", "descending"))
        .axis(title=yaxis_title, labels=False),
        color=alt.value("#bab0ac"),
    )

    middle = (
        base.encode(alt.Text(f"{feature}:N"), color=alt.value("white"))
        .mark_text()
        .properties(width=20)
    )

    right = base.encode(
        x=alt.X("mean:Q", axis=right_xaxis),
        color=alt.value("#76b7b2"),
    )

    return left, middle, right


def draw_quantile_charts(
    data: pd.DataFrame, feature: str, q_low: float, q_high: float, title: str
) -> alt.HConcatChart:
    """
    Draw a combined chart for quantile-based visualization of count and mean sold price
    across the top 25% and bottom 25% listings.

    Parameters:
    data: The dataframe containing the data to plot.
    feature: The categorical feature to visualize.
    q_low: The quantile threshold for the bottom listings (e.g., 0.25 for bottom 25%).
    q_high: The quantile threshold for the top listings (e.g., 0.75 for top 25%).
    title: The title of the chart.

    Returns:
    An Altair chart object combining top and bottom quantile charts.
    """

    top_left, top_middle, top_right = draw_quantile_chart(
        data,
        feature,
        alt.datum.sold_price > q_high,
        xaxis=False,
        yaxis_title="Top 25% Listings",
    )

    bottom_left, bottom_middle, bottom_right = draw_quantile_chart(
        data,
        feature,
        alt.datum.sold_price < q_low,
        yaxis_title="Bottom 25% Listings",
    )

    return (
        (
            (top_left & bottom_left).resolve_scale(x="shared")
            | (top_middle & bottom_middle)
            | (top_right & bottom_right).resolve_scale(x="shared")
        )
        .properties(title=title)
        .configure_title(anchor="middle")
    )


def draw_distribution_price_chart(data: pd.DataFrame, feature: str) -> alt.HConcatChart:
    """
    Draw a pie chart and bar chart for the distribution and mean sold price of a feature.

    Parameters:
    data: The dataframe containing the data to plot.
    feature: The categorical feature to visualize.

    Returns:
    An Altair chart object combining left distribution and right mean sold price charts.
    """
    left = (
        draw_pie_chart(data, width=400)
        .transform_aggregate(count="count()", groupby=[feature])
        .transform_joinaggregate(total="sum(count)")
        .transform_calculate(percentage="datum.count / datum.total")
        .encode(
            color=alt.Color(feature).legend(title=None, orient="none"),
            tooltip=[feature, alt.Tooltip("percentage:Q", format=".0%")],
        )
        .properties(title=f"{feature.capitalize()} Distribution")
    )

    right = (
        draw_bar_chart(data)
        .encode(
            x=alt.X(f"{feature}:N").sort("-y").axis(title=None, labelAngle=0),
            color=alt.value("#bab0ac"),
        )
        .properties(title=f"Sold Price by {feature.capitalize()}")
    )

    return alt.hconcat(left | right, spacing=0).configure_title(anchor="middle")


def draw_interactive_distribution_price_chart(
    data: pd.DataFrame,
    feature: str,
    sort_order: alt.SortField | str,
    category_selection: alt.Parameter,
    department_selection: alt.Parameter,
    width: int = 300,
    height: int = 250,
) -> alt.HConcatChart:
    """
    Draw an interactive bar chart displaying the distribution and mean sold price of a
    specified feature.

    This function generates a composite Altair chart consisting of three aligned bar
    charts:
    one for the count of records, one for the mean sold price, and a middle text label
    showing the feature names.
    The chart is interactive, allowing users to filter by department and category.

    Parameters:
    data: The dataframe containing the data to plot.
    feature: The categorical feature to visualize.
    sort_order: The sorting order for the y-axis based on a specified field.
    category_selection: An Altair Parameter object that allows filtering based on category.
    department_selection: An Altair Parameter object that allows filtering based on department.
    width: The width of each individual chart component.
    height: The height of each individual chart component.

    Returns:
    An Altair chart object.
    """
    base = (
        alt.Chart(data)
        .add_params(category_selection, department_selection)
        .transform_filter(department_selection & category_selection)
        .transform_aggregate(
            count="count()", mean="mean(sold_price)", groupby=[feature]
        )
        .encode(y=alt.Y(f"{feature}:N").sort(sort_order).axis(None))
        .properties(width=width, height=height)
    )
    left = (
        base.mark_bar()
        .encode(
            x=alt.X("count:Q").sort("descending").axis(title="Count of Records"),
            color=alt.value("#bab0ac"),
        )
        .properties(title=f"{feature.capitalize()} Distribution")
    )

    middle = (
        base.encode(alt.Text(f"{feature}:N"), color=alt.value("white"))
        .mark_text()
        .properties(width=20)
    )

    right = (
        base.mark_bar()
        .encode(
            x=alt.X("mean:Q").axis(title="Average Sold Price", format="$.0f"),
            color=alt.value("#76b7b2"),
        )
        .properties(title=f"Sold Price by {feature.capitalize()}")
    )

    return st.altair_chart(
        alt.hconcat(left | middle | right, spacing=0).configure_title(anchor="middle"),
        use_container_width=True,
    )


def draw_price_kde_chart(data: pd.DataFrame) -> alt.Chart:
    """
    Draw a Kernel Density Estimation (KDE) chart to visualize the distribution of
    sold prices across different data splits.

    Parameters:
    data: The DataFrame containing the data to plot, with 'sold_price' as the numerical
    feature and 'dataset' as the categorical feature indicating data splits (e.g., train, eval, test).

    Returns:
    An Altair chart object representing the KDE of sold prices, with separate density
    curves for each dataset category.
    """
    chart = (
        alt.Chart(data)
        .transform_density(
            "sold_price", as_=["sold_price", "density"], groupby=["dataset"]
        )
        .mark_area()
        .encode(x=alt.X("sold_price:Q"), y="density:Q", color="dataset")
        .properties(height=150)
    )

    return chart
