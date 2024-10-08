"""Module for inferring ML-related attribute from each trial"""
from openai import OpenAI
from typing import List
import duckdb
import pandas as pd
from tqdm import tqdm

def _contains_chemo(interventions: str, client) -> bool:
    # client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": 'If any of the following treatments are typically considered chemotherapy, answer Y. If not, answer N. '
            },
            {
                "role": "user",
                "content": interventions
            }
        ]
    )
    response = completion.choices[0].message.content
    if response == 'Y':
        return True
    return False


def aggregated_contains_chemo(aggregated_interventions: List[str]) -> List[bool]:
    # TODO: Before running docker build:
    # 1. comment out default client initialization
    # 2. uncomment the custom client initialization by adding a real API key
    client = OpenAI()
    # client = OpenAI(api_key="<real_api_key>")
    
    contains_chemo_results = []
    for interventions in tqdm(aggregated_interventions):
        contains_chemo_results.append(_contains_chemo(interventions, client))
    return contains_chemo_results


def commit_inferred_data_to_duckdb(
    conn: duckdb.DuckDBPyConnection,
    inferred_df: pd.DataFrame,
) -> None:
    """Saves raw data from Pandas DataFrame into DuckDB table"""
    # Define schema for inferred data table
    conn.execute("""
    CREATE OR REPLACE TABLE trial_data_inferred (
        nctId VARCHAR,
        briefTitle VARCHAR,
        officialTitle VARCHAR,
        overallStatus VARCHAR,
        conditions VARCHAR,
        interventions VARCHAR,
        studyFirstPostDate VARCHAR,
        lastUpdatePostDate VARCHAR,
        phases VARCHAR,
        studyType VARCHAR,
        sex VARCHAR,
        minimumAge VARCHAR,
        maximumAge VARCHAR,
        contains_chemo BOOLEAN
    )
    """)

    # Populate the table from the Pandas DataFrame
    conn.execute(
        "INSERT INTO trial_data_inferred SELECT * FROM inferred_df"
    )

    # Commit the transaction to save changes
    conn.commit()
