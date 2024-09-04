import streamlit as st


st.title("Graildient Descent: Predicting Sold Prices on Grailed")

st.write(
    """
**TL;DR:** I’m scraping listings from Grailed and building an ML service to predict item sold prices.
Stay tuned for updates!
"""
)

st.write("This is me throwing fits:")

col1, col2, col3 = st.columns(3)

with col1:
    st.image(
        "https://storage.yandexcloud.net/graildient-descent-assets/intro/kirill-layered-lawyer.jpeg",
        caption="""
        Layered Lawyer: Beams Plus tweed jacket, Jamieson’s Fair Isle vest, Polo Ralph Lauren knit tie.
        """,
    )

with col2:
    st.image(
        "https://storage.yandexcloud.net/graildient-descent-assets/intro/kirill-weekend-warrior.jpeg",
        caption="""
        Weekend Warrior: Gitman Vintage camp collar shirt, Beams Plus ankle-cut Ivy trousers, Loake penny loafers (not shown).
        """,
    )

with col3:
    st.image(
        "https://storage.yandexcloud.net/graildient-descent-assets/intro/kirill-reckless-racqueteer.jpeg",
        caption="""
        Reckless Racqueteer: Polo Ralph Lauren fun shirt, Beams Plus cricket vest, British Royal Navy pleat shorts, Rowing Blazers Pierce & Pierce banker bag.
        """,
    )

st.write(
    """
Almost everything I’m wearing here (and most of my closet) is from Grailed, an online marketplace where you can find
high-end, pre-owned, and limited edition fashion pieces.

Why Grailed? It’s all about sustainable fashion and discovering rare finds at a fraction of the original price.

Since I’ve spent way too much time on Grailed, I figured it was the perfect opportunity to put my newly minted Data Science skills to use.
Over the past year in the HSE University AI Master’s program, I’ve been learning how to build full-cycle ML services.
So I decided to predict the selling prices of items on Grailed — from scraping the data to deploying and monitoring the
model.

Let me know what you think! And hey, if you’re from Grailed — I’m totally open to being hired. 😉
"""
)
