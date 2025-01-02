import numpy as np
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st
import utils.style as style

DATA_FOLDER = "./data"


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
    summed_df["Points"] = summed_df["Points"].astype(int)
    summed_df["EndDate"] = pd.to_datetime(summed_df["EndDate"])

    piv_table = summed_df.pivot_table(["Points"], ["Country"], [entity], sort=False)
    piv_table = piv_table.fillna(0).cumsum(axis=0)
    piv_table = piv_table.stack(future_stack=True).reset_index()
    return piv_table


def plot_points_over_time(
    results_df, entity="DriverName", color_map=None, line_dash_sequence=None
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
        title="Points over time",
    )
    fig.update_layout(
        height=800,
        xaxis_title=None,
    )

    # legent max width
    # fig.update_layout(
    #     legend=dict(
    #         title=None,
    #         orientation="v",
    #         yanchor="bottom",
    #         xanchor="right",
    #         x=1,
    #         y=1,
    #         borderwidth=0,
    #         itemwidth=30,
    #     )
    # )
    fig.for_each_trace(
        lambda trace: trace.update(
            name=trace.name[:15] + "..." if len(trace.name) > 15 else trace.name
        )
    )

    return fig


def main():
    # Load the races from the CSV file
    races_df = pd.read_csv(DATA_FOLDER + "/races.csv")
    drivers_df = pd.read_csv(DATA_FOLDER + "/drivers.csv")
    teams_df = pd.read_csv(DATA_FOLDER + "/teams.csv")

    race_names = races_df["Country"].tolist()
    results_df = pd.DataFrame()
    # fastest_file = f"{DATA_FOLDER}/races/fastest_laps.csv"
    # try:
    #     fastest_df = pd.read_csv(
    #         fastest_file, index_col=0, dtype=str, keep_default_na=False
    #     )
    # except FileNotFoundError:
    #     fastest_df = pd.DataFrame()

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
            st.warning(f"Results not found")
            st.stop()
        df = pd.concat([race_df, sprint_df], axis=0)
        df["Country"] = country
        df["EndDate"] = end_date
        results_df = pd.concat([results_df, df], axis=0) if not results_df.empty else df

    # add points of fastest laps
    # for country, driver in fastest_df.iterrows():
    #     print(country, driver)
    #     results_df = pd.concat(
    #         [
    #             results_df,
    #             pd.DataFrame(
    #                 {
    #                     "Country": country,
    #                     "EndDate": races_df[races_df["Country"] == country][
    #                         "EndDate"
    #                     ].values[0],
    #                     "Position": 0,
    #                     "DriverName": driver["DriverName"],
    #                     "TeamName": results_df[
    #                         results_df["DriverName"] == driver["DriverName"]
    #                     ]["TeamName"].values[0],
    #                     "Points": 1,
    #                 }
    #             ),
    #         ],
    #         axis=0,
    #         ignore_index=True,
    #     )

    st.title("DF1shboard")

    cols = st.columns(2)

    driver_point_over_time_graph = plot_points_over_time(
        results_df,
        entity="DriverName",
        color_map=driver_to_color,
        line_dash_sequence=["solid", "dot"],
    )

    team_points_over_time_grpah = plot_points_over_time(
        results_df,
        entity="TeamName",
        color_map=team_to_color,
        line_dash_sequence=["solid"],
    )

    cols[0].plotly_chart(driver_point_over_time_graph)
    cols[1].plotly_chart(team_points_over_time_grpah)

    st.info("More features coming soon!")


if __name__ == "__main__":
    style.set_page_config()
    main()
