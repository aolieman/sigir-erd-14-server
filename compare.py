# -*- coding: utf-8 -*-
import urllib2
from spotlight import annotate, candidates, SpotlightException
from functools import partial

def through_spotlight(text, cand_param, conf=0.0, supp=0):
    if cand_param == "single":
        cand_uri = "annotate"
        cand_function = annotate
    elif cand_param == "multi":
        cand_uri = "candidates"
        cand_function = candidates
    else: raise Exception("Incorrect cand_param provided")
    en_sztaki = 'http://spotlight.sztaki.hu:2222/rest/%s' % cand_uri
    en_cleverdon = 'http://cleverdon.hum.uva.nl:8082/rest/%s' % cand_uri

    no_coref_filter = {
        'coreferenceResolution': False
    }

    api = partial(cand_function, en_sztaki,
                  confidence=conf, support=supp,
                  spotter='Default', filters=no_coref_filter)
    try:
        spotlight_response = api(text)
    except SpotlightException as err:
        print err
        return None
    except TypeError as err:
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
