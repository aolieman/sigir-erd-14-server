# -*- coding: utf-8 -*-
"""Helper functions to deal with the vocabulary a.k.a. target database.
"""
import sys, csv, pickle
import mqlkey

def get_target_db():
    print "Loading target_db...",
    sys.stdout.flush()
    try:
        tdb = pickle.load(open('target_db.pickle', 'rb'))
        print "Done!"
    except IOError:
        print "Reading TSV"
        tdb = read_target_db(verbosity=1)
    return tdb

def read_target_db(fpath="../entity.tsv", verbosity=0):
    '''Read the target db into a dict with wiki_id as keys
    '''
    target_db = {}
    
    with open(fpath, 'rb') as tsvf:
        vreader = csv.reader(tsvf, delimiter='\t')
        for i, row in enumerate(vreader):
            if verbosity == 1:
                if i % 1000 == 0:
                    print "Loaded %i entries" % (i,)
            elif verbosity > 1:
                print i, row[2].split('en_title/')[1]
                
            wiki_id = mqlkey.unquotekey(row[2].split('en_title/')[1])
            target_db[wiki_id] = tuple(row)
            
    print "Dumping target_db.pickle ...",
    sys.stdout.flush()
    pickle.dump(target_db, open('target_db.pickle', 'wb'))
    print "Done!"
            
    return target_db