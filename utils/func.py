import os
import shutil

import streamlit as st

DATA_FOLDER = "./data"


def submit():
    st.session_state.current_season = st.session_state.new_season_input
    st.session_state.new_season_input = ""


# Utility Functions
def list_seasons():
    """List all season folders in the base directory."""
    return [
        folder
        for folder in os.listdir(DATA_FOLDER)
        if os.path.isdir(os.path.join(DATA_FOLDER, folder))
    ][::-1]


def create_season(name):
    """Create a new season folder."""
    os.makedirs(os.path.join(DATA_FOLDER, name), exist_ok=True)


def delete_season(name):
    """Delete an existing season folder."""
    shutil.rmtree(os.path.join(DATA_FOLDER, name))


def refresh_seasons():
    st.session_state.seasons = list_seasons()


@st.fragment
def display_header(header_title):
    if "current_season" not in st.session_state:
        st.session_state.current_season = ""

    season_control_cols = st.columns([3, 1, 1, 1], vertical_alignment="bottom")

    with season_control_cols[0]:
        st.title(header_title)
    with season_control_cols[1]:
        # create a new season
        with st.popover("Create New Season", use_container_width=True):
            st.text_input(
                "Enter the name of the new season",
                key="new_season_input",
                on_change=submit,
            )
            if st.session_state.current_season:
                os.makedirs(f"./data/{st.session_state.current_season}", exist_ok=True)
                st.success(
                    f"New season '{st.session_state.current_season}' created successfully."
                )
    with season_control_cols[2]:
        # TODO wenn kein folder da
        # select season (folders in .data)
        saved_seasons = os.listdir("./data")[::-1]
        if (
            st.session_state.current_season
            and st.session_state.current_season in saved_seasons
        ):
            season_select_index = saved_seasons.index(st.session_state.current_season)
        else:
            season_select_index = 0
        st.selectbox(
            "Select Season",
            saved_seasons,
            label_visibility="collapsed",
            # index=season_select_index,
            key="current_season",
        )
    with season_control_cols[3]:
        # delete season
        with st.popover("Delete Season", use_container_width=True):
            if st.button(
                f"Delete Season {st.session_state.current_season}?",
                use_container_width=True,
            ):
                os.rmdir(f"./data/{st.session_state.current_season}")
                st.rerun()
                # st.success(
                #     f"Season '{st.session_state.current_season}' deleted successfully."
                # )
    return st.session_state.current_season
