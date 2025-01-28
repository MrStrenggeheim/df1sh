import os

import streamlit as st
from utils import Drivers, Races, Results, Teams, func, style

DATA_FOLDER = "./data"


def main():

    # tabs for races, teams, drivers, results
    tabs = st.tabs(["Races", "Teams", "Drivers", "Results"])

    data_folder = f"./{DATA_FOLDER}/{selected_season}"
    with tabs[0]:
        Races.main(data_folder)
    with tabs[1]:
        Teams.main(data_folder)
    with tabs[2]:
        Drivers.main(data_folder)
    with tabs[3]:
        Results.main(data_folder)


if __name__ == "__main__":
    style.set_page_config()
    main()
