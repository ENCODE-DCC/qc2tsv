#!/usr/bin/env python3
"""qc2tsv converts multiple JSON objects into a single spreadsheet

Author:
    Jin Lee (leepc12@gmail.com) at ENCODE-DCC
"""

import json
import pandas
import argparse
import caper
from copy import deepcopy
from caper.caper_uri import init_caper_uri, CaperURI
from caper.dict_tool import split_dict, merge_dict


__version__ = '0.1.1'


class Qc2Tsv(object):
    """Qc2Tsv converts multiple JSON objects into a single spreadsheet
    Its header will have multiple rows according to the hierachy of JSON objects.
    """
    SEP = '*_:_*'
    SEP_COLLAPSED_HEADER = '.'

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


    def flatten_to_tsv(self, row_split_rules=None,
                       merge_split_rows=None,
                       collapse_header=False, transpose=False):
        """Flatten JSON objects by using pandas.io.json.json_normalize
        Header will be multi-line according to the hierachy of JSON objects
        The last entry of each column will be aligned to bottom
        all the others will be aligned to top
        """
        jsons = []

        for j in self._jsons:
            # split JSONs first according to split rules
            splitted_jsons = split_dict(j, rules=row_split_rules)

            if merge_split_rows is not None:
                merged_jsons = []
                rule_name, first_key = merge_split_rows.split(':', 1)
                j_not_caught = None
                j_with_first_key = None
                for j_ in splitted_jsons:
                    if rule_name not in j_:
                        j_not_caught = j_
                    elif rule_name in j_ and j_[rule_name] == first_key:
                        j_with_first_key = j_
                    else:
                        merged_jsons.append(j_)
                if j_not_caught is not None and j_with_first_key is not None:
                    j_merge = deepcopy(j_not_caught)
                    merge_dict(j_not_caught, j_with_first_key)
                    merged_jsons = [j_not_caught] + merged_jsons
                elif j_not_caught is not None:
                    merged_jsons = [j_not_caught] + merged_jsons
                elif j_with_first_key is not None:
                    merged_jsons = [j_with_first_key] + merged_jsons
            else:
                merged_jsons = splitted_jsons
            jsons.extend(merged_jsons)

        if collapse_header:
            sep = Qc2Tsv.SEP_COLLAPSED_HEADER
        else:
            sep = Qc2Tsv.SEP
        df = pandas.io.json.json_normalize(jsons, sep=sep)
        tsv = df.to_csv(sep=self._delim, index=False).strip('\n')
        (header, contents) = tsv.split('\n', 1)

        if collapse_header:
            # single-row header
            header_matrix_t = [[col for col in header.split(self._delim)]]
        else:
            # multi-row header
            # find number of lines of header (maximum nesting level in JSON)
            header_sparse_matrix = [col.split(sep) for col in header.split(self._delim)]
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
            # transpose temp matrix
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
        contents_matrix = [row.split(self._delim) for row in contents.split('\n')]
        final_matrix = header_matrix_t + contents_matrix
        # transpose the final matrix if required
        if transpose:
            final_matrix = [[final_matrix[j][i] for j in range(len(final_matrix))] \
                    for i in range(len(final_matrix[0]))]
        return '\n'.join([self._delim.join(row) for row in final_matrix])


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
             'Format: "RULE_NAME:REGEX". '
             'IMPORTANT: Escape slashes (\\) in REGEX. '
             'Example: "replicate:rep1:^(rep|ctl)\\d+$". '
             'This example will find key names for biological replicates '
             'like "rep1" and "rep2" and split each row into multiple rows '
             'for each replicate.')
    p.add_argument(
        '--merge-split-rows', default='replicate:rep1',
        help='Merge rows splitted by rules defined with --regex-split-rule. '
             'Two rows will be merged. '
             '1) A row that is not caught by REGEX. '
             '(e.g. quality metrics of the whole experiment) '
             '2) A row splitted with an entry "RULE_NAME:FIRST_KEY". '
             '(e.g. quality metrics for rep1)'
             'Format: "RULE_NAME:FIRST_KEY". '
             'This will be helpful to make the spreadsheet non-staggered.')
    p.add_argument(
        '--delim', default='\t',
        help='Delimiter for output TSV.')
    p.add_argument(
        '--tmp-cache-dir', default='~/.qc2tsv/cache',
        help='LOCAL temporary cache directory for remote QC files. '
             'All temporary files for auto-inter-storage transfer will be '
             'stored here.')
    p.add_argument(
        '--transpose', action='store_true',
        help='Transpose rows and columns.')
    p.add_argument(
        '--collapse-header', action='store_true',
        help='Collapse header rows into a single row using DOT (.) notation.')
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

    return qcs, args.delim, args.regex_split_rule, args.merge_split_rows, args.transpose, args.collapse_header


def main():
    # parse arguments. note that args is a dict
    qcs, delim, regex_split_rule, merge_split_rows, transpose, collapse_header = parse_arguments()

    q = Qc2Tsv(
        qcs,
        delim=delim)

    rules = [tuple(i.split(':', 1)) for i in regex_split_rule]
    tsv = q.flatten_to_tsv(
        row_split_rules=rules,
        merge_split_rows=merge_split_rows,
        collapse_header=collapse_header,
        transpose=transpose)

    print(tsv)
    return 0


if __name__ == '__main__':
    main()
