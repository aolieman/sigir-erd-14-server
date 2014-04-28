# -*- coding: utf-8 -*-
"""
API client functions that offload requests
to a DBpedia Spotlight server.
"""

import urllib2, json
from spotlight import annotate, candidates, SpotlightException
from functools import partial


def through_spotlight(spotlight_url, text, cand_param, conf=0.0, supp=0):
    if cand_param == "single":
        cand_uri = "annotate"
        cand_function = annotate
    elif cand_param == "multi":
        cand_uri = "candidates"
        cand_function = candidates
    else: raise Exception("Incorrect cand_param provided")
    api_url = spotlight_url + cand_uri

    no_coref_filter = {
        'coreferenceResolution': False
    }

    api = partial(cand_function, api_url,
                  confidence=conf, support=supp,
                  spotter='Default', filters=no_coref_filter)
    try:
        spotlight_response = api(text)
    except (SpotlightException, TypeError) as err:
        print err
        return None
        
    annotations = []
    if cand_param == "single":
        for ann in spotlight_response:
            ann[u'URI'] = urllib2.unquote(ann[u'URI'].split('resource/')[-1])
            annotations.append(ann)
    elif cand_param == "multi":
        for ann in spotlight_response:
            if u'resource' in ann:
                if isinstance(ann[u'resource'], dict):
                    ann[u'resource'][u'uri'] = urllib2.unquote(ann[u'resource'][u'uri'])
                    ann[u'resource'] = [ann[u'resource']]
                else:
                    for cand in ann[u'resource']:
                        cand[u'uri'] = urllib2.unquote(cand[u'uri'])
                annotations.append(ann)
    return annotations

def short_output(target_db, text_id, spotlight_url,
                 text, conf=0.0, supp=0, posr=0.0):
    """
    Get annotations from DBp Spotlight and format them as TSV.
    
    target_db: dict with target entities in this ERD challenge
    text_id: query id string given in the request
    spotlight_url: URL of a DBpedia Spotlight REST endpoint (incl. trailing slash)
    text: input text in UTF-8 encoding
    conf: confidence threshold for DBp Spotlight
    supp: support threshold for DBp Spotlight
    posr: minimum 'percentage of second rank' to include further candidates
    """
    out_str = ""
    text = text.decode('utf8')
    annotations = through_spotlight(spotlight_url, text, 'multi', conf, supp)
    
    # Append annotations to a log file
    with open("logs/short_annotations.json", 'a') as f:
        json.dump(annotations, f, indent=4, separators=(',', ': '))
        f.write(",\n")
    
    if not annotations:
        return ""
    
    for ann in annotations:
        i = 0
        for cand in ann[u'resource']:
            if cand[u'uri'] in target_db:
                fid = target_db[cand[u'uri']][0]
                mention = ann[u'name']
                score = u"{0:.2f}".format(cand[u'finalScore'])
                out_str += u"\n" + u"\t".join(
                    (text_id, str(i), fid, mention, score)
                )
                i += 1
            
            if cand[u'percentageOfSecondRank'] < posr:
                break
                
    return out_str.encode('utf8')
    
def long_output(target_db, text_id, spotlight_url,
                text, conf=0.0, supp=0):
    """
    Get annotations from DBp Spotlight and format them as TSV.
    
    target_db: dict with target entities in this ERD challenge
    text_id: query id string given in the request
    spotlight_url: URL of a DBp Spotlight REST endpoint (incl. trailing slash)
    text: input text in UTF-8 encoding
    conf: confidence threshold for DBp Spotlight
    supp: support threshold for DBp Spotlight
    """
    out_str = ""
    text = text.decode('utf8')
    annotations = through_spotlight(spotlight_url, text, 'single', conf, supp)
    
    # Write annotations to a log file
    with open("logs/long/{0}_annotations.json".format(text_id), 
              'wb') as f:
        json.dump(annotations, f, indent=4, separators=(',', ': '))
    
    if not annotations:
        return ""
        
    for ann in annotations:
        if ann['URI'] in target_db:
            fid = target_db[ann['URI']][0]
            mention = str(ann[u'surfaceForm'])
            begin_offset = str(ann[u'offset'])
            end_offset = str(ann[u'offset'] + len(mention))
            score = u"{0:.2f}".format(ann[u'similarityScore'])
            out_str += u"\n" + u"\t".join(
                (text_id, begin_offset, end_offset, 
                 fid, ann['URI'], mention, score, "0")
            )
            
    return out_str.encode('utf8')
    