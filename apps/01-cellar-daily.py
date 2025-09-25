# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "altair==5.4.1",
#     "marimo",
#     "vega-datasets==0.9.0",
#     "pyarrow",
#     "pandas",
#     "requests",
#     "SPARQLWrapper",
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
    # Cellar Notice Statistics for a single day

    Choose the date for your analysis. The dashboard will automatically update based on your selection.

    Select a date: {selected_date}
    """
    )
    return


@app.cell
def _(do_query, notices_per_day_query):
    notices_raw = do_query(notices_per_day_query)
    return (notices_raw,)


@app.cell
def _(form_type_dict, mo, notice_type_dict, notices_raw):
    notices = notices_raw.copy()
    if (len(notices)):
        notices['noticeType'] = notices['noticeTypeUri'].map(notice_type_dict)
        notices['formType'] = notices['formTypeUri'].map(form_type_dict)

        # Create TED URL for each notice
        notices['tedUrl'] = notices['publicationNumber'].apply(
            lambda x: f"https://ted.europa.eu/en/notice/-/detail/{x}"
        )

        # Remove URI columns
        notices = notices.drop(columns=['noticeTypeUri', 'formTypeUri'])

        # Reorder columns
        notices = notices[['publicationNumber', 'noticeType', 'formType', 'tedUrl']]

    mo.ui.table(notices, selection=None)
    return (notices,)


@app.cell
def _(
    chart1,
    chart2,
    mo,
    notice_types,
    notices,
    selected_date,
    ted_daily,
    ted_daily_same_set,
):
    mo.md(
        rf"""
    ## Comparison with TED API

    ### Day: {selected_date.value.isoformat()}

    - Cellar
        - Number of notices: **{len(notices)}**
        - Notice types found: {notice_types}
    - TED API
        - Notices matching these types: **{ted_daily_same_set["totalNoticeCount"]}**
        - Total notices reported: **{ted_daily["totalNoticeCount"]}**

    ## Notice distribution

    {mo.hstack([chart1, chart2])}
    """
    )
    return


@app.cell
def _(mo, notices_per_day_query):
    mo.md(
        rf"""
    (## Queries

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
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?publicationNumber ?noticeTypeUri ?formTypeUri

    WHERE {
      GRAPH ?g {
        ?notice a epo:Notice ;
                epo:hasPublicationDate ?publicationDate ;
                epo:hasNoticePublicationNumber ?publicationNumber ;
                epo:hasNoticeType ?noticeTypeUri ;
                epo:hasFormType ?formTypeUri .    
      }
      FILTER (?publicationDate = "%s"^^xsd:date)
    }
    """ % (selected_date.value.isoformat())
    return (notices_per_day_query,)


@app.cell
def _(do_query):
    # Fetch notice type labels (cached)
    notice_type_query = """
    PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX epo: <http://data.europa.eu/a4g/ontology#>
    PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?noticeTypeUri ?label
    WHERE {
      ?noticeTypeUri a skos:Concept ;
          skos:topConceptOf <http://publications.europa.eu/resource/authority/notice-type> ;
          skos:prefLabel ?label .
      FILTER (lang(?label) = "en") .
    }
    """

    notice_type_labels = do_query(notice_type_query)
    notice_type_dict = dict(zip(notice_type_labels['noticeTypeUri'], notice_type_labels['label']))
    return (notice_type_dict,)


@app.cell
def _(do_query):
    # Fetch form type labels (cached)
    form_type_query = """
    PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX epo: <http://data.europa.eu/a4g/ontology#>
    PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?formTypeUri ?label
    WHERE {
      ?formTypeUri a skos:Concept ;
          skos:topConceptOf <http://publications.europa.eu/resource/authority/form-type> ;
          skos:prefLabel ?label .
      FILTER (lang(?label) = "en") .
    }
    """

    form_type_labels = do_query(form_type_query)
    form_type_dict = dict(zip(form_type_labels['formTypeUri'], form_type_labels['label']))
    return (form_type_dict,)


@app.cell
def _(get_default_date, mo):
    selected_date = mo.ui.date(value=get_default_date().isoformat())
    return (selected_date,)


@app.cell
def _(fetch_ted_daily_notices, selected_date):
    ted_daily = fetch_ted_daily_notices(selected_date.value.isoformat())
    return (ted_daily,)


@app.cell
def _(fetch_ted_daily_notices, notices_raw, selected_date):
    notice_types = get_distinct_notice_types(notices_raw)

    ted_daily_same_set = (
        {"totalNoticeCount": 0, "results": []}
        if not notice_types
        else fetch_ted_daily_notices(selected_date.value.isoformat(), notice_types)
    )
    return notice_types, ted_daily_same_set


@app.cell
def _():
    from datetime import datetime, timedelta

    def get_default_date():
        """Get yesterday's date, but if today is Sunday, get Friday instead"""
        today = datetime.now()
        if today.weekday() == 6:  # Sunday is 6
            return (today - timedelta(days=2)).date()  # Friday
        else:
            return (today - timedelta(days=1)).date()  # Yesterday

    return (get_default_date,)


@app.function
def get_distinct_notice_types(notices_raw) -> list[str]:
    uris = getattr(notices_raw, "noticeTypeUri", None)
    if uris is None:
        return []
    return sorted({uri.rsplit("/", 1)[-1] for uri in uris})


@app.cell
def _(requests):

    def fetch_ted_daily_notices(date: str, notice_types: list[str] | None = None) -> dict:
        date_formatted = date.replace("-", "")
        api_url = "https://api.acceptance.ted.europa.eu/v3/notices/search"

        # Base condition
        conditions = [f"publication-date = {date_formatted}"]

        # Add notice type filter if provided
        if notice_types:
            type_conditions = [f"notice-type = {nt}" for nt in notice_types]
            conditions.append("(" + " or ".join(type_conditions) + ")")

        query_str = " and ".join(conditions)

        request_body = {
            "query": query_str,
            "scope": "ALL",
            "fields": ["publication-date", "notice-type"],
        }

        response = requests.post(
            api_url, headers={"Accept": "application/json"}, json=request_body
        )
        response.raise_for_status()

        return response.json()
    return (fetch_ted_daily_notices,)


@app.cell
def _(notices):
    import altair as alt

    # Chart 1 - Notice Type (Bar Chart)
    chart1 = (
        alt.Chart(notices)
        .mark_bar()
        .encode(
            x=alt.X("count():Q", title="Count"),
            y=alt.Y("noticeType:N", title="Notice Type", sort="-x"),
            color=alt.Color("noticeType:N", title="Notice Type", legend=None),
            tooltip=[
                alt.Tooltip("count()", title="Count"),
                alt.Tooltip("noticeType:N", title="Notice Type"),
            ],
        )
        .properties(
            height=290,
            width=400,
            title="Notice Type Distribution",
        )
    )

    # Chart 2 - Form Type (Bar Chart)
    chart2 = (
        alt.Chart(notices)
        .mark_bar()
        .encode(
            x=alt.X("count():Q", title="Count"),
            y=alt.Y("formType:N", title="Form Type", sort="-x"),
            color=alt.Color("formType:N", title="Form Type", legend=None),
            tooltip=[
                alt.Tooltip("count()", title="Count"),
                alt.Tooltip("formType:N", title="Form Type"),
            ],
        )
        .properties(
            height=290,
            width=400,
            title="Form Type Distribution",
        )
    )
    return chart1, chart2


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


if __name__ == "__main__":
    app.run()
