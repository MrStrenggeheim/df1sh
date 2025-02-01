import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn import svm
from utils import data, func, style

DATA_FOLDER = "./data"


@st.cache_data()
def get_points_over_time(results_df, entity="DriverName"):
    if entity == "DriverName":
        summed_df = results_df.groupby(
            ["Country", "EndDate", "TeamName", entity]
        ).sum()["Points"]
    if entity == "TeamName":
        summed_df = results_df.groupby(["Country", "EndDate", entity]).sum()["Points"]
    summed_df = summed_df.reset_index().sort_values(
        by=["EndDate", "TeamName", entity], ascending=[True, True, True]
    )

    piv_table = summed_df.pivot_table(["Points"], ["Country"], [entity], sort=False)
    piv_table = piv_table.fillna(0).cumsum(axis=0)
    piv_table = piv_table.stack(future_stack=True).reset_index()
    return piv_table


@st.cache_data()
def plot_points_over_time(
    results_df, entity="DriverName", color_map=None, line_dash_sequence=None, **kwargs
):
    piv_table = get_points_over_time(results_df, entity=entity)
    fig = px.line(
        piv_table,
        x="Country",
        y="Points",
        line_group=entity,
        color=entity,
        color_discrete_map=color_map,
        line_dash=entity,
        line_dash_sequence=line_dash_sequence,
        **kwargs,
    )
    fig.update_layout(
        height=800,
        xaxis_title=None,
    )
    fig.for_each_trace(
        lambda trace: trace.update(
            name=trace.name[:15] + "..." if len(trace.name) > 15 else trace.name
        )
    )

    return fig


