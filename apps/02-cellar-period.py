# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "altair==5.4.1",
#     "marimo",
#     "sparqlwrapper==2.0.0",
#     "vega-datasets==0.9.0",
#     "pyarrow",
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
def _(bars, mo, scatter):
    chart = mo.ui.altair_chart(scatter & bars)
    chart
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
def _(mo):
    from datetime import date, timedelta

    today = date.today()
    three_months_ago = today - timedelta(days=90)

    period_start = mo.ui.date(
        value=three_months_ago,
        label="Start Date",
    )
    period_end = mo.ui.date(
        value=today,
        label="End Date",
    )

    return period_end, period_start, three_months_ago, today


@app.cell
def _(mo, three_months_ago, today):
    period = mo.ui.range_slider(start=three_months_ago, stop=today, label="Period")
    return


@app.cell
def _(mo):
    mo.ui.date(value="2022-01-01")
    return


@app.cell
def _(period_end, period_start):
    start_iso, end_iso = (
        period_start.value.isoformat(),
        period_end.value.isoformat(),
    )
    return end_iso, start_iso


@app.cell
def _(end_iso, start_iso):
    notice_raw_count_query = """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX epo: <http://data.europa.eu/a4g/ontology#>
    PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?publicationDate ?noticeTypeUri (COUNT(?notice) AS ?documentCount)
    WHERE {
      GRAPH ?g {
        ?notice a epo:Notice ;
                epo:hasPublicationDate ?publicationDate ;
                epo:hasNoticePublicationNumber ?publicationNumber ;
                epo:hasNoticeType ?noticeTypeUri .
        FILTER (?publicationDate >= "%s"^^xsd:dateTime &&
                ?publicationDate <= "%s"^^xsd:dateTime)
      }
    }
    GROUP BY ?publicationDate ?noticeTypeUri
    """ % (start_iso, end_iso)
    return (notice_raw_count_query,)


@app.cell
def _(do_query, notice_raw_count_query, notice_type_mapping, pd):
    notice_raw_count = do_query(notice_raw_count_query)
    notice_raw_count = notice_raw_count.assign(
        publicationDate=pd.to_datetime(notice_raw_count["publicationDate"], errors="coerce"),
        documentCount=pd.to_numeric(
            notice_raw_count["documentCount"], errors="coerce"
        ),
        noticeTypeLabel=notice_raw_count["noticeTypeUri"].map(notice_type_mapping)
    )
    return (notice_raw_count,)


@app.cell
def _():
    # This cell was cleaned up - unused chart definition removed
    return


@app.cell
def _(alt, notice_raw_count):

    # selection: brush on x axis
    brush = alt.selection_interval(encodings=["x"])

    # first chart: publication date histogram
    scatter = (
        alt.Chart(notice_raw_count)
        .mark_bar()
        .encode(
            x=alt.X("publicationDate:T", title="Publication Date"),
            y=alt.Y("documentCount:Q", title="Documents"),
        )
        .add_params(brush)
    )

    # second chart: notice type distribution filtered by brush
    bars = (
        alt.Chart(notice_raw_count)
        .mark_bar()
        .encode(
            x=alt.X("sum(documentCount):Q", title="Documents"),
            y=alt.Y("noticeTypeLabel:N", title="Notice Type"),
            color=alt.Color("noticeTypeLabel:N", legend=None),
            tooltip=[
                alt.Tooltip("noticeTypeLabel:N", title="Notice Type"),
                alt.Tooltip("sum(documentCount):Q", title="Document Count")
            ]
        )
        .transform_filter(brush)
    )
    return bars, scatter


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
    return (pipeline_activity_query,)


@app.cell
def _():
    notice_type_labels_query = """
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
    return (notice_type_labels_query,)


@app.cell
def _(do_query, notice_type_labels_query):
    # Fetch notice type labels (this runs once since labels never change)
    notice_type_labels_df = do_query(notice_type_labels_query)

    # Create mapping from URI to human-readable label
    notice_type_mapping = dict(zip(
        notice_type_labels_df["noticeTypeUri"],
        notice_type_labels_df["label"]
    ))
    return (notice_type_mapping,)


@app.cell
def _(JSON, SPARQLWrapper, mo, pd):
    sparql_service_url = "https://publications.europa.eu/webapi/rdf/sparql"


    def do_query(sparql_query):
        try:
            sparql = SPARQLWrapper(sparql_service_url, agent="Sparql Wrapper")
            sparql.setQuery(sparql_query)
            sparql.setReturnFormat(JSON)

            # ask for the result
            result = sparql.query().convert()
            return pd.DataFrame(result["results"]["bindings"]).map(lambda x: x["value"])
        except Exception as e:
            mo.md(f"⚠️ **Query Error**: {str(e)}")
            return pd.DataFrame()  # Return empty DataFrame on error
    return (do_query,)


if __name__ == "__main__":
    app.run()
