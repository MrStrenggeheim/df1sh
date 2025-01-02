import os

import pandas as pd
import streamlit as st
import utils.data as data
import utils.style as style

DATA_FOLDER = "./data"


def main():

    st.title("Race Data Configuration")

    data_editor_nr = st.session_state.setdefault("data_editor_nr", 0)
    if "races_df" not in st.session_state:
        if os.path.exists(DATA_FOLDER + "/races.csv"):
            st.session_state.races_df = pd.read_csv(
                DATA_FOLDER + "/races.csv", parse_dates=["StartDate", "EndDate"]
            )
        else:
            os.makedirs(DATA_FOLDER, exist_ok=True)
            st.session_state.races_df = pd.DataFrame(
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
        st.session_state.races_df,
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
        key=f"data_editor_{data_editor_nr}",
    )

    col1, col2, _ = st.columns([1, 1, 1])
    with col1:
        save_button = st.button("Save to file")
    with col2:
        fetch_button = st.button("Fetch from API")

    if save_button:
        races_df.to_csv(DATA_FOLDER + "/races.csv", index=False)
        st.session_state.races_df = races_df
        st.success("Data saved.")
    if fetch_button:
        with st.spinner("Fetching data..."):
            st.session_state.races_df = data.get_races()
            st.session_state.data_editor_nr += 1
        st.rerun()


if __name__ == "__main__":
    style.set_page_config()
    main()
