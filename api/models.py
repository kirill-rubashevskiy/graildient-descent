from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class Department(str, Enum):
    MENSWEAR = "menswear"
    WOMENSWEAR = "womenswear"


class Category(str, Enum):
    ACCESSORIES = "accessories"
    BAGS_LUGGAGE = "bags-luggage"
    BOTTOMS = "bottoms"
    DRESSES = "dresses"
    FOOTWEAR = "footwear"
    JEWELRY = "jewelry"
    OUTERWEAR = "outerwear"
    TAILORING = "tailoring"
    TOPS = "tops"


class Subcategory(str, Enum):
    # Accessories
    BAGS_LUGGAGE = "bags-luggage"
    BELTS = "belts"
    GLASSES = "glasses"
    GLOVES = "gloves"
    GLOVES_SCARVES = "gloves-scarves"
    HAIR_ACCESSORIES = "hair-accessories"
    HATS = "hats"
    JEWELRY_WATCHES = "jewelry-watches"
    MISCELLANEOUS = "miscellaneous"
    PERIODICALS = "periodicals"
    SCARVES = "scarves"
    SOCKS_INTIMATES = "socks-intimates"
    SOCKS_UNDERWEAR = "socks-underwear"
    SUNGLASSES = "sunglasses"
    SUPREME = "supreme"
    TIES_POCKETSQUARES = "ties-pocketsquares"
    WALLETS = "wallets"
    WATCHES = "watches"

    # Bags & Luggage
    BACKPACKS = "backpacks"
    BELT_BAGS = "belt-bags"
    BUCKET_BAGS = "bucket-bags"
    CLUTCHES = "clutches"
    CROSSBODY_BAGS = "crossbody-bags"
    HANDLE_BAGS = "handle-bags"
    HOBO_BAGS = "hobo-bags"
    LUGGAGE_TRAVEL = "luggage-travel"
    MESSENGERS_SATCHELS = "messengers-satchels"
    MINI_BAGS = "mini-bags"
    SHOULDER_BAGS = "shoulder-bags"
    TOILETRY_POUCHES = "toiletry-pouches"
    TOTE_BAGS = "tote-bags"
    OTHER = "other"

    # Bottoms
    CASUAL_PANTS = "casual-pants"
    CROPPED_PANTS = "cropped-pants"
    PANTS = "pants"
    DENIM = "denim"
    JEANS = "jeans"
    JOGGERS = "joggers"
    JUMPSUITS = "jumpsuits"
    LEGGINS = "leggins"
    MAXI_SKIRTS = "maxi-skirts"
    MIDI_SKIRTS = "midi-skirts"
    MINI_SKIRTS = "mini-skirts"
    OVERALLS_JUMPSUITS = "overalls-jumpsuits"
    SHORTS = "shorts"
    SWEATPANTS = "sweatpants"
    SWEATPANTS_JOGGERS = "sweatpants-joggers"
    SWIMWEAR = "swimwear"

    # Dresses
    MINI_DRESSES = "mini-dresses"
    MIDI_DRESSES = "midi-dresses"
    MAXI_DRESSES = "maxi-dresses"
    GOWNS = "gowns"

    # Footwear
    BOOTS = "boots"
    CASUAL_LEATHER_SHOES = "casual-leather-shoes"
    FLATS = "flats"
    FORMAL_SHOES = "formal-shoes"
    HEELS = "heels"
    HI_TOP_SNEAKERS = "hi-top-sneakers"
    LOW_TOP_SNEAKERS = "low-top-sneakers"
    MULES = "mules"
    PLATFORMS = "platforms"
    SANDALS = "sandals"
    SLIP_ONS = "slip-ons"

    # Jewelry
    BODY_JEWELRY = "body-jewelry"
    BRACELETS = "bracelets"
    BROOCHES = "brooches"
    CHARMS = "charms"
    CUFFLINKS = "cufflinks"
    EARRINGS = "earrings"
    NECKLACES = "necklaces"
    RINGS = "rings"

    # Outerwear
    BLAZERS = "blazers"
    BOMBERS = "bombers"
    CLOAKS_CAPES = "cloaks-capes"
    COATS = "coats"
    DENIM_JACKETS = "denim-jackets"
    DOWN_JACKETS = "down-jackets"
    FUR_FAUX_FUR = "fur-faux-fur"
    HEAVY_COATS = "heavy-coats"
    JACKETS = "jackets"
    LEATHER_JACKETS = "leather-jackets"
    LIGHT_JACKETS = "light-jackets"
    PARKAS = "parkas"
    RAIN_JACKETS = "rain-jackets"
    RAINCOATS = "raincoats"
    VESTS = "vests"

    # Tailoring
    # BLAZERS = "blazers"
    FORMAL_SHIRTING = "formal-shirting"
    FORMAL_TROUSERS = "formal-trousers"
    SUITS = "suits"
    TUXEDOS = "tuxesdos"
    # VESTS = "vests"

    # Tops
    BLOUSES = "blouses"
    BODYSUITS = "bodysuits"
    BUTTON_UPS = "button-ups"
    CROP_TOPS = "crop-tops"
    HOODIES = "hoodies"
    JERSEYS = "jersesys"
    LONG_SLEEVE_T_SHIRTS = "long-sleeve-t-shirts"
    POLOS = "polos"
    SHIRTS_BUTTON_UPS = "shirts-button-ups"
    SHORT_SLEEVE_T_SHIRTS = "short-sleeve-t-shirts"
    SWEATERS = "sweaters"
    SWEATERS_KNITWEAR = "sweaters-knitwear"
    SWEATSHIRTS = "sweatshirts"
    SWEATSHIRTS_HOODIES = "sweatshirts-hoodies"
    TANK_TOPS = "tank-tops"
    TANK_TOPS_SLEEVELESS = "tank-tops-sleeveless"


