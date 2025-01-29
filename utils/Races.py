import os

import pandas as pd
import streamlit as st
from utils import data, style


def main(data_folder, selected_season):
    DATA_FOLDER = data_folder

    st.title(f"Race Data Configuration - {selected_season}")

    races_data_editor_nr = st.session_state.setdefault("races_data_editor_nr", 0)
    if f"races_df_{DATA_FOLDER}" not in st.session_state:
        if os.path.exists(DATA_FOLDER + "/races.csv"):
            st.session_state[f"races_df_{DATA_FOLDER}"] = pd.read_csv(
                DATA_FOLDER + "/races.csv", parse_dates=["StartDate", "EndDate"]
            )
        else:
            st.session_state[f"races_df_{DATA_FOLDER}"] = pd.DataFrame(
                columns=[
                    "Index",
                    "StartDate",
                    "EndDate",
                    "Country",
                    "City",
                    "Circuit",
                    "HasSprint",
                ]
            )

    st.header("Edit Races")
    races_df = st.data_editor(
        st.session_state[f"races_df_{DATA_FOLDER}"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Index": st.column_config.NumberColumn(
                "Index", required=True, disabled=True, width="small"
            ),
            "StartDate": st.column_config.DateColumn(
                "StartDate", required=True, format="YYYY-MM-DD"
            ),
            "EndDate": st.column_config.DateColumn(
                "EndDate", required=True, format="YYYY-MM-DD"
            ),
        },
        key=f"races_editor_{DATA_FOLDER}_{races_data_editor_nr}",
    )

    col1, col2, _ = st.columns([1, 1, 1])
    with col1:
        save_button = st.button("Save Races to file")
    with col2:
        fetch_button = st.button("Fetch Races from API")

    if save_button:
        races_df.to_csv(DATA_FOLDER + "/races.csv", index=False)
        st.session_state[f"races_df_{DATA_FOLDER}"] = races_df
        st.success("Data saved.")
    if fetch_button:
        with st.spinner("Fetching data..."):
            st.session_state[f"races_df_{DATA_FOLDER}"] = data.get_races()
            st.session_state.races_data_editor_nr += 1
        st.rerun()


if __name__ == "__main__":
    style.set_page_config()
    main()
