# -*- coding: utf-8 -*-
"""
Functions for offline evaluation, e.g. using
the TREC example queries and annotations.
"""
import csv, requests

def read_tsv_queries(file_path="../Trec_beta.query.txt"):
    with open(file_path, 'r') as f:
        return [r for r in csv.reader(
                    f, delimiter='\t', quoting=csv.QUOTE_NONE
        )]
        

def query_local_server(query_list, run_id):
    """Sends queries to a local server.
    Assumes a server listens locally on port 5000.
    """
    for query in query_list:
        payload = {
                    'runID': run_id,
                    'TextID': query[0],
                    'Text': query[1]
        }
        url = "http://localhost:5000/short"
        resp = requests.post(url, data=payload)
        print payload
        if resp.status_code != 200:
            break
