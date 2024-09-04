import streamlit as st


intro = st.Page("intro.py", title="Intro", default=True)

pg = st.navigation([intro])
st.set_page_config(page_title="Graildient Descent")

pg.run()
