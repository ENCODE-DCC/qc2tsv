#!/usr/bin/env python3
"""qc2tsv converts multiple JSON objects into a single spreadsheet

Author:
    Jin Lee (leepc12@gmail.com) at ENCODE-DCC
"""

import json
import pandas
import argparse
import caper
from caper.caper_uri import init_caper_uri, CaperURI
from caper.dict_tool import split_dict


__version__ = '0.1.0'


class Qc2Tsv(object):
    """Qc2Tsv converts multiple JSON objects into a single spreadsheet
    Its header will have multiple rows according to the hierachy of JSON objects.
    """
    SEP = '*-_:_-*'

    def __init__(self, qcs, delim='\t'):        
        """
        Args:
            qcs:
                list of QC file URIs (path/URL/S3/GCS)
            delim:
                delimiter for output ([TAB] by default)
        """
        self._delim = delim
        self._jsons = []
        for qc in qcs:
            f = CaperURI(qc).get_local_file()
            with open(f) as fp:
                j = json.loads(fp.read())
            self._jsons.append(j)


    def flatten_to_tsv(self, row_split_rules=None):
        """Flatten JSON objects by using pandas.io.json.json_normalize
        Header will be multi-line according to the hierachy of JSON objects
        The last entry of each column will be aligned to bottom
        all the others will be aligned to top
        """
        jsons = []

        # split JSONs first according to split rules
        for j in self._jsons:
            jsons.extend(split_dict(j, rules=row_split_rules))
        df = pandas.io.json.json_normalize(jsons, sep=Qc2Tsv.SEP)
        tsv = df.to_csv(sep=self._delim, index=False).strip('\n')
        (header, contents) = tsv.split('\n', 1)

        # find number of lines of header (maximum nesting level in JSON)
        header_sparse_matrix = [col.split(Qc2Tsv.SEP) for col in header.split(self._delim)]
        num_header_lines = max([len(c) for c in header_sparse_matrix])

        # align sparse matrix to top (fill zeros for empty entries)
        # except for the lowest level. align lowest level to bottom
        header_matrix = []
        for cols in header_sparse_matrix:
            m = num_header_lines*['']
            # align all but lowest to top
            m[:len(cols)-1] = cols[:-1]
            # align lowest level to bottom
            m[-1] = cols[-1]
            header_matrix.append(m)
        # transpose
        header_matrix_t = [[header_matrix[j][i] for j in range(len(header_matrix))] \
                for i in range(len(header_matrix[0]))]

        # remove repeating entries except for the last row
        for row in header_matrix_t[:-1]:
            for i, col in enumerate(row):
                if not col:
                    continue
                for j in range(i + 1, len(row)):                    
                    if col == row[j]:
                        row[j] = ''
                    else:
                        break
        new_header = '\n'.join([self._delim.join(row) for row in header_matrix_t])
        return '\n'.join([new_header, contents])


def parse_arguments():
    """Argument parser for qc2tsv
    """
    p = argparse.ArgumentParser()
    p.add_argument(
        'qcs', nargs='*',
        help='URIs for QC JSON files. '
             'Example: /scratch/sample1/qc.json, s3://here/qc.json, '
             'gs://some/where/qc.json, http://hello.com/world/qc.json')
    p.add_argument(
        '--file',
        help='URI for a text file with all QC JSON files. '
             'One QC JSON file for each line.')
    p.add_argument(
        '--regex-split-rule', nargs='*', default=['replicate:^(rep|ctl)\d+$'],
        help='Python regular expression to split a single row into '
             'multiple rows. You can define this rule multiple times. '
             'Format: "SPLIT_RULE_NAME:REGEX". '
             'IMPORTANT: Escape slashes (\\) in REGEX. '
             'Example: "replicate:^(rep|ctl)\\d+$". '
             'This example will find key names for biological replicates '
             'like "rep1" and "rep2" and split each row into multiple rows '
             'for each replicate.')
    p.add_argument(
        '--delim', default='\t',
        help='Delimiter for output TSV.')
    p.add_argument(
        '--tmp-cache-dir', default='~/.qc2tsv/cache',
        help='LOCAL temporary cache directory for remote QC files. '
             'All temporary files for auto-inter-storage transfer will be '
             'stored here.')
    p.add_argument('-v', '--version', action='store_true',
                   help='Show version')

    args = p.parse_args()
    if args.version:
        print(__version__)
        p.exit()

    init_caper_uri(tmp_dir=args.tmp_cache_dir)

    qcs = []
    for qc in args.qcs:
        qcs.append(qc)
    if args.file is not None:
        with open(CaperURI(args.file).get_local_file()) as fp:
            qcs.extend(fp.read().strip('\n').split('\n'))
    if len(qcs) == 0:
        p.print_help()
        p.exit()

    return qcs, args.delim, args.regex_split_rule


def main():
    # parse arguments. note that args is a dict
    qcs, delim, regex_split_rule= parse_arguments()

    q = Qc2Tsv(qcs, delim=delim)
    rules = [tuple(i.split(':', 1)) for i in regex_split_rule]
    tsv = q.flatten_to_tsv(row_split_rules=rules)
    print(tsv)
    return 0


if __name__ == '__main__':
    main()
