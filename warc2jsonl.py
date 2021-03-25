#!/usr/bin/env python3

# Run trafilatura to format warc file content as JSONL for Prodigy

import sys
import gzip
import json
import logging
import xml.etree.ElementTree as ET

import trafilatura

from argparse import ArgumentParser

from warcio.archiveiterator import ArchiveIterator


# Mapping from trafilatura XML output tags to HTML tags (and class values).
TRAFILATURA_XML_TO_HTML_TAG_MAP = {
    'head': 'h4',
    'quote': 'blockquote',
    'table': ('table', 'trafilatura'),
    'row': 'tr',
    'cell': 'td',
    'list': ('ul', 'trafilatura'),
    'item': 'li',
    'comments': ('section', 'comments'),
    'main': ('div', 'trafilatura-content'),
}


def argparser():
    ap = ArgumentParser()
    ap.add_argument('warc', nargs='+')
    ap.add_argument('-m', '--min-tokens', default=None, type=int,
                    help='Require given number of tokens to extract document.')
    ap.add_argument('-v', '--verbose', default=False, action='store_true')
    return ap


def get_id(record):
    return record.rec_headers.get_header('WARC-Record-ID')


def get_uri(record):
    return record.rec_headers.get_header('WARC-Target-URI')


def trafilatura_xml_to_html(xml_string):
    root = ET.fromstring(xml_string)
    for from_tag, map_to in TRAFILATURA_XML_TO_HTML_TAG_MAP.items():
        for elem in root.findall(f'.//{from_tag}'):
            if isinstance(map_to, str):
                to_tag = map_to
            else:
                # Assume tag, class tuple
                to_tag, to_class = map_to
                elem.attrib['class'] = to_class
            elem.tag = to_tag
    return ET.tostring(root, encoding='unicode')


def get_trafilatura_xml_doc_attribs(xml_string):
    root = ET.fromstring(xml_string)    # TODO avoid parsing twice
    assert root.tag == 'doc'
    return root.attrib


def token_count(text):
    return len(text.split())    # TODO better definition of token


def process_stream(flo, options):
    responses, total, empties, errors = 0, 0, 0, 0
    for record in ArchiveIterator(flo):
        total += 1
        if record.rec_type != 'response':
            continue
        responses += 1
        id_ = get_id(record)
        uri = get_uri(record)
        content = record.content_stream().read()
        if not content:
            empties += 1
            continue
        try:
            xml_content = trafilatura.extract(
                content,
                output_format='xml'
            )
        except Exception as e:
            logging.error(f'failed extract for {id_}: {e}')
            errors += 1
            continue
        if not xml_content:
            empties += 1
            continue
        if options.min_tokens is not None:
            text_content = trafilatura.extract(content)
            if token_count(text_content) < options.min_tokens:
                continue
        data = {
            'uri': uri,
            'html': trafilatura_xml_to_html(xml_content),
            'meta': { 'source': id_ },
        }
        # add in all attributes of the trafilatura root XML element
        attribs = get_trafilatura_xml_doc_attribs(xml_content)
        for key, value in attribs.items():
            data[f'doc_{key}'] = value
        print(json.dumps(data))
        if total % 1000 == 0:
            logging.info(f'processed {total} records, {responses} responses, '
                         f'{empties} with empty text content, {errors} errors')

    print(f'Done, processed {total} records, {responses} responses, '
          f'{empties} with empty text content, {errors} errors',
          file=sys.stderr)


def main(argv):
    args = argparser().parse_args(argv[1:])

    logging.basicConfig()
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    for fn in args.warc:
        with gzip.open(fn) as f:
            process_stream(f, args)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
