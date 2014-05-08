# -*- coding: utf-8 -*-
"""
Build a modified DBpedia Spotlight model by manipulating the raw data.
"""
import os, json, urllib2
from vocabulary import read_target_db

target_db = read_target_db()

def uri_to_id(uri, split_str="resource/"):
    """Split and unquote a URI to obtain a unicode ID.
    """
    id_part = uri.split(split_str)[-1]
    if id_part.startswith('/'):
        id_part = id_part[1:]
    return urllib2.unquote(id_part)
    

def rewrite_tsv(file_path, rewrite_row):
    """Loop through the file at file_path and call
    rewrite_row for each row. Modified rows are written
    to a new output file.
    """
    path, fname = os.path.split(file_path)
    dirpath, dirname = os.path.split(path)
    out_fpath = os.path.join(dirpath, dirname+"_modified", fname)
    

# UriCounts, TokenCounts
# TODO: deal with redirects & disambiguation pages
## if unicode_id not in target_db: del row


# PairCounts
"""Pseudocode
for row in tsvreader:
    if unicode_id not in target_db:
        count_change[surface_form] -= count
        del row
    elif not surface_form.islower():
        count_change[surface_form] += count
        duplicate row with surface_form.lower()
json.dump(count_change, f)
"""

# SFandTotalCounts
"""Pseudocode
for row in tsvreader:
    this_change = count_change.pop(surface_form, 0)
    if this_change:
        if count < 0:
            count = this_change
        else:
            count += this_change
        if count <= 0:
            count = -1
for sf, cc in count_change.iteritems():
    append row [sf, cc, -1]
"""