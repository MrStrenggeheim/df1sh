import os

import pandas as pd
import streamlit as st
from utils import data, style


def main(data_folder, selected_season):
    DATA_FOLDER = data_folder
    st.title(f"Driver Data Configuration - {selected_season}")

    drivers_data_editor_nr = st.session_state.setdefault("drivers_data_editor_nr", 0)
    if f"drivers_df_{DATA_FOLDER}" not in st.session_state:
        if os.path.exists(DATA_FOLDER + "/drivers.csv"):
            st.session_state[f"drivers_df_{DATA_FOLDER}"] = pd.read_csv(
                DATA_FOLDER + "/drivers.csv"
            )
        else:
            st.session_state[f"drivers_df_{DATA_FOLDER}"] = pd.DataFrame(
                columns=["DriverName", "TeamName"]
            )
    try:
        df_teams = pd.read_csv(DATA_FOLDER + "/teams.csv")
    except FileNotFoundError:
        st.warning("Teams data not found. Please configure the data in the Teams tab.")
        st.stop()

    st.header("Edit Drivers")
    drivers_df = st.data_editor(
        st.session_state[f"drivers_df_{DATA_FOLDER}"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "TeamName": st.column_config.SelectboxColumn(
                "TeamName", options=df_teams["TeamName"].tolist(), required=True
            ),
        },
        key=f"driver_editor_{DATA_FOLDER}_{drivers_data_editor_nr}",
    )

    col1, col2, _ = st.columns([1, 1, 1])
    with col1:
        save_button = st.button("Save Drivers to file")
    with col2:
        fetch_button = st.button("Fetch Drivers from API")

    if save_button:
        drivers_df.to_csv(DATA_FOLDER + "/drivers.csv", index=False)
        st.session_state[f"drivers_df_{DATA_FOLDER}"] = drivers_df
        st.success("Data saved.")
    if fetch_button:
        with st.spinner("Fetching data..."):
            st.session_state[f"drivers_df_{DATA_FOLDER}"] = data.get_drivers(
                year_to_fetch=st.session_state.year_to_fetch
            )
            st.session_state.drivers_data_editor_nr += 1
        st.rerun()


if __name__ == "__main__":
    style.set_page_config()
    main()
