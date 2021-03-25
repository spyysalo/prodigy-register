# prodigy-register

Tools for register (genre) annotation with Prodigy

## Quickstart

Set up virtual environment

```
python3 -m venv venv
source venv/bin/activate
python -m pip install trafilatura warcio
```

Grab data

```
wget https://a3s.fi/commoncrawl-samples/CC-MAIN-2021-04-es-tiny-v1.warc.gz
```

Extract content in Prodigy JSONL format

```
python3 warc2jsonl.py --min-tokens 75 CC-MAIN-2021-04-es-tiny-v1.warc.gz > \
    CC-MAIN-2021-04-es-tiny-v1.jsonl
```

Start Prodigy

```
python -m prodigy registers [DATA-NAME] CC-MAIN-2021-04-es-tiny-v1.jsonl \
    [USER-NAME] -F registers.py 
```

Where `[DATA-NAME]` and `[USER-NAME]` should be replaced with
values suiting your environment.
