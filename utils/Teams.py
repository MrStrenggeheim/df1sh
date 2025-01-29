import os

import pandas as pd
import streamlit as st
from utils import data, style


def main(data_folder, selected_season):
    DATA_FOLDER = data_folder
    st.title(f"Team Data Configuration - {selected_season}")

    teams_data_editor_nr = st.session_state.setdefault("teams_data_editor_nr", 0)
    if f"teams_df_{DATA_FOLDER}" not in st.session_state:
        if os.path.exists(DATA_FOLDER + "/teams.csv"):
            st.session_state[f"teams_df_{DATA_FOLDER}"] = pd.read_csv(
                DATA_FOLDER + "/teams.csv"
            )
        else:
            st.session_state[f"teams_df_{DATA_FOLDER}"] = pd.DataFrame(
                columns=["TeamName", "Color"]
            )

    st.header("Edit Teams")
    teams_df = st.data_editor(
        st.session_state[f"teams_df_{DATA_FOLDER}"],
        num_rows="dynamic",
        use_container_width=True,
        key=f"teams_editor_{DATA_FOLDER}_{teams_data_editor_nr}",
    )

    col1, col2, _ = st.columns([1, 1, 1])
    with col1:
        save_button = st.button("Save Teams to file")
    with col2:
        fetch_button = st.button("Fetch Teams from API")

    if save_button:
        teams_df.to_csv(DATA_FOLDER + "/teams.csv", index=False)
        st.session_state[f"teams_df_{DATA_FOLDER}"] = teams_df
        st.success("Data saved.")
    if fetch_button:
        with st.spinner("Fetching data..."):
            st.session_state[f"teams_df_{DATA_FOLDER}"] = data.get_teams()
            st.session_state.teams_data_editor_nr += 1
        st.rerun()


if __name__ == "__main__":
    style.set_page_config()
    main()
