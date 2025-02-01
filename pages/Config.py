import os

import streamlit as st
from utils import Drivers, Races, Results, Teams, data, func, style

DATA_FOLDER = "./data"


def main():
    with st.sidebar:
        st.selectbox(
            "Fetch from ...",
            ["Current"] + data.get_available_years(),
            key="year_to_fetch",
        )
    # Ensure the base directory exists
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    if "seasons" not in st.session_state:
        func.refresh_seasons()
    saved_seasons = st.session_state.seasons

    season_control_cols = st.columns([4, 1, 1, 1], vertical_alignment="bottom")

    with season_control_cols[0]:
        st.title("Config")
    with season_control_cols[1]:
        with st.popover("Create New Season", use_container_width=True):
            new_season_name = st.text_input(
                "Name of the new season",
                key="new_season_name_field",
            )
            if st.button("Create Season", key="create_season_button"):
                func.create_season(new_season_name)
                st.success(f"New season '{new_season_name}' created successfully.")
                func.refresh_seasons()
                st.rerun()
    with season_control_cols[2]:
        selected_season = st.selectbox(
            "Select Season",
            saved_seasons,
            key="select_season",
            label_visibility="collapsed",
            disabled=not saved_seasons,
        )
    with season_control_cols[3]:
        with st.popover(
            "Delete Season", use_container_width=True, disabled=not saved_seasons
        ):
            if selected_season:
                if st.button(
                    f"Delete Season {selected_season}?",
                    use_container_width=True,
                    disabled=not saved_seasons,
                ):
                    func.delete_season(selected_season)
                    st.success(f"Season '{selected_season}' deleted!")
                    # delete all sesion state entries with the deleted season in key
                    for key in st.session_state.keys():
                        if selected_season in key:
                            print(f"Deleting {key}")
                            del st.session_state[key]
                    func.refresh_seasons()
                    st.rerun()

    if not saved_seasons:
        st.info("Please create a new season.")
        st.stop()

    # tabs for races, teams, drivers, results
    tabs = st.tabs(["Races", "Teams", "Drivers", "Results"])

    data_folder = os.path.join(DATA_FOLDER, selected_season)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with tabs[0]:
        Races.main(data_folder, selected_season)
    with tabs[1]:
        Teams.main(data_folder, selected_season)
    with tabs[2]:
        Drivers.main(data_folder, selected_season)
    with tabs[3]:
        Results.main(data_folder, selected_season)


if __name__ == "__main__":
    style.set_page_config()
    main()
