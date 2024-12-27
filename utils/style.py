import streamlit as st


def set_page_config():
    st.set_page_config(
        page_title="DF1SH",
        page_icon=":racing_car:",
        initial_sidebar_state="expanded",
        layout="wide",
    )
    # st.logo("./assets/test.png", size="large")

    css = """
img[data-testid="stLogo"] {
        height: 3.5rem;
}"""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    return None
