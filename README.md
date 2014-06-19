sigir-erd-14-server
===================

This is the outer server layer that controls I/O for the ERD workshop challenge. The actual work (i.e. ERD) is done by underlying modules.

## Installation
```bash
git clone https://github.com/aolieman/sigir-erd-14-server.git
wget http://web-ngram.research.microsoft.com/erd2014/Docs/entity.tsv
cd sigir-erd-14-server
pip install -r requirements.txt
```

## Run Server
```
python run_server.py
```

## Error Analysis
### Long track
```python
cd sigir-erd-14-server
python
>>> from offline_evaluation import *
>>> runs = ["dbp_sz_c0.3_s0_single", "dbp_sz_c0.4_s0_single", "dbp_sz_c0.3_s0_multi"]
>>> server_url = "http://e.hum.uva.nl:8080/long"
>>> multiple_runs_long(runs, server_url)
dbp_sz_c0.3_s0_single overview {'average_F1': 0.71498559488389513, 'overall_recall': 0.6757912745936698, 'FP_wrong_disambiguation': 0.2331288343558282, 'average_recall': 0.73262404987843055, 'overall_precision': 0.7078853046594982, 'FP_should_be_NIL': 0.7668711656441718, 'average_precision': 0.74251112150648169, 'overall_F1': 0.6914660831509847}
dbp_sz_c0.4_s0_single overview {'average_F1': 0.70702201335018788, 'overall_recall': 0.6330196749358425, 'FP_wrong_disambiguation': 0.23829787234042554, 'average_recall': 0.67366065384417384, 'overall_precision': 0.7589743589743589, 'FP_should_be_NIL': 0.7617021276595745, 'average_precision': 0.79503059635958195, 'overall_F1': 0.6902985074626865}
dbp_sz_c0.3_s0_multi overview {'average_F1': 0.71409983517460596, 'overall_recall': 0.6757912745936698, 'FP_wrong_disambiguation': 0.23404255319148937, 'average_recall': 0.73654561850588152, 'overall_precision': 0.7059874888293118, 'FP_should_be_NIL': 0.7659574468085106, 'average_precision': 0.74061360684537103, 'overall_F1': 0.6905594405594405}
>>> 
```
