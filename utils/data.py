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
results = "https://www.formula1.com/en/results/2024/races"

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
    soup = get_soup(results)
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


def refactor_df(df: pd.DataFrame):
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
    drivers_df = pd.read_csv(DATA_FOLDER + "/drivers.csv")
    df = update_teams(df, drivers_df)

    return df


def save_results_to_csv():
    os.makedirs(DATA_FOLDER + "/races", exist_ok=True)
    for location, info in get_locations().items():
        link = info["link"]

        soup = get_soup(base_url + link)

        # Get the race results
        race = get_table(soup)
        race = refactor_df(race)
        race.to_csv(f"{DATA_FOLDER}/races/race_{location}.csv", index=False)
        # Get the sprint results
        sprint = get_sprint(soup)
        if sprint is not None:
            sprint = refactor_df(sprint)
            sprint.to_csv(f"{DATA_FOLDER}/races/sprint_{location}.csv", index=False)
