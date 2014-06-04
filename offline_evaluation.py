# -*- coding: utf-8 -*-
"""
Functions for offline evaluation, e.g. using
the TREC example queries and annotations.
"""
import csv, requests
import pandas as pd

# Short track

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

# Long track

def load_comparison(fp_golden_standard, fp_sys_output):
    gs = pd.read_csv(fp_golden_standard, sep="\t", encoding='utf8', quotechar='~', header=None)
    # NB: remove any rows in sys_output that correspond to DocIDs not included in golden_standard
    so = pd.read_csv(fp_sys_output, sep="\t", encoding='utf8', quotechar='~', header=None)
    headers = ['DocID', 'begin', 'end', 'FbID', 'AltID', 'mention', 'conf', 'altconf']
    gs.columns = so.columns = headers
    return pd.merge(gs, so, how='outer', on=headers[:2], suffixes=('_gs', '_so'))
    
def calculate_performance(comparison_df):
    comp = comparison_df
    TP_df = comp[comp.FbID_gs == comp.FbID_so]
    FP_df = comp[(comp.FbID_gs != comp.FbID_so) & (comp.FbID_so.notnull())]
    FN_df = comp[comp.FbID_so.isnull()]
    # Discern between FP caused by NIL and disambiguation
    FP_should_be_NIL_df = FP_df[FP_df.FbID_gs.isnull()]
    FP_wrong_disambiguation_df = FP_df[FP_df.FbID_gs.notnull()]
    
    assert len(TP_df) + len(FP_df) == comp.FbID_so.count(), "TP + FP should equal all sys_output"
    assert len(FP_wrong_disambiguation_df) + len(TP_df) + len(FN_df) == comp.FbID_gs.count(), "Incorrect disambiguations + TP + FN should equal all golden_standard"
    
    overall_precision = float(len(TP_df)) / comp.FbID_so.count()
    overall_recall = float(len(TP_df)) / comp.FbID_gs.count()
    overall_F1 = f_score(overall_precision, overall_recall, 1)
    FP_frac_wrong_disambiguation = len(FP_wrong_disambiguation_df) / float(len(FP_df))
    FP_frac_should_be_NIL = len(FP_should_be_NIL_df) / float(len(FP_df))
    
    # Per-document statistics
    tp_per_doc = TP_df.DocID.value_counts()
    tp_per_doc.name = 'TP'
    fp_per_doc = FP_df.DocID.value_counts()
    fp_per_doc.name = 'FP'
    fn_per_doc = FN_df.DocID.value_counts()
    fn_per_doc.name = 'FN'
    fp_nil_per_doc = FP_should_be_NIL_df.DocID.value_counts()
    fp_nil_per_doc.name = 'FP (should be NIL)'
    fp_dis_per_doc = FP_wrong_disambiguation_df.DocID.value_counts()
    fp_dis_per_doc.name = 'FP (wrong disambiguation)'
    
    stats_per_doc = pd.concat([tp_per_doc, fp_per_doc, fn_per_doc,
                               fp_nil_per_doc, fp_dis_per_doc], axis=1)
    spd = stats_per_doc.fillna(0)
    spd['precision'] = spd.TP / (spd.TP + spd.FP)
    spd['recall'] = spd.TP / (spd.TP + spd.FN)
    spd['F1'] = f_score(spd.precision, spd.recall, 1)
    spd_means = spd.mean(axis=0)
    
    overview = {
        'overall_precision': overall_precision, 
        'overall_recall': overall_recall,
        'overall_F1': overall_F1,
        'average_precision': spd_means.precision,
        'average_recall': spd_means.recall,
        'average_F1': spd_means.F1,
        'FP_wrong_disambiguation': FP_frac_wrong_disambiguation,
        'FP_should_be_NIL': FP_frac_should_be_NIL
    }
    
    data_and_stats = {
        'overview': overview,
        'stats_per_doc': spd,
        'TP_df': TP_df,
        'FP_df': FP_df,
        'FN_df': FN_df,
        'FP_should_be_NIL_df': FP_should_be_NIL_df,
        'FP_wrong_disambiguation_df': FP_wrong_disambiguation_df
    }
    print overview
    return data_and_stats
    
def f_score(precision, recall, beta):
    return (1+beta**2)*(precision*recall)/((beta**2*precision)+recall)
    
fp_gs = r'G:\MyData\Dropbox\ExPoSe\golden_standard.tsv'
fp_so = r'G:\MyData\ExPoSe\SIGIR ERD 2014\sigir-erd-14-server\logs\long\dbp_sz_c0.3_s0_single.tsv'
    