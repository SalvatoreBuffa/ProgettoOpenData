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


import pickle
from SPARQLWrapper import SPARQLWrapper, JSON
from difflib import SequenceMatcher


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def read_monuments():
    with open("monuments.pickle", "rb") as file:
        return pickle.load(file)


def write_monuments():
    with open("monuments.pickle", "wb") as file:
        pickle.dump(monuments, file)


def print_monuments():
    for monument in monuments:
        print(monument)


def query_sparql(endpoint, query):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def interlinking_monuments(results, index):
    for monument in monuments:
        for result in results:
            if similar(result["nome"]["value"].replace("Palermo", "").replace("()", ""),
                       monument["nome"].replace("Palermo", "")) > index:
                monument["uguale"].append(result["monumento"]["value"])
                if "immagine" in result:
                    if monument["link_img"] == "":
                        monument["link_img"] = str(result["immagine"]["value"])
                    else:
                        monument["altre_img"].append(str(result["immagine"]["value"]))


monuments = read_monuments()
results = query_sparql("http://dati.beniculturali.it/sparql",
                       """
                            select distinct ?monumento ?nome where { 
                                ?monumento a cis:CulturalInstituteOrSite.
                                ?monumento rdfs:label ?nome. 
                                ?monumento cis:hasSite ?sito. 
                                ?sito cis:siteAddress ?indirizzo.
                                ?indirizzo clvapit:hasProvince <http://dati.beniculturali.it/mibact/luoghi/resource/Province/Palermo>.
                            }
                       """)
interlinking_monuments(results["results"]["bindings"], 0.85)
results = query_sparql("https://dbpedia.org/sparql",
                       """
                            select distinct ?monumento ?nome ?immagine where {
                                ?monumento a <http://dbpedia.org/ontology/ArchitecturalStructure> .
                                ?monumento rdfs:label ?nome .
                                filter (lang(?nome)="it") .
                                {
                                      ?monumento dbp:location ?luogo .
                                      filter regex(?luogo, "[Pp]alermo") .
                                }
                                UNION
                                {
                                      ?monumento dbo:location <http://dbpedia.org/resource/Palermo> .
                                }
                                optional {?monumento dbo:thumbnail ?immagine .}  
                            }
                       """)
interlinking_monuments(results["results"]["bindings"], 0.87)
write_monuments()
