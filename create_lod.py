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


from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, OWL, XSD, DC
import pickle
import re


def read_monuments():
    with open("monuments.pickle", "rb") as file:
        return pickle.load(file)


def clean_name(name):
    name = name.replace(" d'", "").replace(" D'", "").replace(" o dei ", "").replace(" o di ", "")
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"[\'\"\-]", "", name)
    name = name.replace(" della ", "").replace(" delle", "").replace(" detta ", ""). \
                replace(" dell", "").replace(" alla ", "").replace(" gli ", "").replace(" all", ""). \
                replace(" di ", "").replace("à", "a").replace("é", "e").replace(" al ", ""). \
                replace("è", "e").replace("ò", "o").replace("ù", "u").replace(" degli ", ""). \
                replace(" il ", "").replace(" lo ", "").replace(" la ", "").replace(" i ", ""). \
                replace(" le ", "").replace(" del ", "").replace(" ai ", ""). \
                replace(" La ", "").replace(" dei ", "").replace(" o ", "").replace(" e ", ""). \
                replace(" in ", "").replace(" a ", "").replace(" da ", "").replace(" ", "")
    return name


def create_lod(graph):
    graph.serialize(destination='dataset.ttl', format='turtle')


def create_graph():
    g = Graph()
    pmo = Namespace("http://www.palermo.monumenti.it/ontology/")
    cis = Namespace("http://dati.beniculturali.it/cis/")
    dbo = Namespace("http://dbpedia.org/ontology/")
    g.bind("cis", cis)
    g.bind("pmo", pmo)
    g.bind("dbo", dbo)
    g.bind("owl", OWL)
    g.bind("dc", DC)
    base_monument_uri = "http://www.palermo.monumenti.it/resource/monuments/"

    cities_uri = list()
    for monument in monuments:
        base_dbpedia = "http://dbpedia.org/resource/"
        city = monument["comune"].replace(" ", "_")
        if city == "Alia":
            city = "Alia,_Sicily"
        elif city == "Cefalu":
            city = "Cefalù"
        cities_uri.append(base_dbpedia + city)

    monuments_uri = list()
    for monument in monuments:
        monument_name = clean_name(monument["nome"])
        monuments_uri.append(base_monument_uri + monument_name)

    for monument in monuments:
        monument_uri = monuments_uri[monument["id"]]
        g.add([URIRef(monument_uri), RDF.type, cis.CulturalInstituteOrSite])
        g.add([URIRef(monument_uri), DC.identifier, Literal(monument["id"], datatype=XSD.integer)])
        g.add([URIRef(monument_uri), cis.institutionalName, Literal(monument["nome"], lang='it')])
        g.add([URIRef(monument_uri), pmo.city, URIRef(cities_uri[monument["id"]])])
        g.add([URIRef(monument_uri), dbo.lat, Literal(monument["latitudine"], datatype=XSD.double)])
        g.add([URIRef(monument_uri), dbo.long, Literal(monument["longitudine"], datatype=XSD.double)])
        if monument["descrizione"] != "":
            g.add([URIRef(monument_uri), cis.description, Literal(monument["descrizione"], lang='it')])
        if monument["link_img"] != "":
            g.add([URIRef(monument_uri), pmo.picture, URIRef(monument["link_img"])])
        for reference in monument["altre_img"]:
            g.add([URIRef(monument_uri), pmo.picture, URIRef(reference)])
        for reference in monument["storiche_img"]:
            g.add([URIRef(monument_uri), pmo.oldPicture, URIRef(reference)])
        for reference in monument["monumenti_vicini"]:
            g.add([URIRef(monument_uri), pmo.nearbyCulturalInstituteOrSite, URIRef(monuments_uri[reference])])
        for reference in monument["uguale"]:
            g.add([URIRef(monument_uri), OWL.sameAs, URIRef(reference)])

    return g


monuments = read_monuments()
g = create_graph()
create_lod(g)
