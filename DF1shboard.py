import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn import svm
import toml

from utils import data, func, style

# Load settings from the settings.toml file
settings = func.read_settings()
DATA_FOLDER = settings["dashboard"].get("data_folder", f"./data/")

def short_legend(name):
    return name[:15] + "..." if len(name) > 15 else name


# @st.cache_data()
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
    piv_table = piv_table.astype(float).fillna(0).cumsum(axis=0)
    piv_table = piv_table.stack(future_stack=True).reset_index()
    return piv_table


@st.cache_data()
def plot_points_over_time(results_df, entity="DriverName", **kwargs):
    piv_table = get_points_over_time(results_df, entity=entity)
    fig = px.line(
        piv_table,
        x="Country",
        y="Points",
        line_group=entity,
        color=entity,
        line_dash=entity,
        **kwargs,
    )
    fig.update_layout(
        height=800,
        xaxis_title=None,
    )
    fig.for_each_trace(
        lambda trace: trace.update(
            name=short_legend(trace.name),
        )
    )

    return fig


@st.cache_data()
def load_data(selected_season):
    DATA_FOLDER = f"./data/{selected_season}"

    # Load the races from the CSV file
    try:
        races_df = pd.read_csv(
            DATA_FOLDER + "/races.csv",
            parse_dates=["StartDate", "EndDate"],
        )
        drivers_df = pd.read_csv(DATA_FOLDER + "/drivers.csv")
        teams_df = pd.read_csv(DATA_FOLDER + "/teams.csv")
    except FileNotFoundError:
        st.warning("Data not found. Please configure the data in apropiate tabs.")
        st.stop()
    races_df["StartDate"] = pd.to_datetime(races_df["StartDate"]).dt.date
    races_df["EndDate"] = pd.to_datetime(races_df["EndDate"]).dt.date

    # Load the results from the CSV file
    results_df = pd.DataFrame()
    for country, has_sprint, end_date in races_df[
        ["Country", "HasSprint", "EndDate"]
    ].values:
        race_file = f"{DATA_FOLDER}/races/race_{country}.csv"
        sprint_file = f"{DATA_FOLDER}/races/sprint_{country}.csv"
        try:
            race_df = pd.read_csv(race_file)
            race_df["Sprint"] = False
            if has_sprint:
                sprint_df = pd.read_csv(sprint_file)
                sprint_df["FastestLap"] = 0
                sprint_df["Sprint"] = True
            else:
                sprint_df = None
        except FileNotFoundError:
            race_df = data.RACE_DEFAULT
            sprint_df = data.SPRINT_DEFAULT

        df = pd.concat([race_df, sprint_df], axis=0)
        df["Country"] = country
        df["EndDate"] = end_date
        results_df = pd.concat([results_df, df], axis=0) if not results_df.empty else df

    # FIXME type conversion stuff
    results_df["Points"] = results_df["Points"].astype(float)
    results_df["Points"] = results_df["Points"] + results_df["FastestLap"]
    results_df["EndDate"] = pd.to_datetime(results_df["EndDate"]).dt.date

    return races_df, teams_df, drivers_df, results_df


