import os

import pandas as pd
import streamlit as st
from utils import data, style

DATA_FOLDER = "./data"


def main():
    st.title("Team Data Configuration")
    os.makedirs(DATA_FOLDER, exist_ok=True)

    data_editor_nr = st.session_state.setdefault("data_editor_nr", 0)
    if "teams_df" not in st.session_state:
        if os.path.exists(DATA_FOLDER + "/teams.csv"):
            st.session_state.teams_df = pd.read_csv(DATA_FOLDER + "/teams.csv")
        else:
            st.session_state.teams_df = pd.DataFrame(columns=["TeamName", "Color"])

    st.header("Edit Teams")
    df_teams = st.data_editor(
        st.session_state.teams_df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"data_editor_{data_editor_nr}",
    )

    col1, col2, _ = st.columns([1, 1, 1])
    with col1:
        save_button = st.button("Save to file")
    with col2:
        fetch_button = st.button("Fetch from API")

    if save_button:
        df_teams.to_csv(DATA_FOLDER + "/teams.csv", index=False)
        st.session_state.teams_df = df_teams
        st.success("Data saved.")
    if fetch_button:
        with st.spinner("Fetching data..."):
            st.session_state.teams_df = data.get_teams()
            st.session_state.data_editor_nr += 1
        st.rerun()


if __name__ == "__main__":
    style.set_page_config()
    main()
