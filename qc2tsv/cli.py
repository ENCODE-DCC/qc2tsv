#!/usr/bin/env python3
import argparse
import logging
import os
from autouri import AutoURI
from .qc2tsv import Qc2Tsv
from . import __version__ as version


def get_abspath(path):
    """Get abspath from a string.
    This function is mainly used to make a command line argument an abspath
    since AutoURI module only works with abspath and full URIs
    (e.g. /home/there, gs://here/there).
    For example, "caper run toy.wdl --docker ubuntu:latest".
    AutoURI cannot recognize toy.wdl on CWD as a file path.
    It should be converted to an abspath first.
    To do so, use this function for local file path strings only (e.g. toy.wdl).
    Do not use this function for other non-local-path strings (e.g. --docker).
    """
    if path:
        if not AutoURI(path).is_valid:
            return os.path.abspath(os.path.expanduser(path))
    return path


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
             'for each replicate. '
             'IMPORTANT: MAKE SURE THAT THIS PARAMETER IS CONSITENT WITH '
             '--merge-split-rows.')
    p.add_argument(
        '--merge-split-rows', default='replicate:rep1',
        help='Merge rows splitted by rules defined with --regex-split-rule. '
             'Two rows will be merged. '
             '1) A row that is not caught by REGEX. '
             '(e.g. quality metrics of the whole experiment) '
             '2) A row splitted with an entry "RULE_NAME:FIRST_KEY". '
             '(e.g. quality metrics for rep1)'
             'Format: "RULE_NAME:FIRST_KEY". '
             'This will be helpful to make the spreadsheet non-staggered. '
             'IMPORTANT: MAKE SURE THAT THIS PARAMETER IS CONSITENT WITH '
             '--regex-split-rule.')
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
    p.add_argument('-V', '--verbose', action='store_true',
                   help='Prints all logs >= INFO level')
    p.add_argument('-D', '--debug', action='store_true',
                   help='Prints all logs >= DEBUG level')

    args = p.parse_args()
    if args.version:
        print(version)
        p.exit()

    qcs = []
    for qc in args.qcs:
        qcs.append(qc)
    if args.file:
        qc_files = AutoURI(get_abspath(args.file)).read().strip('\n').split('\n')
        qcs.extend(qc_files)
    if len(qcs) == 0:
        p.print_help()
        p.exit()

    # init logging
    if args.verbose:
        log_level = 'INFO'
    elif args.debug:
        log_level = 'DEBUG'
    else:
        log_level = 'WARNING'
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s|%(name)s|%(levelname)s| %(message)s')
    # suppress filelock logging
    logging.getLogger('filelock').setLevel('CRITICAL')

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