class Condition(str, Enum):
    NEW = "New"
    GENTLY_USED = "Gently Used"
    USED = "Used"
    WELL_WORN = "Worn"


class Size(str, Enum):
    # Tops, outerwear & accessories
    XXS = "XXS"
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    S3XL = "3XL"
    S4XL = "4XL"
    ONE_SIZE = "ONE SIZE"

    # Bottoms
    S22 = "22"
    S23 = "23"
    S24 = "24"
    S25 = "25"
    S26 = "26"
    S27 = "27"
    S28 = "28"
    S29 = "29"
    S30 = "30"
    S31 = "31"
    S32 = "32"
    S33 = "33"
    S34 = "34"
    S35 = "35"
    S36 = "36"
    S37 = "37"
    S38 = "38"
    S39 = "39"
    S40 = "40"
    S41 = "41"
    S42 = "42"
    S43 = "43"
    S44 = "44"

    # Footwear
    S4 = "4"
    S5 = "5"
    S6 = "6"
    S7 = "7"
    S8 = "8"
    S9 = "9"
    S10 = "10"
    S11 = "11"
    S12 = "12"
    S13 = "13"
    S14 = "14"
    S15 = "15"

    # Tailoring
    S34S = "34S"
    S34R = "34R"
    S34L = "34L"
    S36S = "36S"
    S36R = "36R"
    S36L = "36L"
    S38S = "38S"
    S38R = "38R"
    S38L = "38L"
    S40S = "40S"
    S40R = "40R"
    S40L = "40L"
    S42S = "42S"
    S42R = "42R"
    S42L = "42L"
    S44S = "44S"
    S44R = "44R"
    S44L = "44L"
    S46S = "46S"
    S46R = "46R"
    S46L = "46L"
    S48S = "48S"
    S48R = "48R"
    S48L = "48L"
    S50S = "50S"
    S50R = "50R"
    S50L = "50L"
    S52S = "52S"
    S52R = "52R"
    S52L = "52L"
    S54S = "54S"
    S54R = "54R"
    S54L = "54L"


class Listing(BaseModel):
    department: Department
    category: Category
    subcategory: Subcategory
    condition: Condition
    size: Size
    designer: str = Field(min_length=1)
    color: str = Field(min_length=1)
    n_photos: int = Field(gt=0, le=25)
    item_name: str = Field(min_length=1, max_length=60)
    description: str = Field(min_length=1)
    hashtags: Optional[str] = None


class ListingUrl(BaseModel):
    url: HttpUrl


class PredictionResponse(BaseModel):
    prediction_id: str
    predicted_price: float
    metadata: dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
