# -*- coding: utf-8 -*-
"""
Run a Flask server that responds to requests in the ERD14 format.
"""

import logging
from logging import handlers
from flask import Flask, request
from vocabulary import read_target_db
from spotlight_client import short_output, long_output

# Read the target db into a dict
target_db = read_target_db(verbosity=1)

# Initialize a Flask instance
app = Flask(__name__)

# Set up logging
handler = handlers.RotatingFileHandler(
    'logs/short_queries.tsv', maxBytes=10000, backupCount=1
)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# Initialize runtime parameters
spotlight_url = "http://spotlight.sztaki.hu:2222/rest/"
conf = 0.03
supp = 0
posr = 0.0

##
# Flask views
##
@app.route('/parameters', methods=['GET'])
def set_parameters():
    global spotlight_url, conf, supp, posr
    spotlight_url = str(request.args.get('url', spotlight_url))
    conf = float(request.args.get('conf', conf))
    supp = int(request.args.get('supp', supp))
    posr = float(request.args.get('posr', posr))
    msg = "Parameters set to url={0}, confidence={1:.2f},"\
          "support={2:d}, PoSR={3:.2f}".format(spotlight_url, conf, supp, posr)
    app.logger.warning(msg)
    return msg

@app.route('/short', methods=['POST'])
def short_track(target_db=target_db):
    # Get request parameter values
    run_id = request.form['runID']
    text_id = request.form['TextID']
    text = request.form['Text']
    
    body_str = short_output(
        target_db, text_id, spotlight_url,
        text, conf, supp, posr
    )
        
    app.logger.warning("\t".join((text_id, text, run_id)))
    with open("logs/{0}.tsv".format(run_id), 'a') as f:
        f.write(body_str)
    rotate_on_final_query(text_id)        
        
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    
    return (body_str, 200, headers)

@app.route('/long', methods=['POST'])
def long_track():
    # Get request parameter values
    run_id = request.form['runID']
    text_id = request.form['TextID']
    text = request.form['Text']
    
    body_str = long_output(
        target_db, text_id, spotlight_url, text, conf, supp
    )
    
    app.logger.warning("\t".join((text_id, repr(text[:500]), run_id)))
    with open("logs/long/{0}.txt".format(text_id), 'w') as f:
        f.write(text)
    with open("logs/long/{0}.tsv".format(run_id), 'a') as f:
        f.write(body_str)
    rotate_on_final_query(text_id)        
        
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
                   "mainbody-00045"}:
        handler.doRollover()

if __name__ == '__main__':    
    
    ## Local use only
    # app.run(debug=True)
    ## Public (any originating IP allowed)
    app.run(host='0.0.0.0', port=5000)
    pass