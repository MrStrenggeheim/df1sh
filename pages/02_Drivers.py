import pandas as pd
import streamlit as st
import utils.style as style

DATA_FOLDER = "./data"


def main():
    st.title("Driver Data Configuration")
    df_drivers = pd.read_csv(DATA_FOLDER + "/drivers.csv")
    df_teams = pd.read_csv(DATA_FOLDER + "/teams.csv")

    st.header("Edit Drivers")
    df_drivers = st.data_editor(
        df_drivers,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "TeamName": st.column_config.SelectboxColumn(
                "TeamName", options=df_teams["TeamName"].tolist(), required=True
            ),
        },
    )
    if st.button("Save Drivers"):
        df_drivers.to_csv(DATA_FOLDER + "/drivers.csv", index=False)
        st.success("Drivers saved successfully!")


if __name__ == "__main__":
    style.set_page_config()
    main()
