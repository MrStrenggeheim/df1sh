import streamlit as st

CUSTOM_CSS = """
<style>
    .message-p {
        font-size: 18px;
        padding: 0;
        margin-bottom: 0;
    }
    
    #next-race-name {
        font-size: 36px;
        color: #007acc;
    }
    
    .message-div {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
    }
</style>
"""


def set_page_config():
    st.set_page_config(
        page_title="DF1SH",
        page_icon=":racing_car:",
        initial_sidebar_state="expanded",
        layout="wide",
    )
    # st.logo("./assets/test.png", size="large")

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    return None


NEXT_RACE_HTML = """
<div class="message-div">
    <p class="message-p">Next Race</p>
    <p class="message-p" id="next-race-name">{next_race}</p>
    <p class="message-p">Starts in <strong style="color: #d9534f;">{days_left} days</strong></p>
</div>
"""

NO_UPCOMING_RACE_HTML = """
<div class="message-div">
    <p class="message-p">No Upcoming Races</p>
</div>
"""
