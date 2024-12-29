"""This module contains the functionality for the weather forecast model."""

import os
from datetime import datetime, timedelta, time
import pytz
import requests


class LocationNotFoundError(Exception):
    """Raise when the location is not found."""

    pass


def formated_weather_data(data: dict, for_predict: bool) -> dict:
    """Format the weather data to display in the app."""
    data["Rainfall"] = 0.00 if data["Rainfall"] < 0 else data["Rainfall"]
    data.update(
        {
            "MinTemp": f"{data['MinTemp']:.1f}°C",
            "MaxTemp": f"{data['MaxTemp']:.1f}°C",
            "Rainfall": f"{data['Rainfall']:.2f}mm",
            "WindGustSpeed": f"{data['WindGustSpeed']:.1f}kph",
            "WindSpeed9am": f"{data['WindSpeed9am']:.1f}kph",
            "WindSpeed3pm": f"{data['WindSpeed3pm']:.1f}kph",
            "Pressure9am": f"{data['Pressure9am']:.1f}hPa",
            "Pressure3pm": f"{data['Pressure3pm']:.1f}hPa",
            "Temp9am": f"{data['Temp9am']:.1f}°C",
            "Temp3pm": f"{data['Temp3pm']:.1f}°C",
        }
    )
    if for_predict:
        data["RainToday"] = f'{data["RainToday"]:.0%}'
    else:
        data.update(
            {
                "Humidity9am": f"{data['Humidity9am']:.0f}%",
                "Humidity3pm": f"{data['Humidity3pm']:.0f}%",
                "Cloud9am": f"{data['Cloud9am']:.0f}%",
                "Cloud3pm": f"{data['Cloud3pm']:.0f}%",
            }
        )
        del data["text"]
        del data["icon"]
    return data


def parse_history_response(response: dict, for_predict: bool) -> dict:
    """Parse the response from the history API to get the features."""
    day_feature_names = ["maxtemp_c", "mintemp_c", "totalprecip_mm"]
    hour_feature_names = [
        "wind_kph",
        "pressure_mb",
        "temp_c",
        "wind_dir",
        "humidity",
        "cloud",
    ]
    forecast_data = response["forecast"]["forecastday"][0]
    parse_dict = {k: forecast_data["day"][k] for k in day_feature_names}
    all_wind_gust = []
    need_times = [time(9, 0), time(15, 0)]
    for hour in forecast_data["hour"]:
        all_wind_gust.append(hour["gust_kph"])
        iter_time = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M").time()
        if iter_time in need_times:
            str_time = iter_time.strftime("%I%p")
            parse_dict.update({f"{k}{str_time}": hour[k] for k in hour_feature_names})
    parse_dict.update(
        {
            "max_gust": max(all_wind_gust),
            "rain_today": 1 if parse_dict["totalprecip_mm"] > 0 else 0,
        }
    )
    if not for_predict:
        feature_names_encoder = {
            "maxtemp_c": "MaxTemp",
            "mintemp_c": "MinTemp",
            "totalprecip_mm": "Rainfall",
            "max_gust": "WindGustSpeed",
            "wind_kph09AM": "WindSpeed9am",
            "wind_kph03PM": "WindSpeed3pm",
            "pressure_mb09AM": "Pressure9am",
            "pressure_mb03PM": "Pressure3pm",
            "temp_c09AM": "Temp9am",
            "temp_c03PM": "Temp3pm",
            "wind_dir09AM": "WindDir9am",
            "wind_dir03PM": "WindDir3pm",
            "humidity09AM": "Humidity9am",
            "humidity03PM": "Humidity3pm",
            "cloud09AM": "Cloud9am",
            "cloud03PM": "Cloud3pm",
            "rain_today": "RainToday",
        }
        parse_dict = {feature_names_encoder[k]: v for k, v in parse_dict.items()}
        condition_data = forecast_data["day"]["condition"]
        parse_dict.update(
            {"text": condition_data["text"], "icon": condition_data["icon"]}
        )
        parse_dict["RainToday"] = "Yes" if parse_dict["RainToday"] == 1 else "No"
    return parse_dict


def parse_current_response(response: dict) -> tuple[datetime.date, str, str]:
    """Parse the response from the current API."""
    location_data = response["location"]
    response_location = location_data["name"]
    response_country = location_data["country"]
    tz_id = location_data["tz_id"]
    tz = pytz.timezone(tz_id)
    now_date = datetime.now(tz).date()
    return now_date, response_location, response_country


def get_weather_data(
    location: str, for_predict: bool
) -> tuple[list[list[float]] | dict, str, str, datetime.date]:
    """Get the weather data for the location."""
    key = os.getenv("WEATHER_API_KEY")
    current_url = "http://api.weatherapi.com/v1/current.json"
    history_url = "http://api.weatherapi.com/v1/history.json"
    params = {"key": key, "q": location}
    response = requests.get(current_url, params=params)
    if response.status_code == 400:
        raise LocationNotFoundError()
    elif response.status_code > 400:
        response.raise_for_status()
    now_date, response_location, response_country = parse_current_response(
        response.json()
    )
    if response_country != "Australia":
        raise LocationNotFoundError()
    if not for_predict:
        params = {"key": key, "q": location, "dt": now_date.strftime("%Y-%m-%d")}
        response = requests.get(history_url, params=params)
        if response.status_code == 400:
            raise LocationNotFoundError()
        elif response.status_code > 400:
            response.raise_for_status()
        current_weather_data = parse_history_response(response.json(), for_predict)
        return current_weather_data, response_location, response_country, now_date

    features_order = [
        "mintemp_c",
        "maxtemp_c",
        "totalprecip_mm",
        "max_gust",
        "wind_kph09AM",
        "wind_kph03PM",
        "pressure_mb09AM",
        "pressure_mb03PM",
        "temp_c09AM",
        "temp_c03PM",
        "wind_dir09AM",
        "wind_dir03PM",
        "humidity09AM",
        "humidity03PM",
        "cloud09AM",
        "cloud03PM",
        "rain_today",
    ]
    n_days = 7
    features = []
    start_date = now_date - timedelta(days=6)
    prediction_date = now_date + timedelta(days=1)
    for i in range(n_days):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        params = {"key": key, "q": location, "dt": date}
        response = requests.get(history_url, params=params)
        if response.status_code == 400:
            raise LocationNotFoundError()
        elif response.status_code > 400:
            response.raise_for_status()
        parse_features = parse_history_response(response.json(), for_predict)
        features.append([parse_features[k] for k in features_order])
    return features, response_location, response_country, prediction_date


def predict(features: list[list[float]]):
    """Predict the weather forecast using the model."""
    url = "https://rnn-weather-forecast-api.onrender.com/predict/"
    response = requests.post(url, json={"data": features})
    response.raise_for_status()
    return response.json()
