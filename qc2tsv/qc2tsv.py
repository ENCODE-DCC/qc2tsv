import json
import logging
import pandas
from copy import deepcopy
from autouri import AutoURI, AbsPath
from caper.dict_tool import split_dict, merge_dict


logger = logging.getLogger(__name__)


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
            qc = AbsPath.get_abspath_if_exists(qc)
            if not AutoURI(qc).exists:
                logger.error('File does not exists. Skipping... {uri}'.format(uri=qc))
                continue
            s = AutoURI(qc).read()
            j = json.loads(s)
            self._jsons.append(j)


    def flatten_to_tsv(self, row_split_rules=None,
                       merge_split_rows=None,
                       collapse_header=False, transpose=False):
        """Flatten JSON objects by using pandas.json_normalize
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
        df = pandas.json_normalize(jsons, sep=sep)
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
