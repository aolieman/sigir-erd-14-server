# -*- coding: utf-8 -*-
import logging, json
from logging import handlers
from flask import Flask, request
from vocabulary import read_target_db
from compare import short_output

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
conf = 0.03
supp = 0
posr = 0.0

##
# Flask views
##
@app.route('/parameters', methods=['GET'])
def set_parameters():
    global conf, supp, posr
    conf = float(request.args.get('conf', conf))
    supp = int(request.args.get('supp', supp))
    posr = float(request.args.get('posr', posr))
    msg = "Parameters set to confidence={0:.2f}, "\
          "support={1:d}, PoSR={2:.2f}".format(conf, supp, posr)
    app.logger.warning(msg)
    return msg

@app.route('/short', methods=['POST'])
def short_track(target_db=target_db):
    # Get request parameter values
    run_id = request.form['runID']
    text_id = request.form['TextID']
    text = request.form['Text']
    
    body_str = short_output(
        target_db, text_id, text, conf, supp, posr
    )
        
    app.logger.warning("\t".join((text_id, text, run_id)))
    with open("logs/{0}.tsv".format(run_id), 'a') as f:
        f.write(body_str)
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    
    # Rotate the query log file on the final query
    if text_id in {"do_task_1-100.tsv-99",
                   "TREC-91"}:
        handler.doRollover()
    
    return (body_str, 200, headers)

@app.route('/long', methods=['POST'])
def long_track():
    # Get request parameter values
    run_id = request.form['runID']
    text_id = request.form['TextID']
    text = request.form['Text']
    return 'Hello World!'

if __name__ == '__main__':    
    
    ## Local use only
    # app.run(debug=True)
    ## Public (any originating IP allowed)
    app.run(host='0.0.0.0', port=8080)
    pass