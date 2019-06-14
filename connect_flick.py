
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
from difflib import SequenceMatcher
import pickle
import urllib.request
from geopy.distance import great_circle


def read_monuments():
    with open("monuments.pickle", "rb") as file:
        return pickle.load(file)


def write_monuments():
    with open("monuments.pickle", "wb") as file:
        pickle.dump(monuments, file)


def read_img_locations():
    with open("img_locations.pickle", "rb") as file:
        return pickle.load(file)


def write_img_locations():
    with open("img_locations.pickle", "wb") as file:
        pickle.dump(info_img, file)


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def print_monuments():
    for monument in monuments:
        print(monument)


def get_photos_locations(request):
    photo_data = json.loads(urllib.request.urlopen(request).read())['photos']["photo"]
    for img in photo_data:
        photo_id = "&photo_id=" + img["id"]
        geo_url = BASE_API + GET_PHOTO_GEO + KEY_API + photo_id + FORMAT
        geo_data = json.loads(urllib.request.urlopen(geo_url).read())
        if "photo" in geo_data:
            geo_data = json.loads(urllib.request.urlopen(geo_url).read())["photo"]["location"]
            photo_coordinates = (geo_data["latitude"], geo_data["longitude"])
            info_img[img["id"]] = photo_coordinates


def get_photos(request):
    photo_data = json.loads(urllib.request.urlopen(request).read())['photos']["photo"]
    for monument in monuments:
        for img in photo_data:
            flickr_title = img['title'].replace("Palermo -", "")
            if similar(monument['nome'].replace("Palermo", ""), flickr_title.replace("Palermo", "")) > 0.8:
                monument["storiche_img"].append(BASE_FLICKR + img["id"])
                photo_data.remove(img)
        for img in photo_data:
            if img["id"] in info_img:
                photo_coordinates = info_img[img["id"]]
                monument_coordinates = (monument["latitudine"], monument["longitudine"])
                dist = great_circle(monument_coordinates, photo_coordinates).meters
                if dist < 50:
                    monument["storiche_img"].append(BASE_FLICKR + img["id"])


def get_num_page(url):
    n_page = json.loads(urllib.request.urlopen(url).read())['photos']
    return n_page['pages']


BASE_API = "https://api.flickr.com/services/rest/?method="
GET_PHOTO = "flickr.people.getPhotos"
GET_PHOTO_GEO = "flickr.photos.geo.getLocation"
KEY_API = "&api_key=XXXX"
USER_ID = "&user_id=140129279@N05"
BASE_FLICKR = "https://www.flickr.com/photos/biblioteca-comunale-palermo/"
FORMAT = "&format=json&nojsoncallback=1"
N_FOR_PAGE = "&per_page=500"

monuments = read_monuments()
url = BASE_API + GET_PHOTO + KEY_API + USER_ID + FORMAT + N_FOR_PAGE
n = get_num_page(url)
info_img = read_img_locations()
"""
for num_page in range(1, n+1):
    request = BASE_API + GET_PHOTO + KEY_API + USER_ID + FORMAT + N_FOR_PAGE + "&page="
    request += str(num_page)
    get_photos_locations(request)
write_img_locations()
"""
for num_page in range(1, n + 1):
    request = BASE_API + GET_PHOTO + KEY_API + USER_ID + FORMAT + N_FOR_PAGE + "&page="
    request += str(num_page)
    get_photos(request)
write_monuments()
