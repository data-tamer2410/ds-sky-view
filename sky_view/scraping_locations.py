"""This script scrapes the locations from the website and writes them to a file."""

from bs4 import BeautifulSoup
import requests

response = requests.get(
    "https://answers.id.com.au/answers/all-cities-and-towns-in-australia-by-population"
)
soup = BeautifulSoup(response.text, "html.parser")

locations = []
all_locations = soup.find("table").find_all("tr")
for location in all_locations:
    location_name = location.find("td").text
    locations.append(f"{location_name.strip()}\n")

with open("sky_view/locations.txt", "w", encoding="utf-8") as f:
    f.writelines(locations)
