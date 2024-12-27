import pandas as pd
import streamlit as st

DATA_FOLDER = "./data"


def main():
    st.title("Team Data Configuration")
    df_teams = pd.read_csv(DATA_FOLDER + "/teams.csv")

    st.header("Edit Teams")
    df_teams = st.data_editor(df_teams, num_rows="dynamic", use_container_width=True)
    if st.button("Save Teams"):
        df_teams.to_csv(DATA_FOLDER + "/teams.csv", index=False)
        st.success("Teams saved successfully!")


if __name__ == "__main__":
    main()
