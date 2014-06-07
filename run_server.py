# -*- coding: utf-8 -*-
"""
Run a Flask server that responds to requests in the ERD14 format.
"""

import logging, string
from logging import handlers
from flask import Flask, request
from vocabulary import get_target_db
from spotlight_client import short_output, long_output, SpotlightCallConfiguration


# Read the target db into a dict
target_db = get_target_db()

# Initialize a Flask instance
app = Flask(__name__)

# Set up logging
handler = handlers.RotatingFileHandler(
    'logs/all_queries.tsv', maxBytes=67000, backupCount=1
)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# Initialize runtime parameters
spotlight_url = "http://spotlight.sztaki.hu:2222/rest/"
conf = 0.3
supp = 0
posr = 0.0
cand_param = "single"
strf = None

##
# Flask views
##
@app.route('/echo', methods=['POST'])
def echo():
    # Get request parameter values
    run_id = request.form['runID']
    text_id = request.form['TextID']
    text = redecode_utf8(request.form['Text'])
    
    body_str = run_id+"\n"+text_id+"\n\n"+text
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    return (body_str, 200, headers)

@app.route('/short', methods=['POST'])
def short_track(target_db=target_db):
    # Get request parameter values
    run_id = request.form['runID']
    text_id = request.form['TextID']
    text = redecode_utf8(request.form['Text'])
    spotlight_config = parse_configuration(run_id)
    
    body_str = short_output(target_db, text_id, text, spotlight_config)
        
    app.logger.warning("\t".join((text_id, text, run_id)))
    with open("logs/{0}.tsv".format(run_id), 'a') as f:
        f.write(body_str)       
        
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    
    return (body_str, 200, headers)

@app.route('/long', methods=['POST'])
def long_track():
    # Get request parameter values
    run_id = request.form['runID']
    text_id = request.form['TextID']
    text = redecode_utf8(request.form['Text'])
    spotlight_config = parse_configuration(run_id)
        
    body_str = long_output(target_db, text_id, text, spotlight_config)
    
    app.logger.warning("\t".join((text_id, repr(text[:500]), run_id)))
    with open("logs/long/{0}.txt".format(text_id), 'w') as f:
        try:
            f.write(text)
        except UnicodeEncodeError:
            f.write(text.encode('utf8'))
    with open("logs/long/{0}.tsv".format(run_id), 'a') as f:
        try:
            f.write(body_str)
        except UnicodeEncodeError:
            f.write(body_str.encode('utf8'))     
        
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    
    return (body_str, 200, headers)


##
# Helper functions
##
def rotate_on_final_query(text_id):
    """Rotate the query log file on the final query
    """
    if text_id in {"do_task_1-100.tsv-99",
                   "TREC-91",
                   "msn-2014-03-28-01515"}:
        handler.doRollover()
        
def redecode_utf8(unicode_s):
    try:
        return unicode_s.encode('latin1').decode('utf8')
    except UnicodeError:
        return unicode_s
        
def parse_config_str(config_str):
    spotlight_url = "http://spotlight.sztaki.hu:2222/rest/"
    conf = 0.3
    supp = 0
    posr = 0.0
    cand_param = "single"
    strf = None    
    
    for p_str in config_str.split('_'):
        print p_str
        if p_str == "single" or p_str == "multi":
            cand_param = p_str
        elif p_str == "capwords":
            strf = string.capwords
        elif p_str == "sz":
            spotlight_url = "http://spotlight.sztaki.hu:2222/rest/"
        elif p_str == "cl":
            spotlight_url = "http://e.hum.uva.nl:8082/rest/"
        elif p_str.startswith('c'):
            conf = float(p_str[1:])
        elif p_str.startswith('s'):
            supp = int(p_str[1:])
        elif p_str.startswith('posr'):
            posr = float(p_str[4:])
    
    return SpotlightCallConfiguration(
        spotlight_url, cand_param, conf, supp, posr, strf
    )
        
def parse_configuration(run_id):
    if run_id.startswith('m_'):
        config_strs = run_id[2:].split('__')
        primary_config = parse_config_str(config_strs[0])
        additional_config = parse_config_str(config_strs[1])
        for config in (primary_config, additional_config):
            config.cand_param = "multi"
        return (primary_config, additional_config)
        
    if run_id.startswith('dbp_'):
        return parse_config_str(run_id[4:])
    else:
        return SpotlightCallConfiguration(spotlight_url, cand_param, conf)


if __name__ == '__main__':    
    
    ## Local use only
    # app.run(debug=True)
    ## Public (any originating IP allowed)
    app.run(host='0.0.0.0', port=8080)
    pass