# -*- coding: utf-8 -*-
"""
Build a modified DBpedia Spotlight model by manipulating the raw data.
"""
import os, json, urllib2, sys, re
import unicodecsv as csv
from collections import defaultdict
from vocabulary import get_target_db

csv.field_size_limit(sys.maxint)
target_db = get_target_db()

def uri_to_id(uri, split_str="resource/"):
    """Split and unquote a URI to obtain a unicode ID.
    """
    id_part = uri.split(split_str)[-1]
    if id_part.startswith('/'):
        id_part = id_part[1:]
    return urllib2.unquote(id_part.encode('utf-8')).decode('utf-8')
    

def rewrite_tsv(file_path, rewrite_row, count_deltas=None):
    """Loop through the file at file_path and call
    rewrite_row for each row. Modified rows are written
    to a new output file.
    """
    path, fname = os.path.split(file_path)
    dirpath, dirname = os.path.split(path)
    out_dirpath = os.path.join(dirpath, dirname+"_modified")
    if not os.path.exists(out_dirpath):
        os.makedir(out_dirpath)
    
    with open(file_path, 'rb') as in_f:
        tsvr = csv.reader(
            in_f, delimiter='\t', encoding='utf-8', quotechar="|",
            quoting=csv.QUOTE_NONE, lineterminator='\n'
        )
        with open(os.path.join(out_dirpath, fname), 'wb') as out_f:
            tsvw = csv.writer(
                out_f, delimiter='\t', encoding='utf-8', quotechar="|",
                quoting=csv.QUOTE_NONE, lineterminator='\n', escapechar=None
            )
            for i, row in enumerate(tsvr):
                mod_rows = rewrite_row(row, count_deltas)
                for row in mod_rows:
                    try:
                        tsvw.writerow(row)
                    except csv.Error:
                        clean = clean_row(row)
                        tsvw.writerow(clean)
                if i % 10000 == 0:
                    print "Processed %i0K rows from %s" % (i/10000, file_path)
                
    return count_deltas, out_dirpath
    
def clean_row(row):
    clean = []
    print "clean_row(%s)" % repr(row)
    for col in row:
        if isinstance(col, basestring):
            clean.append(re.sub(r'\W+', '', col.split('\t')[0]))
        else:
            clean.append(col)
    return clean

# UriCounts, TokenCounts
# TODO: deal with redirects & disambiguation pages
## if unicode_id not in target_db: del row
def uri_counts(file_path):
    def dbp_filter(row, _):
        if uri_to_id(row[0]) in target_db:
            return [row]
        else:
            return []
            
    rewrite_tsv(file_path, dbp_filter)
    
def token_counts(file_path):    
    def wiki_filter(row, _):
        if uri_to_id(row[0], split_str='wiki/') in target_db:
            return [row]
        else:
            return []
            
    rewrite_tsv(file_path, wiki_filter)

# PairCounts
"""Pseudocode
for row in tsvreader:
    if unicode_id not in target_db:
        count_deltas[surface_form] -= count
        del row
    elif not surface_form.islower():
        count_deltas[surface_form.lower()] += count
        duplicate row with surface_form.lower()
json.dump(count_deltas, f)
"""
def pair_counts(file_path):
    def lowercase_duplicate(row, count_deltas):
        if uri_to_id(row[1]) in target_db and len(row[0]) < 70:
            if not row[0].islower():
                count_deltas[row[0].lower()] += int(row[2])
                add_row = [row[0].lower(), row[1], row[2]]
                return [row, add_row]
            else:
                return [row]
        else:
            count_deltas[row[0]] -= int(row[2])
            return []
            
    deltas_dict = defaultdict(int)
    count_deltas, base_path = rewrite_tsv(
        file_path, lowercase_duplicate, deltas_dict
    )
    cd_path = os.path.join(base_path, "count_deltas.json")
    with open(cd_path, 'wb') as jfile:
        json.dump(count_deltas, jfile)
    return count_deltas

# SFandTotalCounts
"""Pseudocode
for row in tsvreader:
    this_change = count_deltas.pop(surface_form, 0)
    if this_change:
        if count < 0:
            count = this_change
        else:
            count += this_change
        if count <= 0:
            count = -1
for sf, dc in count_deltas.iteritems():
    append row [sf, dc, -1]
"""
def sf_and_total_counts(file_path, count_deltas, add_lowercase=True):
    def update_counts(row, count_deltas):
        this_change = count_deltas.pop(row[0], 0)
        if this_change:
            sf_count, total_count = int(row[1]), int(row[2] or -1)
            for count in (sf_count, total_count):
                if count < 0:
                    count = this_change
                else:
                    count += this_change
                if count <= 0:
                    count = -1
            if max(sf_count, total_count) > 0:
                return [[row[0], sf_count, total_count]]
            else:
                return []
        else:
            return [row]
                    
    _, base_path = rewrite_tsv(file_path, update_counts, count_deltas)
    
    if add_lowercase:
        # Add rows for lowercase duplicates
        _, fname = os.path.split(file_path)
        with open(os.path.join(base_path, fname), 'a') as out_f:
            tsvw = csv.writer(
                out_f, delimiter='\t', encoding='utf-8', quoting=csv.QUOTE_NONE,
                lineterminator='\n', escapechar=None, quotechar="|"
            )
            print "Adding {0} lowercase duplicates".format(len(count_deltas))
            for sf, dc in count_deltas.iteritems():
                if dc > 0:
                    tsvw.writerow(clean_row([sf, dc, -1]))
    
# Rewrite all raw data files
def rewrite_all(base_path):
    uri_counts(os.path.join(base_path, "uriCounts"))
    token_counts(os.path.join(base_path, "tokenCounts"))
    count_deltas = pair_counts(os.path.join(base_path, "pairCounts"))
    sf_and_total_counts(
        os.path.join(base_path, "sfAndTotalCounts"), count_deltas, add_lowercase=False
    )
    return count_deltas