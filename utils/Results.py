import os

import pandas as pd
import streamlit as st
import utils.data as data
import utils.style as style

DATA_FOLDER = "./data"


def main(data_folder, selected_season):
    DATA_FOLDER = data_folder
    # Create a Streamlit app with sub-tabs for each race
    st.title(f"Race Results - {selected_season}")
    # Load the races from the CSV file
    try:
        races_df = pd.read_csv(DATA_FOLDER + "/races.csv")
        drivers_df = pd.read_csv(DATA_FOLDER + "/drivers.csv")
        teams_df = pd.read_csv(DATA_FOLDER + "/teams.csv")
    except FileNotFoundError:
        st.warning("Data not found. Please configure the data in apropiate tabs.")
        st.stop()
    # Create a list of race names
    race_names = races_df["Country"].tolist()

    # folder
    os.makedirs(DATA_FOLDER + "/races", exist_ok=True)

    cols = st.columns([12, 2])
    with cols[0]:
        race_name = st.selectbox(
            "keck",
            placeholder="Select Race",
            label_visibility="collapsed",
            options=race_names,
            index=None,
        )
    with cols[1]:
        with st.popover("Fetch Results", use_container_width=True):
            st.markdown(
                "Are you sure you want to fetch results from web? <br> This will overwrite any local changes.",
                unsafe_allow_html=True,
            )
            if st.button("Do it!"):
                with st.spinner("Fetching Results..."):
                    data.save_results_to_csv(datafolder=DATA_FOLDER)
                    st.rerun()

    if race_name is None:
        st.stop()

    has_sprint = races_df["HasSprint"][race_names.index(race_name)]
    race_file = f"{DATA_FOLDER}/races/race_{race_name}.csv"
    sprint_file = f"{DATA_FOLDER}/races/sprint_{race_name}.csv"
    # fastest_file = f"{DATA_FOLDER}/races/fastest_laps.csv"

    if os.path.exists(race_file):
        race_df = pd.read_csv(
            f"{DATA_FOLDER}/races/race_{race_name}.csv",
        )
    else:
        race_df = data.RACE_DEFAULT
    if os.path.exists(sprint_file):
        sprint_df = pd.read_csv(sprint_file)
    else:
        sprint_df = data.SPRINT_DEFAULT
    # if os.path.exists(fastest_file):
    #     fastest_df = pd.read_csv(
    #         fastest_file, index_col=0, dtype=str, keep_default_na=False
    #     )
    # else:
    #     fastest_df = FASTEST_DEFAULT

    st.header(f"Results for {race_name}")
    race_df_edit = st.data_editor(
        race_df,
        num_rows=data.RACE_POS,
        column_config={
            # driver is a selectbox of drivers_df["Driver"].tolist()
            "Position": st.column_config.NumberColumn(
                "Position", required=True, disabled=True, width="small"
            ),
            "DriverName": st.column_config.SelectboxColumn(
                "DriverName",
                options=drivers_df["DriverName"].tolist(),
                # required=True,
            ),
            # team is a selectbox of teams_df["Team"].tolist() but defaults to the team of the selected driver
            "TeamName": st.column_config.SelectboxColumn(
                "TeamName",
                options=teams_df["TeamName"].tolist(),
                required=False,
                help="Leave empty to auto-fill with default team",
            ),
            "Points": st.column_config.NumberColumn(
                "Points",
                required=True,
                disabled=False,
                width="small",
                help="Manually add 1 here for fastest lap",
            ),
        },
        hide_index=True,
        key=f"race_editor_{race_name}_{DATA_FOLDER}",
        use_container_width=True,
    )

    # if race_name not in fastest_df.index:
    #     fastest_df_idx = None
    # else:
    #     fastest_df_name = fastest_df.loc[race_name]["DriverName"]
    #     fastest_df_idx = (
    #         drivers_df["DriverName"].tolist().index(fastest_df_name) + 1
    #         if fastest_df_name
    #         else None
    #     )
    # fastest_lap = st.selectbox(
    #     "keck",
    #     placeholder="Fastest Lap",
    #     label_visibility="collapsed",
    #     options=[""] + drivers_df["DriverName"].tolist() + [None],
    #     index=fastest_df_idx,
    #     key=f"fastest_{race_name}",
    #     help="Adds 1 point to selected driver",
    # )
    # fastest_df.loc[race_name] = fastest_lap

    if has_sprint:
        st.header(f"Sprint")
        sprint_df_edit = st.data_editor(
            sprint_df,
            num_rows=data.SPRINT_POS,
            column_config={
                "Position": st.column_config.NumberColumn(
                    "Position", required=True, disabled=True, width="small"
                ),
                "DriverName": st.column_config.SelectboxColumn(
                    "DriverName",
                    options=drivers_df["DriverName"].tolist(),
                    # required=True,
                ),
                "TeamName": st.column_config.SelectboxColumn(
                    "TeamName",
                    options=teams_df["TeamName"].tolist(),
                    required=False,
                    help="Leave empty to auto-fill with default team",
                ),
                "Points": st.column_config.NumberColumn(
                    "Points", required=True, disabled=True, width="small"
                ),
            },
            hide_index=True,
            key=f"sprint_{race_name}",
            use_container_width=True,
        )

    if st.button("Save Results", key=f"save_{race_name}"):

        # # set pos 0 as fastest lap
        # if fastest_lap:
        #     race_df_edit = pd.concat(
        #         [
        #             pd.DataFrame(
        #                 {
        #                     "Position": [0],
        #                     "DriverName": [fastest_lap],
        #                     "TeamName": [""],
        #                     "Points": [1],
        #                 }
        #             ),
        #             race_df_edit,
        #         ]
        #     )
        # update the team names
        race_df_edit = data.update_teams(race_df_edit, drivers_df)
        race_df_edit.to_csv(race_file, index=False)
        if has_sprint:
            sprint_df_edit = data.update_teams(sprint_df_edit, drivers_df)
            sprint_df_edit.to_csv(sprint_file, index=False)
        # update fastest df
        # fastest_df.to_csv(fastest_file, index=True)
        st.rerun()


if __name__ == "__main__":
    style.set_page_config()
    main()
