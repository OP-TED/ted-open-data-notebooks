# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "altair==5.4.1",
#     "marimo",
#     "vega-datasets==0.9.0",
# ]
# ///

import marimo

__generated_with = "0.13.10"
app = marimo.App(width="full")


@app.cell
def _():
    import pandas as pd
    import marimo as mo

    from pandas import json_normalize
    from SPARQLWrapper import SPARQLWrapper, JSON
    return JSON, SPARQLWrapper, mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md("""# Notice Statistics for a single day""")
    return


@app.cell
def _(mo, notices_per_day_query, selected_date):
    mo.md(
        rf"""
    Select a date: {selected_date}

    ```sparql
    {notices_per_day_query}
    ```
    """
    )
    return


@app.cell
def _(do_query, notices_per_day_query):
    notices = do_query(notices_per_day_query)
    notices
    return


@app.cell
def _(selected_date):
    notices_per_day_query = """
    PREFIX epo: <http://data.europa.eu/a4g/ontology#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>  
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT *
    WHERE {
        GRAPH ?g {
        FILTER (?publicationDate = "%s"^^xsd:date)
      	?notice a epo:Notice ; 
    		epo:hasPublicationDate ?publicationDate ;
            epo:hasOJSIssueNumber ?OJSIssueNumber ;
    	    epo:hasNoticePublicationNumber ?publicationNumber ;
    	    epo:hasNoticeType ?noticeTypeUri ;
    	    epo:hasFormType ?formTypeUri .
        }
    }
    """ % (selected_date.value.isoformat())
    return (notices_per_day_query,)


@app.cell
def _(JSON, SPARQLWrapper, pd):
    sparql_service_url = "https://publications.europa.eu/webapi/rdf/sparql"
    def do_query(sparql_query):
        sparql = SPARQLWrapper(sparql_service_url, agent="Sparql Wrapper")

        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)

        # ask for the result
        result = sparql.query().convert()
        pd.DataFrame(result["results"]["bindings"])
        return pd.DataFrame(result["results"]["bindings"]).map(lambda x: x["value"])
    return (do_query,)


@app.cell
def _(mo):
    selected_date = mo.ui.date(value="2025-05-23")
    return (selected_date,)


if __name__ == "__main__":
    app.run()
