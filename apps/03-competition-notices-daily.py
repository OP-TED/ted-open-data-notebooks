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
    import altair as alt
    import pandas as pd
    import marimo as mo
    import requests
    from vega_datasets import data

    from pandas import json_normalize
    from SPARQLWrapper import SPARQLWrapper, JSON
    return JSON, SPARQLWrapper, alt, data, mo, pd


@app.cell
def _(mo, selected_date):
    mo.md(
        rf"""
    # Information about competition notices published on a specific date

    Choose the date for your analysis. The dashboard will automatically update based on your selection.

    Select a date: {selected_date}
    """
    )
    return


@app.cell
def _(notices):
    notices
    return


@app.cell
def _(map):
    map
    return


@app.cell
def _(do_query, notices_per_day_query):
    notices = do_query(notices_per_day_query)
    return (notices,)


@app.cell
def _(create_country_map, notices):
    map = None 

    if len(notices):
        df = process_your_data(notices)
        map = create_country_map(df)
    return (map,)


@app.cell
def _(alt, data):
    def create_country_map(df, country_col='country', count_col='count'):
        # If count column doesn't exist, create it by counting occurrences
        if count_col not in df.columns:
            country_counts = df[country_col].value_counts().reset_index()
            country_counts.columns = [country_col, count_col]
        else:
            country_counts = df.groupby(country_col)[count_col].sum().reset_index()
        
        # Load world map data from vega_datasets
        countries = alt.topo_feature(data.world_110m.url, 'countries')

        # Your data already has numeric ISO codes, so just use them directly
        # Convert country codes to integers (they're already the right format)
        country_counts['id'] = country_counts[country_col].astype(int)

        # Add readable country names
        country_names = {
            40: 'Austria', 56: 'Belgium', 100: 'Bulgaria', 191: 'Croatia',
            196: 'Cyprus', 203: 'Czech Republic', 208: 'Denmark', 233: 'Estonia',
            246: 'Finland', 250: 'France', 276: 'Germany', 300: 'Greece',
            348: 'Hungary', 352: 'Iceland', 372: 'Ireland', 380: 'Italy',
            428: 'Latvia', 440: 'Lithuania', 442: 'Luxembourg', 470: 'Malta',
            528: 'Netherlands', 578: 'Norway', 616: 'Poland', 620: 'Portugal',
            642: 'Romania', 703: 'Slovakia', 705: 'Slovenia', 724: 'Spain',
            752: 'Sweden', 756: 'Switzerland', 826: 'United Kingdom'
        }
        country_counts['country_name'] = country_counts['id'].map(country_names)

        # Create the base map (gray background)
        base = alt.Chart(countries).mark_geoshape(
            fill='lightgray',
            stroke='white',
            strokeWidth=0.5
        ).properties(
            width=800,
            height=500
        ).project(
            type='mercator',
            scale=600,
            center=[10, 54]
        )

        # Create the choropleth layer (colored countries)
        choropleth = alt.Chart(countries).mark_geoshape(        ).transform_lookup(
            lookup='id',
            from_=alt.LookupData(country_counts, 'id', [count_col, 'country_name'])
        ).encode(
            color=alt.Color(
                f'{count_col}:Q',
                scale=alt.Scale(scheme='blues'),
                legend=alt.Legend(title='Publication Count')
            ),
            tooltip=[
                alt.Tooltip('country_name:N', title='Country'),
                alt.Tooltip(f'{count_col}:Q', title='Publications')
            ]
        ).properties(
            width=800,
            height=500
        ).project(
            type='mercator',
            scale=600,
            center=[10, 54]
        )

        # Combine base map and choropleth
        chart = base + choropleth

        return chart
    return (create_country_map,)


@app.function
def process_your_data(df):
    # Get country mapping
    country_mapping = get_country_mapping()
    
    # Filter for mapped countries only
    mapped_df = df[df['country'].isin(country_mapping.keys())].copy()
    
    # Check if any countries were mapped
    if len(mapped_df) == 0:
        available_countries = df['country'].unique().tolist()
        mapped_countries = list(country_mapping.keys())
        raise ValueError(f"No countries found in mapping! "
                        f"Available countries in data: {available_countries}. "
                        f"Countries in mapping: {mapped_countries}")
    
    # Count publications per country
    country_counts = mapped_df['country'].value_counts().reset_index()
    country_counts.columns = ['country_code', 'count']
    
    # Map to numeric country IDs
    country_counts['country'] = country_counts['country_code'].map(country_mapping)
    country_counts = country_counts.dropna(subset=['country'])
    
    # Final check - if mapping failed completely
    if len(country_counts) == 0:
        raise ValueError("All country mappings failed! No valid country codes found.")
    
    return country_counts[['country', 'count']]


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
    PREFIX cccev: <http://data.europa.eu/m8g/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX epo: <http://data.europa.eu/a4g/ontology#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?publicationNumber ?legalName ?procedureType ?country

    WHERE {

    	FILTER (?publicationDate = "%s"^^xsd:date)
    	FILTER (?formType = <http://publications.europa.eu/resource/authority/form-type/competition>)

      GRAPH ?g {
        ?notice
            epo:hasPublicationDate ?publicationDate ;
            epo:refersToProcedure [
                epo:hasProcedureType ?procedureTypeUri ;
                a epo:Procedure
            ] ;
            epo:hasNoticePublicationNumber ?publicationNumber ;
            epo:hasFormType ?formType ;
            epo:announcesRole [
                a epo:Buyer ;
                epo:playedBy [
                    epo:hasLegalName ?legalName ;
                    cccev:registeredAddress [
                        epo:hasCountryCode ?countryUri
                    ]
                ]
            ]
        }
    
        ?procedureTypeUri a skos:Concept ;
            skos:prefLabel ?procedureType.
        FILTER (lang(?procedureType) = "en")

        ?countryUri dc:identifier ?country .
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


@app.function
def get_country_mapping():
    """
    Mapping of 3-digit country codes to ISO numeric codes
    """
    return {
        'AUT': '040',  # Austria
        'BEL': '056',  # Belgium
        'BGR': '100',  # Bulgaria
        'HRV': '191',  # Croatia
        'CYP': '196',  # Cyprus
        'CZE': '203',  # Czech Republic
        'DNK': '208',  # Denmark
        'EST': '233',  # Estonia
        'FIN': '246',  # Finland
        'FRA': '250',  # France
        'DEU': '276',  # Germany
        'GRC': '300',  # Greece
        'HUN': '348',  # Hungary
        'IRL': '372',  # Ireland
        'ITA': '380',  # Italy
        'LVA': '428',  # Latvia
        'LTU': '440',  # Lithuania
        'LUX': '442',  # Luxembourg
        'MLT': '470',  # Malta
        'NLD': '528',  # Netherlands
        'POL': '616',  # Poland
        'PRT': '620',  # Portugal
        'ROU': '642',  # Romania
        'SVK': '703',  # Slovakia
        'SVN': '705',  # Slovenia
        'ESP': '724',  # Spain
        'SWE': '752',  # Sweden
        'GBR': '826',  # United Kingdom
        'NOR': '578',  # Norway
        'CHE': '756',  # Switzerland
        'ISL': '352',  # Iceland
        'LIE': '438',  # Liechtenstein
        'MKD': '807',  # North Macedonia
        'MNE': '499',  # Montenegro
        'SRB': '688',  # Serbia
        'ALB': '008',  # Albania
        'BIH': '070',  # Bosnia and Herzegovina
    }


if __name__ == "__main__":
    app.run()
