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


import csv
import xml.etree.ElementTree as xml
from difflib import SequenceMatcher
import json
import pickle
import re
from geopy.distance import great_circle


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def write_monuments():
    with open("monuments.pickle", "wb") as file:
        pickle.dump(monuments, file)


def print_monuments():
    for monument in monuments:
        print(monument)


def read_csv():
    global id
    try:
        with open("monumenti_italia.csv", "r", encoding="latin-1") as inFile:
            reader = csv.reader(inFile, delimiter=';')
            for row in reader:
                name = row[3]
                city = row[1]
                latitude = row[9]
                longitude = row[8]
                if city.lower() == "palermo" and name != "":
                    duplicate = -1
                    for monument in monuments:
                        if similar(monument["nome"].replace("Palermo", ""), name.replace("Palermo", "")) > 0.67 \
                                or (monument["latitudine"] == latitude and monument["longitudine"] == longitude):
                            duplicate = monument["id"]
                    if duplicate == -1:
                        description = ""
                        if row[4] != "Monumento":
                            description = row[4]
                        monument = {"id": id,
                                    "nome": name,
                                    "descrizione": description,
                                    "latitudine": latitude,
                                    "longitudine": longitude,
                                    "comune": row[0],
                                    "link_img": "",
                                    "altre_img": list(),
                                    "storiche_img": list(),
                                    "monumenti_vicini": list(),
                                    "uguale": list()}
                        monuments.append(monument)
                        id += 1
    except FileNotFoundError:
        print("File not found!")


def read_xml():
    global id
    try:
        tree = xml.parse("VIS_DATASET_TURISMO03.xml")
        root = tree.getroot()
        for data in root.findall('DATA_RECORD'):
            if data.find('LATITUDE').text != "0" and data.find('LONGITUDE').text != "0":
                monument = {"id": id,
                            "nome": data.find('DENOMINAZIONE').text,
                            "descrizione": data.find('CENNI_STORICI').text,
                            "latitudine": data.find('LATITUDE').text,
                            "longitudine": data.find('LONGITUDE').text,
                            "comune": data.find('CITTA').text,
                            "link_img": "",
                            "altre_img": list(),
                            "storiche_img": list(),
                            "monumenti_vicini": list(),
                            "uguale": list()}
                monuments.append(monument)
                id += 1
    except FileNotFoundError:
        print("File not found!")


def read_json():
    global id
    with open("dataset-luoghiSicilia.json", "r") as inFile:
        data = json.load(inFile)['@graph']
        for row in data:
            if str(row["@type"]).__contains__  ("cis:CulturalInstituteOrSite"):
                name = row["rdfs:label"]["@value"]
                duplicate = -1
                for monument in monuments:
                    if similar(monument["nome"].replace("Palermo", ""), name.replace("Palermo", "")) > 0.87:
                        duplicate = monument["id"]
                if duplicate == -1 and "geo:lat" in row and "geo:long" in row:
                    description = ""
                    if "l0:description" in row:
                        temp = row["l0:description"]
                        if "@value" in temp:
                            description = row["l0:description"]["@value"]
                            description = clean_html(description)
                    img = ""
                    if "foaf:depiction" in row:
                        img = row["foaf:depiction"]["@id"]
                    city = ""
                    province = ""
                    for row1 in data:
                        if row1["@id"] == row["cis:hasSite"]["@id"]:
                            for row2 in data:
                                if row2["@id"] == row1["cis:siteAddress"]["@id"]:
                                    city = row2["clvapit:hasCity"]["@id"][57:].replace("_", " ")
                                    province = row2["clvapit:hasProvince"]["@id"][61:]
                    if province == "Palermo":
                        monument = {"id": id,
                                    "nome": name,
                                    "descrizione": description,
                                    "latitudine": row["geo:lat"],
                                    "longitudine": row["geo:long"],
                                    "comune": city,
                                    "link_img": img,
                                    "altre_img": list(),
                                    "storiche_img": list(),
                                    "monumenti_vicini": list(),
                                    "uguale": list()}
                        monuments.append(monument)
                        id += 1


def find_near_monuments():
    for monument in monuments:
        monument_coordinates = (monument["latitudine"], monument["longitudine"])
        for other_monument in monuments:
            other_monument_coordinates = (other_monument["latitudine"], other_monument["longitudine"])
            dist = great_circle(monument_coordinates, other_monument_coordinates).meters
            if dist < 250 and monument != other_monument:
                monument["monumenti_vicini"].append(other_monument["id"])


def clean_html(raw_html):
    regex = re.compile("<.*?>")
    raw_html = re.sub(regex, '', raw_html)
    return raw_html.replace("&nbsp", "")


def clean_locations():
    for monument in monuments:
        monument["latitudine"] = monument["latitudine"].replace(",", ".")
        monument["longitudine"] = monument["longitudine"].replace(",", ".")


id = 0
monuments = list()
read_xml()
read_json()
read_csv()
clean_locations()
find_near_monuments()
write_monuments()
#print_monuments()
