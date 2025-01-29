# %%
import math
import os
from datetime import datetime
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup

# URL for the F1 results page
base_url = "https://www.formula1.com"
results_url = "https://www.formula1.com/en/results/2024/races"
drivers_url = "https://www.formula1.com/en/drivers"
team_url = "https://www.formula1.com/en/teams"

DATA_FOLDER = "./data"

COL_NAME_MAP = {
    "Pos": "Position",
    "No": "Number",
    "Driver": "DriverName",
    "Car": "Car",
    "Laps": "Laps",
    "Time/retired": "Time",
    "Pts": "Points",
}

RACES_DTYPES = {
    "Index": int,
    "StartDate": str,
    "EndDate": str,
    "Country": str,
    "City": str,
    "Circuit": str,
    "HasSprint": bool,
}

DRIVERS_DTYPES = {
    "DriverName": str,
    "TeamName": str,
}

TEAMS_DTYPES = {
    "TeamName": str,
    "Color": str,
}

RACE_POS = 10
RACE_DEFAULT = pd.DataFrame(
    {
        "Position": list(range(1, RACE_POS + 1)),
        "DriverName": [None] * RACE_POS,
        "TeamName": [None] * RACE_POS,
        "Points": [25, 18, 15, 12, 10, 8, 6, 4, 2, 1],
    }
)
SPRINT_POS = 8
SPRINT_DEFAULT = pd.DataFrame(
    {
        "Position": list(range(1, SPRINT_POS + 1)),
        "DriverName": [None] * SPRINT_POS,
        "TeamName": [None] * SPRINT_POS,
        "Points": [8, 7, 6, 5, 4, 3, 2, 1],
    }
)


def update_teams(df, drivers_df):
    """update column TeamName in df based on the column DriverName-TeamName pair in drivers_df"""
    for i, row in df.iterrows():
        driver = row["DriverName"]
        team = row["TeamName"]
        if driver is not None and isinstance(driver, str):

            driver_row = drivers_df[drivers_df["DriverName"] == driver]
            if len(driver_row) < 1:
                continue
            if team is None or (isinstance(team, float) and math.isnan(team)):
                team = driver_row["TeamName"].values[0]
                df.loc[i, "TeamName"] = team
    return df


def get_soup(url):
    content = requests.get(url).content.decode("utf-8")
    content = content.replace("\xa0", " ")
    soup = BeautifulSoup(content, "html.parser")
    return soup


def get_table(soup):
    table = soup.find(lambda tag: tag.name == "table")
    table = pd.read_html(StringIO(str(table)))[0]
    return table


def get_sprint(soup, only_check=False):
    links = soup.find_all("a", href=True, class_="block")
    links = [link for link in links if "sprint-results" in link["href"]]
    if only_check:
        return len(links) > 0
    if len(links) > 0:
        link = links[0]
        sprint_link = base_url + link["href"]
        soup = get_soup(sprint_link)
        return get_table(soup)
    return None


def get_locations():
    # get all location names and location links from the main page
    soup = get_soup(results_url)
    # get all links that contain race-result
    links = soup.find_all("a", href=True, class_="block")
    # get all location names
    locations = [
        (link.get_text(strip=True), link["href"])
        for link in links
        if "race-result" in link["href"]
    ]
    infos = dict()

    for location, link in locations:
        soup = get_soup(base_url + link)

        # parse date format: dd MMM - dd MMM YYYY
        date, circuit = soup.find_all("p")[3:5]
        date = date.get_text(strip=True)
        circuit = circuit.get_text(strip=True)
        circuit, city = circuit.split(", ")
        start, end = date.split(" - ")
        end_date = datetime.strptime(end, "%d %b %Y")
        if len(start.split()) == 1:
            start = f"{start} {end.split()[-2]} {end.split()[-1]}"
        elif len(start.split()) == 2:
            start = f"{start} {end.split()[-1]}"
        start_date = datetime.strptime(start, "%d %b %Y")
        has_sprint = get_sprint(soup) is not None

        infos[location] = {
            "link": link,
            "start_date": start_date,
            "end_date": end_date,
            "city": city,
            "circuit": circuit,
            "has_sprint": has_sprint,
        }

    return infos


def get_races():
    """Index,Date,City,Country,HasSprint"""
    info = get_locations()

    data = []
    for i, (location, link) in enumerate(info.items()):
        data.append(
            {
                "Index": i,
                "StartDate": link["start_date"],
                "EndDate": link["end_date"],
                "Country": location,
                "City": link["city"],
                "Circuit": link["circuit"],
                "HasSprint": link["has_sprint"],
            }
        )

    return pd.DataFrame(data)


def refactor_df(df: pd.DataFrame, datafolder=DATA_FOLDER):
    """assuming df is a race/sprint result table from f1 web: refactor names,columns,types,..."""
    df = df.iloc[:20, :]
    df = df[["Pos", "Driver", "Pts"]]

    # exclude where Pos is not a number
    df = df[df["Pos"].apply(lambda x: isinstance(x, int) or x.isnumeric())]

    df["Pos"] = df["Pos"].astype(int)
    df["Driver"] = df["Driver"].str[:-3]
    df["Pts"] = df["Pts"].astype(int)

    df = df.rename(columns=COL_NAME_MAP)
    df.insert(2, "TeamName", None)
    drivers_df = pd.read_csv(datafolder + "/drivers.csv")
    df = update_teams(df, drivers_df)

    return df


def save_results_to_csv(datafolder=DATA_FOLDER):
    os.makedirs(datafolder + "/races", exist_ok=True)
    for location, info in get_locations().items():
        link = info["link"]

        soup = get_soup(base_url + link)

        # Get the race results
        race = get_table(soup)
        race = refactor_df(race, datafolder)
        race.to_csv(f"{datafolder}/races/race_{location}.csv", index=False)
        # Get the sprint results
        sprint = get_sprint(soup)
        if sprint is not None:
            sprint = refactor_df(sprint, datafolder)
            sprint.to_csv(f"{datafolder}/races/sprint_{location}.csv", index=False)


def get_drivers():
    drivers = []
    soup = get_soup(drivers_url)
    links = soup.find_all("a", href=True, class_="group")
    links = [link for link in links if "drivers/" in link["href"]]
    for driver in links:
        ps = driver.find_all("p")
        first_name = driver.find_all("p")[0].get_text(strip=True)
        last_name = driver.find_all("p")[1].get_text(strip=True)
        team_name = driver.find_all("p")[2].get_text(strip=True)
        drivers.append(
            {
                "DriverName": f"{first_name} {last_name}",
                "TeamName": team_name,
            }
        )

    drivers_df = pd.DataFrame(drivers)
    return drivers_df


def get_teams():
    teams = []
    soup = get_soup(team_url)
    links = soup.find_all("a", href=True, class_="group")
    for link in links:
        name = link.span.get_text(strip=True)
        color = [
            "#" + color[-6:]
            for color in link.div.attrs["class"]
            if color.startswith("text")
        ][0]
        teams.append({"TeamName": name, "Color": color})

    teams_df = pd.DataFrame(teams)
    return teams_df
