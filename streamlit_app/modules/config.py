import streamlit as st


def generate_size_range(start: int, end: int) -> list[str]:
    """Generate a range of sizes as strings."""
    return [str(i) for i in range(start, end + 1)]


API_ENDPOINT_URL = f"{st.secrets.api.base_url}{st.secrets.api.predictions_form}"

departments = ["menswear", "womenswear"]

categories = {
    "menswear": [
        "accessories",
        "bottoms",
        "footwear",
        "outerwear",
        "tailoring",
        "tops",
    ],
    "womenswear": [
        "accessories",
        "bags-luggage",
        "bottoms",
        "dresses",
        "footwear",
        "jewelry",
        "outerwear",
        "tops",
    ],
}

subcategories = {
    "menswear": {
        "accessories": [
            "bags-luggage",
            "belts",
            "glasses",
            "gloves-scarves",
            "hats",
            "jewelry-watches",
            "wallets",
            "miscellaneous",
            "periodicals",
            "socks-underwear",
            "sunglasses",
            "supreme",
            "ties-pocketsquares",
        ],
        "bottoms": [
            "casual-pants",
            "cropped-pants",
            "denim",
            "leggings",
            "overalls-jumpsuits",
            "shorts",
            "sweatpants-joggers",
            "swimwear",
        ],
        "footwear": [
            "boots",
            "casual-leather-shoes",
            "formal-shoes",
            "hi-top-sneakers",
            "low-top-sneakers",
            "sandals",
            "slip-ons",
        ],
        "outerwear": [
            "bombers",
            "cloaks-capes",
            "denim-jackets",
            "heavy-coats",
            "leather-jackets",
            "light-jackets",
            "parkas",
            "raincoats",
            "vests",
        ],
        "tailoring": [
            "blazers",
            "formal-shirting",
            "formal-trousers",
            "suits",
            "tuxedos",
            "vests",
        ],
        "tops": [
            "long-sleeve-t-shirts",
            "polos",
            "shirts-button-ups",
            "short-sleeve-t-shirts",
            "sweaters-knitwear",
            "sweatshirts-hoodies",
            "tank-tops-sleeveless",
            "jerseys",
        ],
    },
    "womenswear": {
        "accessories": [
            "belts",
            "glasses",
            "gloves",
            "hair-accessories",
            "hats",
            "miscellaneous",
            "scarves",
            "socks-intimates",
            "sunglasses",
            "wallets",
            "watches",
        ],
        "bags-luggage": [
            "backpacks",
            "belt-bags",
            "bucket-bags",
            "clutches",
            "crossbody-bags",
            "handle-bags",
            "hobo-bags",
            "luggage-travel",
            "messengers-satchels",
            "mini-bags",
            "shoulder-bags",
            "toiletry-pouches",
            "tote-bags",
            "other",
        ],
        "bottoms": [
            "jeans",
            "joggers",
            "jumpsuits",
            "leggings",
            "maxi-skirts",
            "midi-skirts",
            "mini-skirts",
            "pants",
            "shorts",
            "sweatpants",
        ],
        "dresses": ["mini-dresses", "midi-dresses", "maxi-dresses", "gowns"],
        "footwear": [
            "boots",
            "heels",
            "platforms",
            "mules",
            "flats",
            "hi-top-sneakers",
            "low-top-sneakers",
            "sandals",
            "slip-ons",
        ],
        "jewelry": [
            "body-jewelry",
            "bracelets",
            "brooches",
            "charms",
            "cufflinks",
            "earrings",
            "necklaces",
            "rings",
        ],
        "outerwear": [
            "blazers",
            "bombers",
            "coats",
            "denim-jackets",
            "down-jackets",
            "fur-faux-fur",
            "jackets",
            "leather-jackets",
            "rain-jackets",
            "vests",
        ],
        "tops": [
            "blouses",
            "bodysuits",
            "button-ups",
            "crop-tops",
            "hoodies",
            "long-sleeve-t-shirts",
            "polos",
            "short-sleeve-t-shirts",
            "sweaters",
            "sweatshirts",
            "tank-tops",
        ],
    },
}

conditions = ["New", "Gently Used", "Used", "Worn"]

# Size Constants
ONE_SIZE = ["ONE SIZE"]
STANDARD_SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL"]
EXTENDED_SIZES = STANDARD_SIZES + ["3XL", "4XL", ONE_SIZE]

sizes = {
    "menswear": {
        "accessories": ONE_SIZE,
        "bottoms": generate_size_range(26, 44),
        "footwear": generate_size_range(5, 15),
        "outerwear": STANDARD_SIZES,
        "tailoring": [f"{i}{j}" for i in range(34, 55, 2) for j in ("S", "R", "L")],
        "tops": STANDARD_SIZES,
    },
    "womenswear": {
        "accessories": ONE_SIZE,
        "bags-luggage": ONE_SIZE,
        "bottoms": generate_size_range(22, 42),
        "dresses": EXTENDED_SIZES,
        "footwear": generate_size_range(4, 12),
        "jewelry": ONE_SIZE,
        "outerwear": EXTENDED_SIZES,
        "tops": EXTENDED_SIZES,
    },
}
