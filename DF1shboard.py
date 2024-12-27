import numpy as np
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st
import utils.style as style

DATA_FOLDER = "./data"


def main():
    # Load the races from the CSV file
    races_df = pd.read_csv(DATA_FOLDER + "/races.csv")
    drivers_df = pd.read_csv(DATA_FOLDER + "/drivers.csv")
    teams_df = pd.read_csv(DATA_FOLDER + "/teams.csv")

    race_names = races_df["Country"].tolist()
    results_df = pd.DataFrame()
    # fastest_file = f"{RESULT_FOLDER}/fastest_laps.csv"
    # try:
    #     fastest_df = pd.read_csv(fastest_file, index_col=0)
    # except FileNotFoundError:
    #     st.warning(f"Fastest laps not found")
    #     st.stop()

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

    st.title("DF1shboard")
    results_df = results_df.groupby(
        ["Country", "EndDate", "TeamName", "DriverName"]
    ).sum()["Points"]
    results_df = results_df.reset_index()
    results_df = results_df.sort_values(
        by=["EndDate", "TeamName", "DriverName"], ascending=[True, True, True]
    )
    # st.dataframe(results_df)

    # TODO multiselect for driver

    # race_interval = st.slider(
    #     "Races to include", value=(1, 24), min_value=1, max_value=24
    # )

    # accumulate points
    results_df["Points"] = results_df["Points"].astype(int)
    results_df["EndDate"] = pd.to_datetime(results_df["EndDate"])
    results_df["PointsAcc"] = results_df.groupby(["DriverName"])["Points"].cumsum()

    fig = px.line(
        results_df,
        x="Country",
        y="PointsAcc",
        line_group="DriverName",
        color="DriverName",
        color_discrete_map=driver_to_color,
        line_dash="DriverName",
        line_dash_sequence=["solid", "dot"],
        # markers=True,
        title="Points over time",
        # line_shape="spline",
        # labels={"PointsAcc": "Points", "Country": ""},
    )
    fig.update_layout(
        height=800,
        xaxis_title=None,
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=results_df["Country"].unique(),
        ),
    )
    st.plotly_chart(fig)

    st.info("More features coming soon!")


if __name__ == "__main__":
    style.set_page_config()
    main()