def main():
    title_col, season_col = st.columns([5, 1], vertical_alignment="bottom")
    with title_col:
        st.title("DF1shboard")
    try:
        saved_seasons = func.list_seasons()
    except FileNotFoundError:
        st.warning("No seasons found. Please configure the data in Config tab.")
        st.stop()
    with season_col:
        selected_season = st.selectbox(
            "Select Season",
            saved_seasons,
            key="select_season",
            label_visibility="collapsed",
            disabled=not saved_seasons,
        )

    races_df, teams_df, drivers_df, results_df = load_data(selected_season)

    team_to_color = teams_df.set_index("TeamName")["Color"].to_dict()
    drivers_df["Color"] = drivers_df["TeamName"].map(team_to_color)
    line_styles = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]
    drivers_df["LineStyle"] = (
        drivers_df.groupby("TeamName")
        .cumcount()
        .apply(lambda nr: line_styles[nr % len(line_styles)])
    )
    race_names = races_df["Country"].tolist()
    driver_points_sum = results_df.groupby("DriverName")["Points"].sum()
    driver_names = driver_points_sum.sort_values(ascending=False).index
    team_points_sum = results_df.groupby("TeamName")["Points"].sum()
    team_names = team_points_sum.sort_values(ascending=False).index

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


    start_points = pd.DataFrame(
        {
            "Country": "",
            "EndDate": pd.to_datetime(
                f"{races_df["StartDate"].min().year}-01-01"
            ).date(),
            "DriverName": drivers_df["DriverName"],
            "TeamName": drivers_df["TeamName"],
            "Points": 0,
        }
    )
    results_df = pd.concat([start_points, results_df], axis=0)

    # FILTER ############################################################
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
    with st.sidebar:#.expander("Filter", expanded=True):
        # col1, col2 = st.columns([1, 100], vertical_alignment="center", gap="medium")
        # with col1:
        filter_by_team = st.checkbox(
            "Team Filter", value=False, #label_visibility="collapsed"
        )
        # with col2:
        selected_teams = st.multiselect(
            "Select Teams",
            options=team_names,
            default=team_names,
            label_visibility="collapsed",
            disabled=not filter_by_team,
        )
        if filter_by_team and selected_teams:
            results_df = results_df[results_df["TeamName"].isin(selected_teams)]
            
            
    # reassign team names to the filtered teams
    team_names = results_df["TeamName"].unique()
    driver_names = results_df["DriverName"].unique()

    # PLOT ############################################################

    cols = st.columns(2)

    driver_point_over_time_graph = plot_points_over_time(
        results_df,
        entity="DriverName",
        color_discrete_map=drivers_df.set_index("DriverName")["Color"].to_dict(),
        line_dash_map=drivers_df.set_index("DriverName")["LineStyle"].to_dict(),
        title="Driver Points Over Time",
        category_orders={"DriverName": list(driver_names)},
    )

    team_points_over_time_grpah = plot_points_over_time(
        results_df,
        entity="TeamName",
        color_discrete_map=team_to_color,
        line_dash_sequence=["solid"],
        title="Team Points Over Time",
        category_orders={"TeamName": list(team_names)},
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
        driver2 = st.selectbox(
            "Select 2", options, label_visibility="collapsed", index=1
        )

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
        if (max_pred := max(1, len(race_names) - len(piv) + 2)) > 1:
            next_n = st.select_slider(
                "Predict next n races",
                options=np.arange(0, max_pred),
                value=0,
            )
        else:
            next_n = 0

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

    cols = st.columns([4, 2])
    # Driver points ############################################################
    with cols[0]:
        st.header("Driver Points")
        agg_method = st.radio(
            "Driver Calculation",
            ["mean", "sum"],
            horizontal=True,
            label_visibility="collapsed",
        )
        avg_points = (
            results_df.groupby("DriverName")["Points"]
            .agg(agg_method)
            .round(2)
            .reset_index()
        )
        avg_points = avg_points.sort_values(by="Points", ascending=False)
        avg_points["DriverName"] = avg_points["DriverName"].apply(short_legend)
        fig = px.bar(
            avg_points,
            x="DriverName",
            y="Points",
            color_discrete_sequence=["#b73a3a"],
        )
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig)

    # Team points ############################################################
    with cols[1]:
        st.header("Team Points")
        agg_method = st.radio(
            "Team Calculation",
            ["mean", "sum"],
            horizontal=True,
            label_visibility="collapsed",
        )
        avg_points = (
            results_df.groupby("TeamName")["Points"]
            .agg(agg_method)
            .round(2)
            .reset_index()
        )
        avg_points = avg_points.sort_values(by="Points", ascending=False)
        avg_points["TeamName"] = avg_points["TeamName"].apply(short_legend)
        fig = px.bar(
            avg_points,
            x="TeamName",
            y="Points",
            color_discrete_sequence=["#b73a3a"],
        )
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig)

    # Heatmap for positions ############################################################
    cols = st.columns([1, 5])
    with cols[0]:
        st.header("Position Heatmap")
        entity = st.radio(
            "Entity 1",
            ["DriverName", "TeamName"],
            label_visibility="collapsed",
        )
        sprint = st.radio(
            "Select Race Type 1",
            ["Race", "Sprint", "Both"],
            label_visibility="collapsed",
        )
        show_values = st.toggle("Show Values 1", value=False)
    with cols[1]:
        if sprint == "Race":
            positions_df = results_df[results_df["Sprint"] == False]
        elif sprint == "Sprint":
            positions_df = results_df[results_df["Sprint"] == True]
        else:
            positions_df = results_df
        positions_df = positions_df[[entity, "Position"]]
        positions_df = positions_df.groupby(entity)["Position"].value_counts()
        positions_df = positions_df.unstack().fillna(0)
        order = driver_names if entity == "DriverName" else team_names
        positions_df = positions_df.reindex(order).fillna(0)
        # FIXME: layout is completely off when driver-team pair is missing in data
        fig = px.imshow(
            positions_df,
            color_continuous_scale=["#0e1117", "#ff4b4b"],
            labels=dict(x="Position", y=entity, color="Count"),
            text_auto=show_values,
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            height=500,
        )
        st.plotly_chart(fig)

    # Debug Pivot Table ############################################################
    # make pivot of y=driver x=country with points
    cols = st.columns([1, 5])
    with cols[0]:
        st.header("Points Heatmap")
        entity = st.radio(
            "Entity 2",
            ["DriverName", "TeamName"],
            label_visibility="collapsed",
        )
        sprint = st.radio(
            "Select Race Type 2",
            ["Race", "Sprint", "Both"],
            label_visibility="collapsed",
        )
        show_values = st.toggle("Show Values 2", value=False)
    with cols[1]:
        if sprint == "Race":
            piv_table = results_df[results_df["Sprint"] == False]
        elif sprint == "Sprint":
            piv_table = results_df[results_df["Sprint"] == True]
        else:
            piv_table = results_df
        piv_table = piv_table.pivot_table(
            values="Points",
            index=entity,
            columns="Country",
            aggfunc="sum",
        )
        order = driver_names if entity == "DriverName" else team_names
        piv_table = piv_table.reindex(order, axis=0)
        piv_table = piv_table.reindex(race_names, axis=1)
        piv_table = piv_table.astype(float).fillna(0)
        # make heatmap with points displayed
        fig = px.imshow(
            piv_table,
            color_continuous_scale=["#0e1117", "#ff4b4b"],
            labels=dict(x="Country", y=entity, color="Points"),
            text_auto=show_values,
            aspect="auto",
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    style.set_page_config()
    main()
