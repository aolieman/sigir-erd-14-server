# -*- coding: utf-8 -*-
"""
Functions for offline evaluation, e.g. using
the TREC example queries and annotations.
"""
import csv, requests, os, json
import pandas as pd

# Use a corrected golden standard for long track
fp_gs = "evaluation/golden_standard_1906.tsv"

def query_server(query_list, run_id, url):
    """Sends queries to a running server.
    """
    out_str = ""
    for query in query_list:
        payload = {
                    'runID': run_id,
                    'TextID': query[0],
                    'Text': query[1]
        }
        resp = requests.post(url, data=payload)
        if resp.status_code != 200:
            print "Breaking due to non-200 response"
            break
        out_str += resp.content
        
    f_path = os.path.join("evaluation/system_output", run_id + ".tsv")
    abs_path = os.path.abspath(f_path)
    with open(abs_path, 'w') as f:
        f.write(out_str[1:]) # strip initial newline
    
    return abs_path

# Short track

def read_tsv_queries(file_path="../Trec_beta.query.txt"):
    with open(file_path, 'r') as f:
        return [r for r in csv.reader(
                    f, delimiter='\t', quoting=csv.QUOTE_NONE
        )]
        

# Long track

def read_document_queries(dir_path="evaluation/documents"):
    doc_file_names = sorted([fn for fn in os.listdir(dir_path) 
                             if fn.endswith(".txt")])
    query_list = []
    
    for fn in doc_file_names:
        text_id = fn[:-4]
        with open(os.path.join(dir_path, fn), 'rb') as f:
            doc_text = f.read()
        query_list.append((text_id, doc_text))
        
    return query_list

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
    return data_and_stats
    
def f_score(precision, recall, beta):
    return (1+beta**2)*(precision*recall)/((beta**2*precision)+recall)
    

def multiple_runs_long(run_id_list, url):
    query_list = read_document_queries()
    
    for run_id in run_id_list:
        fp_so = query_server(query_list, run_id, url)
        comparison_df = load_comparison(fp_gs, fp_so)
        data_and_stats = calculate_performance(comparison_df)
        dir_path = "evaluation/error_analyses/{0}".format(run_id)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        f_path = os.path.join(dir_path, "{0}.{1}")
        for k, v in data_and_stats.items():
            try:
                v.to_csv(f_path.format(k, "tsv"), sep="\t", encoding='utf8', index=False)
            except AttributeError:
                print run_id, k, v
                with open(f_path.format(k, "json"), 'wb') as f:
                    json.dump(v, f, sort_keys=True)