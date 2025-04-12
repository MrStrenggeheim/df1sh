import streamlit as st
import toml

SETTINGS_FILE = "./settings.toml"

def load_settings():
    """Load settings from the settings.toml file."""
    try:
        with open(SETTINGS_FILE, "r") as file:
            return toml.load(file)
    except FileNotFoundError:
        return {"dashboard": {"data_folder": "./data"}}

def save_settings(settings):
    """Save settings to the settings.toml file."""
    with open(SETTINGS_FILE, "w") as file:
        print("test")
        toml.dump(settings, file)

def main():
    st.title("Settings")

    # Load current settings
    settings = load_settings()

    # Dashboard settings
    st.header("Dashboard Settings")
    data_folder = st.text_input(
        "Data Folder",
        value=settings["dashboard"].get("data_folder", "./data"),
    )

    # Save button
    if st.button("Save Settings"):
        settings["dashboard"]["data_folder"] = data_folder
        save_settings(settings)
        st.success("Settings saved successfully!")

if __name__ == "__main__":
    main()