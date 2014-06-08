# -*- coding: utf-8 -*-
"""
API client functions that offload requests
to a DBpedia Spotlight server.
"""

import urllib2, json
from spotlight import annotate, candidates, SpotlightException
from functools import partial

class SpotlightCallConfiguration(object):
    def __init__(self, url, cand_param, conf=0.0, supp=0, posr=0.0, strf=None):
        self.url = url
        self.cand_param = cand_param
        self.conf = conf
        self.supp = supp
        self.posr = posr
        self.strf = strf
        
    def __repr__(self):
        repr_params = {k: repr(v) for k, v in self.__dict__.items()}
        return "<SpotlightCallConfiguration(url={url}, cand_param={cand_param}, \
                conf={conf}, supp={supp}, posr={posr}, strf={strf})>".format(**repr_params)

def through_spotlight(spotlight_call_config, text):
    scc = spotlight_call_config
    if scc.cand_param == "single":
        cand_uri = "annotate"
        cand_function = annotate
    elif scc.cand_param == "multi":
        cand_uri = "candidates"
        cand_function = candidates
    else: raise Exception("Incorrect cand_param provided")
    api_url = scc.url + cand_uri

    no_coref_filter = {
        'coreferenceResolution': False
    }

    api = partial(cand_function, api_url,
                  confidence=scc.conf, support=scc.supp,
                  spotter='Default', filters=no_coref_filter)
    try:
        if spotlight_call_config.strf:
            text = spotlight_call_config.strf(text)
        spotlight_response = api(text)
    except (SpotlightException, TypeError) as err:
        print err
        return None
        
    annotations = []
    if scc.cand_param == "single":
        for ann in spotlight_response:
            ann[u'URI'] = urllib2.unquote(ann[u'URI'].split('resource/')[-1])
            annotations.append(ann)
    elif scc.cand_param == "multi":
        for ann in spotlight_response:
            if u'resource' in ann:
                if isinstance(ann[u'resource'], dict):
                    ann[u'resource'][u'uri'] = unicode(ann[u'resource'][u'uri'])
                    ann[u'resource'][u'uri'] = urllib2.unquote(ann[u'resource'][u'uri'])
                    ann[u'resource'] = [ann[u'resource']]
                else:
                    for cand in ann[u'resource']:
                        cand[u'uri'] = urllib2.unquote(unicode(cand[u'uri']))
                annotations.append(ann)
    return annotations

def short_output(target_db, text_id, text, spotlight_call_config):
    """
    Get annotations from DBp Spotlight and format them as TSV.
    
    target_db: dict with target entities in this ERD challenge
    text_id: query id string given in the request
    spotlight_url: URL of a DBpedia Spotlight REST endpoint (incl. trailing slash)
    text: input text in unicode
    conf: confidence threshold for DBp Spotlight
    supp: support threshold for DBp Spotlight
    posr: minimum 'percentage of second rank' to include further candidates
    """
    out_str = ""
    
    if isinstance(spotlight_call_config, SpotlightCallConfiguration):
        spotlight_call_config.cand_param = "multi"    
        annotations = through_spotlight(spotlight_call_config, text)
    else:
        primary_config, additional_config = spotlight_call_config
        annotations = get_merged_candidates(primary_config, additional_config, text)
        spotlight_call_config = primary_config
    
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
            
            if cand[u'percentageOfSecondRank'] < spotlight_call_config.posr:
                break
                
    return out_str
    
def long_output(target_db, text_id, text, spotlight_call_config):
    """
    Get annotations from DBp Spotlight and format them as TSV.
    
    target_db: dict with target entities in this ERD challenge
    text_id: query id string given in the request
    spotlight_url: URL of a DBp Spotlight REST endpoint (incl. trailing slash)
    text: input text in unicode
    conf: confidence threshold for DBp Spotlight
    supp: support threshold for DBp Spotlight
    cand_param:
        "single" for post-disambiguation filtering
        "multi" for pre-disambiguation filtering (first cand in target_db)
    """
    out_str = ""
    
    if isinstance(spotlight_call_config, SpotlightCallConfiguration):  
        annotations = through_spotlight(spotlight_call_config, text)
    else:
        primary_config, additional_config = spotlight_call_config
        annotations = get_merged_candidates(primary_config, additional_config, text)
        spotlight_call_config = primary_config
    
    # Write annotations to a log file
    with open("logs/long/{0}_annotations.json".format(text_id), 
              'wb') as f:
        json.dump(annotations, f, indent=4, separators=(',', ': '))
    
    if not annotations:
        return ""
        
    # Check if text contains non-ASCII characters
    needs_offset_conversion = len(text) != len(text.encode('utf8'))
        
    for ann in annotations:
        if spotlight_call_config.cand_param == "single":
            if ann['URI'] in target_db:
                fid = target_db[ann['URI']][0]
                mention = unicode(ann[u'surfaceForm'])
                begin_offset, end_offset = get_byte_offsets(
                    text, ann[u'offset'], mention, needs_offset_conversion
                )
                score = u"{0:.2f}".format(ann[u'similarityScore'])
                out_str += u"\n" + u"\t".join(
                    (text_id, begin_offset, end_offset, 
                     fid, ann['URI'], mention, score, "0")
                )
        elif spotlight_call_config.cand_param == "multi":
            for cand in ann[u'resource']:
                if cand[u'uri'] in target_db:
                    fid = target_db[cand[u'uri']][0]
                    mention = unicode(ann[u'name'])
                    begin_offset, end_offset = get_byte_offsets(
                        text, ann[u'offset'], mention, needs_offset_conversion
                    )
                    f_score = u"{0:.2f}".format(cand[u'finalScore'])
                    c_score = u"{0:.2f}".format(cand[u'contextualScore'])
                    out_str += u"\n" + u"\t".join(
                        (text_id, begin_offset, end_offset, 
                         fid, cand[u'uri'], mention, f_score, c_score)
                    )
                    break
            
    return out_str
    
def get_byte_offsets(text, u_begin, substr, needs_conversion):
    if needs_conversion:
        begin_offset = len(text[:u_begin].encode('utf8'))
        end_offset = begin_offset + len(substr.encode('utf8'))
    else:
        begin_offset = u_begin
        end_offset = u_begin + len(substr)
    return str(begin_offset), str(end_offset)
    

def get_merged_candidates(primary_config, additional_config, text):
    primary_annotations = through_spotlight(primary_config, text)
    additional_annotations = through_spotlight(additional_config, text)
    
    offset_mapping = {ann['offset']: ann for ann in (primary_annotations or [])}
    
    for ann in (additional_annotations or []):
        if ann['offset'] in offset_mapping:
            existing_ann = offset_mapping[ann['offset']]
            existing_uris = {cand['uri'] for cand in existing_ann['resource']}
            for cand in ann['resource']:
                if cand['uri'] not in existing_uris:
                    existing_ann['resource'].append(cand)
        else:
            offset_mapping[ann['offset']] = ann
            
    return [offset_mapping[offset] for offset in sorted(offset_mapping)]
