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


import rdflib.graph as g


def info_monument(monument_id, search):
    result = g.Graph()
    result.parse("dataset.ttl", format="ttl")
    query_text = """           
                ask where {
                    ?m a cis:CulturalInstituteOrSite ;
                    dc:identifier """ + monument_id + """ ;
                     """ + search + """ ?x .
                }
            """
    query = result.query(query_text)
    for r in query:
        if r:
            query_text = """
                        select distinct ?x where {
                            ?m a cis:CulturalInstituteOrSite ;
                            dc:identifier """ + monument_id + """ ;
                            """ + search + """ ?x .
                        }
                    """
            query = result.query(query_text)
            result_query = {}
            result_query[monument_id] = list()
            for row in query:
                if row[0] == "":
                    return -1
                a = row[0]
                result_query[monument_id].append(a)
            return result_query
        else:
            return -1


def id_monument(monument_name):
    result = g.Graph()
    result.parse("dataset.ttl", format="ttl")
    result_query = {}
    result_query[monument_name] = list()
    query_text = """
                    select distinct ?id where {
                    """ + monument_name + """ a cis:CulturalInstituteOrSite ;
                    dc:identifier ?id
                }
            """
    query = result.query(query_text)
    for row in query:
        result_query[monument_name].append(row[0])
    return result_query


def check_more_img(query_data):
    if info_monument(query_data, "pmo:nearbyCulturalInstituteOrSite") != -1:
        more_picture = info_monument(query_data, "pmo:nearbyCulturalInstituteOrSite")
        for x in range(0, len(more_picture[query_data]), 1):
            string = "<" + str(more_picture[query_data][x]) + ">"
            monument = id_monument(string)
            monument_id = monument[string][0]
            if info_monument(monument_id, "pmo:picture") != -1:
                return 1
    return -1