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
