import streamlit as st


st.markdown(
    """
    # Graildient Descent: Predicting Sold Prices on Grailed

    > **TL;DR:** I’m scraping listings from Grailed and building an ML service to
      predict item sold prices. Stay tuned for updates!

    This is me throwing fits:
    """
)

images = [
    "https://storage.yandexcloud.net/graildient-descent-assets/intro/kirill_layered_lawyer.jpeg",
    "https://storage.yandexcloud.net/graildient-descent-assets/intro/kirill_weekend_warrior.jpeg",
    "https://storage.yandexcloud.net/graildient-descent-assets/intro/kirill_reckless_racqueteer.jpeg",
]
captions = [
    "Layered Lawyer: Beams Plus tweed jacket, Jamieson’s Fair Isle vest, Polo Ralph Lauren knit tie.",
    "Weekend Warrior: Gitman Vintage camp collar shirt, Beams Plus ankle-cut Ivy trousers.",
    "Reckless Racqueteer: Polo Ralph Lauren fun shirt, Beams Plus cricket vest, British Royal Navy pleat shorts.",
]

for col, image, caption in zip(st.columns(len(images)), images, captions, strict=True):
    with col:
        st.image(image, caption=caption)

st.markdown(
    """
    Almost everything I’m wearing here (and most of my closet) is from
    [Grailed](https://www.grailed.com/), an online marketplace where you can find
    high-end, pre-owned, and limited edition fashion pieces.

    Why Grailed? It’s all about sustainable fashion and discovering rare finds at a
    fraction of the original price.

    Since I’ve spent way too much time on Grailed, I figured it was the perfect
    opportunity to put my newly minted Data Science skills to use. Over the past year in
    the HSE University AI Master’s program, I’ve been learning how to build full-cycle
    ML services. So I decided to predict the selling prices of items on Grailed — from
    scraping the data to deploying and monitoring the model.

    Let me know what you think! And hey, if you’re from Grailed — I’m totally open to
    being hired. 😉
    """
)
