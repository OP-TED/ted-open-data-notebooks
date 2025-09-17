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
    import requests

    from pandas import json_normalize
    from SPARQLWrapper import SPARQLWrapper, JSON
    return JSON, SPARQLWrapper, mo, pd, requests


@app.cell
def _(mo, selected_date):
    mo.md(
        rf"""
    # Notice Statistics for a single day

    Choose the date for your analysis. The dashboard will automatically update based on your selection.

    Select a date: {selected_date}
    """
    )
    return


@app.cell
def _(do_query, notices_per_day_query):
    notices = do_query(notices_per_day_query)
    notices
    return (notices,)


@app.cell
def _(chart1, chart2, chart3, mo):
    mo.hstack([chart1, chart2, chart3])
    return


@app.cell
def _(mo, notices, selected_date, ted_daily):
    mo.md(
        rf"""
    ## Comparison with TED API

    Notices in Cellar for {selected_date.value.isoformat()}: **{len(notices)} Notices**

    Notices reported by TED API for the same day: **{ted_daily["totalNoticeCount"]} Notices**
    """
    )
    return


@app.cell
def _(mo, notices_per_day_query):
    mo.md(
        rf"""
    ## Queries

    The following query was used

    ```sparql
    {notices_per_day_query}
    ```
    """
    )
    return


@app.cell
def _(selected_date):
    notices_per_day_query = """
    PREFIX epo: <http://data.europa.eu/a4g/ontology#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?publicationNumber ?OJSIssueNumber ?procedureType ?noticeType ?formType

    WHERE {

      FILTER (?publicationDate = "%s"^^xsd:date)

      GRAPH ?g {
        ?notice a epo:Notice ;
                epo:hasPublicationDate ?publicationDate ;
                epo:hasNoticePublicationNumber ?publicationNumber ;
                 epo:hasOJSIssueNumber ?OJSIssueNumber ;
                epo:hasNoticeType ?noticeTypeUri ;
                epo:hasFormType ?formTypeUri ;
                epo:refersToProcedure [
                     a epo:Procedure ;
                     epo:hasProcedureType ?procedureTypeUri
               ] .
      }

      # Retrieve the label in english for noticeTypeUri
      ?noticeTypeUri a skos:Concept ;
                     skos:prefLabel ?noticeType .
      FILTER (lang(?noticeType) = "en")

      # Retrieve the label in english for formTypeUri
      ?formTypeUri a skos:Concept ;
                   skos:prefLabel ?formType .
      FILTER (lang(?formType) = "en")

      # Retrieve the label in english for procedureTypeUri
      ?procedureTypeUri a skos:Concept ;
                        skos:prefLabel ?procedureType .
      FILTER (lang(?procedureType) = "en")
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


@app.cell
def _(get_daily_notices, selected_date):
    ted_daily = get_daily_notices(selected_date.value.isoformat())
    return (ted_daily,)


@app.cell
def _(requests):
    def get_daily_notices(date: str) -> dict:
        date_formatted = date.replace("-", "")
        # api_url = "https://api.ted.europa.eu/v3/notices/search" # Has CORS problems
        api_url = "https://api.acceptance.ted.europa.eu/v3"

        request_body = {
            "query": f"publication-date = {date_formatted}",
            "scope": "ALL",
            "fields": ["publication-date"],
        }

        response = requests.post(
            api_url, headers={"Accept": "application/json"}, json=request_body
        )

        result = response.json()
        return result
    return (get_daily_notices,)


@app.cell
def _(notices):
    import altair as alt

    # Chart 1 - Procedure Type
    chart1 = (
        alt.Chart(notices)
        .mark_arc(innerRadius=60)
        .encode(
            color=alt.Color("procedureType:N", title="Procedure Type"),
            theta=alt.Theta("count():Q", title="Count"),
            tooltip=[
                alt.Tooltip("count()", title="Count"),
                alt.Tooltip("procedureType:N", title="Procedure Type"),
            ],
        )
        .properties(
            height=290,
            width=250,
            title="Procedure Type Distribution",  # You can customize each title
        )
        .configure_axis(grid=False)
    )

    # Chart 2 - Notice Type
    chart2 = (
        alt.Chart(notices)
        .mark_arc(innerRadius=60)
        .encode(
            color=alt.Color("noticeType:N", title="Notice Type"),
            theta=alt.Theta("count():Q", title="Count"),
            tooltip=[
                alt.Tooltip("count()", title="Count"),
                alt.Tooltip("noticeType:N", title="Notice Type"),
            ],
        )
        .properties(
            height=290,
            width=250,
            title="Notice Type Distribution",
        )
        .configure_axis(grid=False)
    )

    # Chart 3 - Form Type
    chart3 = (
        alt.Chart(notices)
        .mark_arc(innerRadius=60)
        .encode(
            color=alt.Color("formType:N", title="Form Type"),
            theta=alt.Theta("count():Q", title="Count"),
            tooltip=[
                alt.Tooltip("count()", title="Count"),
                alt.Tooltip("formType:N", title="Form Type"),
            ],
        )
        .properties(
            height=290,
            width=250,
            title="Form Type Distribution",
        )
        .configure_axis(grid=False)
    )
    return chart1, chart2, chart3


if __name__ == "__main__":
    app.run()