def main():
    # title
    title_col, season_col = st.columns([5, 1], vertical_alignment="bottom")
    with title_col:
        st.title("DF1shboard")
    with season_col:
        saved_seasons = func.list_seasons()
        selected_season = st.selectbox(
            "Select Season",
            saved_seasons,
            key="select_season",
            label_visibility="collapsed",
            disabled=not saved_seasons,
        )

    DATA_FOLDER = f"./data/{selected_season}"

    # Load the races from the CSV file
    try:
        races_df = pd.read_csv(DATA_FOLDER + "/races.csv")
        drivers_df = pd.read_csv(DATA_FOLDER + "/drivers.csv")
        teams_df = pd.read_csv(DATA_FOLDER + "/teams.csv")
    except FileNotFoundError:
        st.warning("Data not found. Please configure the data in apropiate tabs.")
        st.stop()
    races_df["StartDate"] = pd.to_datetime(races_df["StartDate"]).apply(
        lambda x: x.date()
    )
    race_names = races_df["Country"].tolist()
    results_df = pd.DataFrame()

    # to get colormap: match driver with team wehere color is a column
    team_to_color = teams_df.set_index("TeamName")["Color"].to_dict()
    driver_to_team = drivers_df.set_index("DriverName")["TeamName"].to_dict()
    driver_to_color = {
        driver: team_to_color[team] for driver, team in driver_to_team.items()
    }

    for country, has_sprint, end_date in races_df[
        ["Country", "HasSprint", "EndDate"]
    ].values:
        race_file = f"{DATA_FOLDER}/races/race_{country}.csv"
        sprint_file = f"{DATA_FOLDER}/races/sprint_{country}.csv"
        try:
            race_df = pd.read_csv(race_file)
            sprint_df = pd.read_csv(sprint_file) if has_sprint else None
        except FileNotFoundError:
            race_df = data.RACE_DEFAULT
            sprint_df = data.SPRINT_DEFAULT
        df = pd.concat([race_df, sprint_df], axis=0)
        df["Country"] = country
        df["EndDate"] = end_date
        results_df = pd.concat([results_df, df], axis=0) if not results_df.empty else df

    results_df["Points"] = results_df["Points"].astype(int)
    results_df["EndDate"] = pd.to_datetime(results_df["EndDate"]).apply(
        lambda x: x.date()
    )

    # START ############################################################
    today = pd.to_datetime("today").date()
    upcoming_races = races_df[races_df["StartDate"] > today][["Country", "StartDate"]]
    if upcoming_races.empty:
        st.markdown(style.NO_UPCOMING_RACE_HTML, unsafe_allow_html=True)
    else:
        next_race = upcoming_races["Country"].values[0]
        days_left = (upcoming_races["StartDate"].values[0] - today).days
        # nice markdown text about next race
        st.markdown(
            style.NEXT_RACE_HTML.format(next_race=next_race, days_left=days_left),
            unsafe_allow_html=True,
        )

    # FILTER ############################################################
    driver_names = drivers_df["DriverName"].unique()
    driver_names.sort()
    start_points = pd.DataFrame(
        {
            "Country": [""] * len(driver_names),
            "EndDate": pd.to_datetime("2021-01-01").date(),
            "DriverName": driver_names,
            "TeamName": [driver_to_team[driver] for driver in driver_names],
            "Points": 0,
        }
    )
    results_df = pd.concat([start_points, results_df], axis=0)

    # two slide slider for the range
    season_start, season_end = st.sidebar.select_slider(
        "Season Range",
        options=[f"{location}" for location in race_names],
        label_visibility="collapsed",
        value=(race_names[0], race_names[-1]),
    )
    season_start_idx, season_end_idx = (
        race_names.index(season_start),
        race_names.index(season_end),
    )
    filtered_countries = race_names[season_start_idx : season_end_idx + 1] + [""]

    results_df = results_df[results_df["Country"].isin(filtered_countries)]

    # team name filter, multi select
    team_names = teams_df["TeamName"].unique()
    team_names.sort()
    selected_teams = st.multiselect(
        "Select Teams",
        options=team_names,
        default=team_names,
        label_visibility="collapsed",
    )
    results_df = results_df[results_df["TeamName"].isin(selected_teams)]

    # PLOT ############################################################

    cols = st.columns(2)

    driver_point_over_time_graph = plot_points_over_time(
        results_df,
        entity="DriverName",
        color_map=driver_to_color,
        line_dash_sequence=["solid", "dot"],
        title="Driver Points Over Time",
    )

    team_points_over_time_grpah = plot_points_over_time(
        results_df,
        entity="TeamName",
        color_map=team_to_color,
        line_dash_sequence=["solid"],
        title="Team Points Over Time",
    )

    cols[0].plotly_chart(driver_point_over_time_graph)
    cols[1].plotly_chart(team_points_over_time_grpah)

    # COMPARE BEST 2 DRIVERS ############################################################

    cols = st.columns([3, 7])
    with cols[0]:
        st.header("Driver Comparison")

        entity = st.radio(
            "Entity", ["DriverName", "TeamName"], label_visibility="collapsed"
        )

        # calculate points left for each race
        max_pts_nosprint = 44 if entity == "TeamName" else 26
        max_pts_sprint = 59 if entity == "TeamName" else 34
        races_df["PointsLeft"] = races_df["HasSprint"].apply(
            lambda x: max_pts_sprint if x else max_pts_nosprint
        )
        races_df["PointsLeft"] = races_df["PointsLeft"][::-1].cumsum()[::-1]

        points_over_time = get_points_over_time(results_df, entity=entity)
        options = driver_names if entity == "DriverName" else team_names
        max_idx = points_over_time["Points"].idxmax()
        max_entity = points_over_time.loc[max_idx][entity]
        driver1 = st.selectbox(
            "Select 1",
            options,
            index=options.tolist().index(max_entity),
            label_visibility="collapsed",
        )
        driver2 = st.selectbox("Select 2", options, label_visibility="collapsed")

        points_over_time = points_over_time[
            points_over_time[entity].isin([driver1, driver2])
        ]
        piv = points_over_time.pivot_table(
            "Country", "Country", entity, fill_value=0, sort=False
        )
        piv["Diff"] = piv[driver1] - piv[driver2]
        piv.reset_index(inplace=True)

        # SETTINGS
        st.divider()
        display_setting_cols = st.columns(2)
        with display_setting_cols[0]:
            show_points_left = st.checkbox("Show Points Left", value=True)
            show_prediction = st.checkbox("Show Prediction", value=True)
        with display_setting_cols[1]:
            min_y, max_y = st.slider("Y-Range", value=(-1000, 1000), step=50)
        last_n = st.select_slider(
            "Predict on last n races", options=np.arange(len(piv) + 1), value=0
        )
        st.write(max(1, len(race_names) - len(piv) + 2))
        next_n = st.select_slider(
            "Predict next n races",
            options=np.arange(0, max(2, len(race_names) - len(piv) + 2)),
            value=0,
        )

        total_n = len(piv)
        X_total = np.arange(total_n).reshape(-1, 1)
        X_train = X_total[-last_n:]
        y_total = piv["Diff"].values
        y_train = y_total[-last_n:]
        points_left = races_df["PointsLeft"].values.tolist() + [0]

        model = svm.SVR(kernel="linear")
        model.fit(X_train, y_train)

        X_pred = np.arange(0, len(piv) + next_n).reshape(-1, 1)
        y_pred = model.predict(X_pred)
        y_pred = np.concatenate(
            [y_pred, [np.nan] * (len(race_names) - len(y_pred) + 1)]
        )
        y = np.concatenate([y_total, [np.nan] * (len(race_names) - len(y_total) + 1)])
        # X_pred = np.arange(0, len(piv) + next_n).reshape(-1, 1)
        # y_pred = model.predict(X_pred)
        # y = np.concatenate([y_total, [np.nan] * next_n])
        # points_left = np.concatenate(
        #     [points_left, [np.nan] * (len(y) - len(points_left))]
        # )[: len(y_pred)]

        # TODO make length variable when prediction goes above all races

        plot_df = pd.DataFrame(
            {
                "X_pred": np.arange(len(race_names) + 1),
                "Diff": y,
                "PointsLeft": points_left,
                "Diff_pred": y_pred,
                "Country": [""] + race_names,
            }
        )

    with cols[1]:
        y_labels = ["Diff"]
        y_labels = y_labels + ["Diff_pred"] if show_prediction else y_labels
        y_labels = y_labels + ["PointsLeft"] if show_points_left else y_labels
        driver_diff_graph = px.line(
            plot_df,
            x="Country",
            y=y_labels,
            color_discrete_map={
                "Diff": "#ff7f0e",
                "Diff_pred": "#d62728",
                "PointsLeft": "#1f77b4",
            },
        )
        driver_diff_graph.update_layout(
            height=700,
            xaxis_title=None,
            legend_title_text=None,
            # y range
            yaxis=dict(range=[min_y, max_y]),
            xaxis=dict(range=[-0.5, len(race_names) + 0.5]),
        )
        if show_prediction and last_n > 0:
            driver_diff_graph.add_vrect(
                x0=total_n - last_n - 0.5,
                x1=total_n - 0.5,
                fillcolor="rgba(0.5,0,0,0.1)",
                layer="below",
                line_width=0,
            )
        st.plotly_chart(driver_diff_graph)


if __name__ == "__main__":
    style.set_page_config()
    main()
