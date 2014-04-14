# -*- coding: utf-8 -*-
import logging
from flask import Flask, request
from vocabulary import read_target_db
from compare import short_output

# Read the target db into a dict
target_db = read_target_db(verbosity=1)

# Initialize a Flask instance
app = Flask(__name__)
#app.logger.setLevel(logging.INFO)

# Initialize runtime parameters
conf = 0.03
supp = 0
posr = 0.0

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
        
    app.logger.info("\t".join((text_id, text, run_id)))
    headers = {"Content-Type": "text/plain; charset=utf-8"}
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
    ## Production only
    app.run(host='0.0.0.0', port=5000)
    pass