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


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    # Cellar Statistics Dashboard

    This dashboard provides basic analytics for notices stored in Cellar,
    including publication patterns, upload trends, and temporal distributions.
    """
    )
    return


@app.cell
def _():
    import altair as alt
    return (alt,)


@app.cell
def _():
    import pandas as pd
    import marimo as mo

    from pandas import json_normalize
    from SPARQLWrapper import SPARQLWrapper, JSON
    return JSON, SPARQLWrapper, mo, pd


@app.cell
def _(mo, period_end, period_start):
    mo.md(
        rf"""
    ## Select Analysis Period

    Choose the date range for your analysis. The dashboard will automatically update based on your selection.

    From {period_start} to {period_end}
    """
    )
    return


@app.cell
def _(mo):
    mo.md(
        rf"""
    ## Daily Notice Publications

    The chart below displays the number of Notices per day currently stored in Cellar, with the X-axis representing the publication date
    """
    )
    return


@app.cell
def _(notices):
    notices
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Cellar Upload Activity

    Daily uploads of Notices into Cellar, with the X-axis showing the upload date.
    """
    )
    return


@app.cell
def _(number_of_uploads):
    number_of_uploads
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Publication Date Range by Upload Date

    This visualization shows the range of publication dates for documents uploaded on each day. The vertical lines represent the min-max range of publication dates.
    """
    )
    return


@app.cell
def _(range_of_uploads):
    range_of_uploads
    return


@app.cell
def _(mo, notice_raw_count_query, pipeline_activity_query):
    mo.md(
        rf"""
    ## Queries

    Query for the number of notices by publication date

    ```sparql
    {notice_raw_count_query}
    ```

    Query for the number of notices uploaded to Cellar per day

    ```sparql
    {pipeline_activity_query}
    ```
    """
    )
    return


@app.cell
def _(alt, notice_raw_count):
    # define selection (click on bars)
    select_bar = alt.selection_point(fields=["date"], on="click")

    notices = (
        alt.Chart(notice_raw_count)
        .mark_bar()
        .encode(
            x=alt.X("date:T", title="Publication Date"),
            y=alt.Y("documentCount:Q", title="Documents"),
            color=alt.condition(
                select_bar, alt.value("steelblue"), alt.value("lightgray")
            ),
        )
        .add_params(select_bar)
    )
    return (notices,)


@app.cell
def _(mo):
    period_start = mo.ui.date(value="2025-01-01")
    period_end = mo.ui.date(value="2025-05-23")
    return period_end, period_start


@app.cell
def _(period_end, period_start):
    start_iso, end_iso = (
        period_start.value.isoformat(),
        period_end.value.isoformat(),
    )
    return end_iso, start_iso


@app.cell
def _(do_query, notice_raw_count_query, pd):
    notice_raw_count = do_query(notice_raw_count_query)
    notice_raw_count = notice_raw_count.assign(
        date=pd.to_datetime(notice_raw_count["date"], errors="coerce"),
        documentCount=pd.to_numeric(
            notice_raw_count["documentCount"], errors="coerce"
        ),
    )
    return (notice_raw_count,)


@app.cell
def _(do_query, pd, pipeline_activity_query):
    pipeline_activity = do_query(pipeline_activity_query)
    pipeline_activity = pipeline_activity.assign(
        dateUpdated=pd.to_datetime(
            pipeline_activity["dateUpdated"], errors="coerce"
        ),
        minPublicationDate=pd.to_datetime(
            pipeline_activity["minPublicationDate"], errors="coerce"
        ),
        maxPublicationDate=pd.to_datetime(
            pipeline_activity["maxPublicationDate"], errors="coerce"
        ),
        documentCount=pd.to_numeric(
            pipeline_activity["documentCount"], errors="coerce"
        ),
    )
    return (pipeline_activity,)


@app.cell
def _(alt, pipeline_activity):
    number_of_uploads = (
        alt.Chart(pipeline_activity)
        .mark_line(point=True)
        .encode(
            x=alt.X("dateUpdated:T", title="Cellar upload Date"),
            y=alt.Y("documentCount:Q", title="Number of documents"),
        )
    )
    return (number_of_uploads,)


@app.cell
def _(alt, pipeline_activity):
    range_of_uploads = (
        alt.Chart(pipeline_activity)
        .mark_rule(strokeWidth=4)  # fixed thickness
        .encode(
            y=alt.Y("minPublicationDate:T", title="Publication Date range"),
            y2="maxPublicationDate:T",
            x=alt.X("dateUpdated:T", title="Cellar upload Date"),
            color=alt.Color(
                "documentCount:Q", legend=alt.Legend(title="Documents")
            ),
            tooltip=[
                "dateUpdated:T",
                "minPublicationDate:T",
                "maxPublicationDate:T",
                "documentCount:Q",
            ],
        )
    )
    return (range_of_uploads,)


@app.cell
def _(end_iso, start_iso):
    notice_raw_count_query = """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX epo: <http://data.europa.eu/a4g/ontology#>
    PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>

    SELECT ?date
           (COUNT(?s) AS ?documentCount)
    WHERE {
      GRAPH ?metsNamedGraph {
        ?s a cdm:procurement_public .
        ?s cdm:work_date_document ?date .    
      }
      FILTER (?date >= "%s"^^xsd:dateTime &&
              ?date <= "%s"^^xsd:dateTime)
    }
    GROUP BY ?date
    ORDER BY ?date

    """ % (start_iso, end_iso)

    pipeline_activity_query = """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX epo: <http://data.europa.eu/a4g/ontology#>
    PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>

    SELECT ?dateUpdated
           (MIN(?date) AS ?minPublicationDate)
           (MAX(?date) AS ?maxPublicationDate)
           (COUNT(?s) AS ?documentCount)
    WHERE {
      GRAPH ?metsNamedGraph {
        ?s a cdm:procurement_public .
        ?s cdm:procurement_public_number_document_in_official-journal ?journalNumber .
        ?s cdm:work_date_document ?date .
        ?s <http://publications.europa.eu/ontology/cdm/cmr#lastModificationDate> ?cellarLastUpdated .

        BIND(STRDT(SUBSTR(STR(?cellarLastUpdated), 1, 10), xsd:date) AS ?dateUpdated)
      }
      FILTER (?cellarLastUpdated >= "%s"^^xsd:dateTime &&
              ?cellarLastUpdated <= "%s"^^xsd:dateTime)
    }
    GROUP BY ?dateUpdated
    ORDER BY ?dateUpdated

    """ % (start_iso, end_iso)
    return notice_raw_count_query, pipeline_activity_query


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
