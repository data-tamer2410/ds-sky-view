"""Main module for the Sky View app."""

import streamlit as st
from sky_view.functionality import (
    get_weather_data,
    LocationNotFoundError,
    predict,
    formated_weather_data,
)


@st.cache_resource
def load_locations():
    """Load the locations from the file."""
    with open("sky_view/locations.txt", "r", encoding="utf-8") as f:
        locations = [line.strip() for line in f]
        locations.append("Other")
        return locations


def toggle_logic() -> None:
    """Toggle the color and state of the toggle button."""
    st.session_state["color_today"] = (
        "green" if st.session_state["color_today"] == "red" else "red"
    )
    st.session_state["color_tomorrow"] = (
        "green" if st.session_state["color_tomorrow"] == "red" else "red"
    )
    st.session_state["toggle_state"] = st.session_state["toggle_state"] is False


def main():
    """Main function for the Sky View app."""
    _, middle, _ = st.columns([10, 11, 10])
    middle.title(
        ":blue[Sky View] [![GitHub](https://img.icons8.com/ios-glyphs/50/000000/github.png)]"
        "(https://github.com/data-tamer2410/ds-sky-view)",
        anchor=False,
    )
    st.divider()
    with st.expander("**About**", icon=":material/info:"):
        st.write(
            """Sky View is a weather forecasting platform designed specifically for Australia.
               The project leverages the API of a pre-trained neural network to predict weather conditions. 
               The model takes weather data from the past seven days and generates predictions for the next day.
               Additionally, the platform integrates a weather forecast API to fetch the necessary input data for 
               predictions. All complex logic is handled internally, so you don’t need to worry about understanding
               API usage or other technical details. To check the current or tomorrow’s weather, simply select a
               location within Australia, set the toggle to display either today’s or tomorrow’s forecast, and click
               the "Check the Weather" button.
            """
        )

    locations = load_locations()
    col1, col2 = st.columns([2, 1])
    location = col1.selectbox(
        "**Select Location**",
        locations,
        index=None,
        help="If you don't see the desired location, "
        "select 'Other' from the list and enter your preferred location in the new text field.",
    )
    if location == "Other":
        location = st.text_input("**Write your Location**")

    if "color_today" not in st.session_state:
        st.session_state.color_today = "green"
    if "color_tomorrow" not in st.session_state:
        st.session_state.color_tomorrow = "red"
    if "toggle_state" not in st.session_state:
        st.session_state.toggle_state = False
    col2.write("**Check the Weather for**:")
    col2.toggle(
        f":{st.session_state['color_today']}[**Today**]/:{st.session_state['color_tomorrow']}[**Tomorrow**]",
        on_change=toggle_logic,
        value=st.session_state["toggle_state"],
    )

    _, col2, _ = st.columns([10, 7, 10])
    with st.spinner():
        if col2.button("**Check the Weather**"):
            if location is None or location.strip() == "":
                st.error("**Please select a location.**")
            else:
                try:
                    if st.session_state["color_today"] == "green":
                        weather_data, location_name, country_name, date = (
                            get_weather_data(location, for_predict=False)
                        )
                    else:
                        weather_features, location_name, country_name, date = (
                            get_weather_data(location, for_predict=True)
                        )
                        weather_data = predict(weather_features)
                    col1, _, col3 = st.columns(3)
                    col1.write(f"{location_name}, {country_name} - {date}")
                    if st.session_state["color_today"] == "green":
                        col1.write(f'**Description**: {weather_data["text"]}.')
                        col3.markdown(f"!['icon']({weather_data['icon']})")
                    col1, _, col3 = st.columns(3)
                    for_predict = st.session_state["color_today"] == "red"
                    weather_data = formated_weather_data(
                        weather_data, for_predict=for_predict
                    )
                    for i, (k, v) in enumerate(
                        sorted(weather_data.items(), key=lambda x: x[0])
                    ):
                        if i % 2 == 0:
                            col1.write(f"**{k}**: {v}")
                        else:
                            col3.write(f"**{k}**: {v}")
                except LocationNotFoundError:
                    st.error(
                        "**Location not found. Please enter a valid location in Australia.**"
                    )
                except Exception as e:
                    st.write(e)
                    st.error(
                        "**Sorry, the service is temporarily unavailable. Please try again later.**"
                    )


if __name__ == "__main__":
    main()
