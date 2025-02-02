# %%
import math
import os
from datetime import datetime
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup, FeatureNotFound

# URL for the F1 results page
base_url = "https://www.formula1.com"
archive_url = "https://www.formula1.com/en/results/"

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

RACE_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
RACE_POS = 10
RACE_DEFAULT = pd.DataFrame(
    {
        "Position": list(range(1, RACE_POS + 1)),
        "DriverName": [None] * RACE_POS,
        "TeamName": [None] * RACE_POS,
        "Points": RACE_POINTS,
        "FastestLap": [0] * RACE_POS,
    }
)
SPRINT_POINTS = [8, 7, 6, 5, 4, 3, 2, 1]
SPRINT_POS = 8
SPRINT_DEFAULT = pd.DataFrame(
    {
        "Position": list(range(1, SPRINT_POS + 1)),
        "DriverName": [None] * SPRINT_POS,
        "TeamName": [None] * SPRINT_POS,
        "Points": SPRINT_POINTS,
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
    try:
        table = pd.read_html(StringIO(str(table)))[0]
    except FeatureNotFound:
        return None
    except ValueError:  # no tables found
        return None
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


def get_locations(year_to_fetch="Current"):
    if year_to_fetch == "Current":
        year_to_fetch = str(datetime.now().year)
    url = archive_url + year_to_fetch + "/races"
    # get all location names and location links from the main page
    soup = get_soup(url)
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
        split = date.split(" - ")
        if len(split) == 1:
            start_date = datetime.strptime(date, "%d %b %Y")
            end_date = start_date + pd.DateOffset(days=3)
        else:
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


def get_races(year_to_fetch="Current"):
    """Index,Date,City,Country,HasSprint"""
    info = get_locations(year_to_fetch=year_to_fetch)

    data = []
    for location, link in info.items():
        data.append(
            {
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
    df["Pts"] = pd.to_numeric(df["Pts"])

    df = df.rename(columns=COL_NAME_MAP)
    df.insert(2, "TeamName", None)
    drivers_df = pd.read_csv(datafolder + "/drivers.csv")
    df = update_teams(df, drivers_df)

    return df


def save_results_to_csv(datafolder=DATA_FOLDER, year_to_fetch="Current"):
    os.makedirs(datafolder + "/races", exist_ok=True)
    for file in os.listdir(datafolder + "/races"):
        if file.endswith(".csv"):
            os.remove(datafolder + "/races/" + file)
    for location, info in get_locations(year_to_fetch).items():
        link = info["link"]
        soup = get_soup(base_url + link)

        # Get the race results
        race = get_table(soup)
        if race is None:
            continue
        race = refactor_df(race, datafolder)
        # add fastest lap column
        race["FastestLap"] = race["Points"].map(
            lambda pt: pt not in ([0] + RACE_POINTS)
        )
        race["Points"] = race["Points"] - race["FastestLap"]

        race.to_csv(f"{datafolder}/races/race_{location}.csv", index=False)
        # Get the sprint results
        sprint = get_sprint(soup)
        if sprint is not None:
            sprint = refactor_df(sprint, datafolder)
            sprint.to_csv(f"{datafolder}/races/sprint_{location}.csv", index=False)


# print(save_results_to_csv("../data/2024", "2024"))


def get_drivers(year_to_fetch="Current"):
    if year_to_fetch == "Current":
        drivers = []
        url = "https://www.formula1.com/en/drivers"
        soup = get_soup(url)
        links = soup.find_all("a", href=True, class_="group")
        links = [link for link in links if "drivers/" in link["href"]]
        for driver in links:
            first_name = driver.find_all("p")[0].get_text(strip=True)
            last_name = driver.find_all("p")[1].get_text(strip=True)
            team_name = driver.find_all("p")[2].get_text(strip=True)
            drivers.append(
                {
                    "DriverName": f"{first_name} {last_name}",
                    "TeamName": team_name,
                }
            )
        return pd.DataFrame(drivers)
    else:
        url = archive_url + year_to_fetch + "/drivers"
        df = get_table(get_soup(url))
        if df is None:
            return pd.DataFrame()
        df.rename(columns={"Driver": "DriverName", "Car": "TeamName"}, inplace=True)
        df["DriverName"] = df["DriverName"].str[:-3]
        return df[["DriverName", "TeamName"]]


def get_teams(year_to_fetch="Current"):
    if year_to_fetch == "Current":
        teams = []
        url = "https://www.formula1.com/en/teams"
        soup = get_soup(url)
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
    else:
        url = archive_url + year_to_fetch + "/team"
        df = get_table(get_soup(url))
        if df is None:
            return pd.DataFrame()
        df.rename(columns={"Team": "TeamName"}, inplace=True)
        df["Color"] = None
        return df[["TeamName", "Color"]]


def get_available_years():
    """fetch available years in archive"""
    soup = get_soup(archive_url)
    years = soup.find_all("a", class_="block")
    years = [
        year.get_text(strip=True)
        for year in years
        if year.get_text(strip=True).isnumeric()
    ]
    return years
