import requests
import streamlit as st
from modules.config import (
    API_ENDPOINT_URL,
    categories,
    conditions,
    departments,
    sizes,
    subcategories,
)


def subcategories_options(department, category):
    if department and category:
        return subcategories[department][category]
    return None


def sizes_options(department, category):
    if department and category:
        return sizes[department][category]
    return None


def submit_listing_form():
    if not all(
        [
            department,
            category,
            subcategory,
            condition,
            size,
            designer,
            color,
            item_name,
            description,
        ]
    ):
        st.error("Please fill in all required fields")
        return None

    if hashtags and len(hashtags.split()) > 10:
        st.error("Please remove some hashtags")
        return None

    return {
        "department": department,
        "category": category,
        "subcategory": subcategory,
        "condition": condition,
        "size": size,
        "designer": designer,
        "color": color,
        "n_photos": n_photos,
        "item_name": item_name,
        "description": description,
        "hashtags": hashtags if hashtags else None,
    }


def format_designer_name(designer: str) -> str:
    """Format designer name for API submission."""
    designer = designer.strip().lower()
    return "-".join(designer.split())


def validate_hashtags(hashtags: str):
    """Validate hashtags."""
    if len(hashtags.split()) > 10:
        st.warning("Maximum 10 hashtags allowed")


def get_prediction(listing_data: dict) -> dict:
    """Handle API prediction request with error handling."""
    try:
        response = requests.post(API_ENDPOINT_URL, json=listing_data)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            st.error("Validation Error: " + str(response.json()["detail"]))
        else:
            st.error(f"Server Error ({response.status_code})")
    except requests.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
    return None


def update_prediction_history(prediction: dict, listing_data: dict):
    if len(st.session_state.predictions) >= 10:  # Keep last 10 predictions
        st.session_state.predictions.pop(0)
    st.session_state.predictions.append(
        {
            "item": listing_data["item_name"],
            "price": prediction["predicted_price"],
        }
    )


prediction = None

st.title("Grailed Price Predictor")
st.write(
    """
Fill out the form below to get a predicted price for your Grailed listing.
All fields except hashtags are required.
"""
)

with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        department = st.selectbox(
            "Department",
            options=departments,
            help="Choose the department for your listing",
            index=None,
        )

        category = st.selectbox(
            "Category",
            options=categories.get(department),
            help="Select the main category of your item",
            index=None,
        )

        subcategory = st.selectbox(
            "Subcategory",
            options=subcategories_options(department, category),
            help="Select the specific subcategory of your item",
            index=None,
        )

        condition = st.selectbox(
            "Condition",
            options=conditions,
            help="Select the condition of your item",
            index=None,
        )

        size = st.selectbox(
            "Size",
            options=sizes_options(department, category),
            help="Select the size of your item",
            index=None,
        )

    with col2:
        designer = st.text_input(
            "Designer", help="Enter the designer/brand name", max_chars=50
        )

        color = st.text_input(
            "Color", help="Enter the primary color of the item", max_chars=30
        )

        n_photos = st.number_input(
            "Number of Photos",
            min_value=1,
            max_value=25,
            value=1,
            help="Enter the number of photos (1-25)",
        )

    item_name = st.text_input(
        "Item Name", help="Enter name of your item (max 60 characters)", max_chars=60
    )

    description = st.text_area(
        "Description", help="Enter a detailed description of your item", height=100
    )
    hashtags = st.text_input(
        "Hashtags",
        help="Enter hashtags separated by spaces (optional, max 10 hashtags)",
    )
    validate_hashtags(hashtags)

    if st.button("Predict", use_container_width=True):
        listing_data = submit_listing_form()
        if listing_data:
            with st.spinner("Estimating price..."):
                prediction = get_prediction(listing_data)
                if prediction:
                    st.success(f"Predicted Price: ${prediction['predicted_price']:.0f}")


# Add price history tracking
if "predictions" not in st.session_state:
    st.session_state.predictions = []

if prediction:
    update_prediction_history(prediction, listing_data)

# Show prediction history
if st.session_state.predictions:
    with st.expander("Previous Predictions"):
        for p in st.session_state.predictions[::-1]:
            st.write(f"{p['item']}: ${p['price']:.0f}")
