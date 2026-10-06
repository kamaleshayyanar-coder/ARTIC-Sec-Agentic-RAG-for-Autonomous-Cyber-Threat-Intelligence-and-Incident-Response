# CIC-IDS2017

Place University of New Brunswick CIC-IDS2017 CSVs here (not committed).

Recommended first file: `Friday-WorkingHours.csv`

```
huggingface-cli download c01dsnap/CIC-IDS2017 --local-dir ./data/cic-ids2017
```

Then:

```
python pipelines/ingest_cic.py --csv data/cic-ids2017/Friday-WorkingHours.csv
```

Dataset license is controlled by UNB: https://www.unb.ca/cic/datasets/ids-2017.html
