# qc2tsv

## Introduction

This tool converts multiple QC JSON objects into a spreadsheet (TSV/CSV), which will be useful to make a QC spread sheet organized for each experiment/replicate.

It flattens each JSON object to make a row in a spreadsheet and then splits each row into multiple rows according to [split rules](#split-rules). This is useful to have a seperate row for a JSON object with a specific key name (e.g. each biological replicate).

This tool can directly read from various types of URIs (`gs://`, `s3://`, `http://`, `https://` and local path). To access private cloud buckets (`gs://` and `s3://`), make sure to authenticate yourself on your shell environment. To access private URLs, use `~/.netrc` file.

## Installation

Make sure that you have `python3`(>= 3.6) installed on your system. Use `pip` to install qc2tsv.
```bash
$ pip install qc2tsv
```

## Example

We will demonstrate how to make a QC spread sheet from two `qc.json` files [QC_SE](https://storage.googleapis.com/encode-pipeline-test-samples/encode-chip-seq-pipeline/ref_output/v1.3.0/ENCSR000DYI_subsampled_chr19_only/qc.json) and [QC_PE](https://storage.googleapis.com/encode-pipeline-test-samples/encode-chip-seq-pipeline/ref_output/v1.3.0/ENCSR936XTK_subsampled_chr19_only/qc.json), which were generated from [ENCODE ChIP-seq pipeline](https://github.com/ENCODE-DCC/chip-seq-pipeline2). You can use any URIs in the command line arguments.

```bash
$ QC_SE=https://storage.googleapis.com/encode-pipeline-test-samples/encode-chip-seq-pipeline/ref_output/v1.3.0/ENCSR000DYI_subsampled_chr19_only/qc.json
$ QC_PE=https://storage.googleapis.com/encode-pipeline-test-samples/encode-chip-seq-pipeline/ref_output/v1.3.0/ENCSR936XTK_subsampled_chr19_only/qc.json
$ qc2tsv $QC_SE $QC_PE
```

See [output](https://docs.google.com/spreadsheets/d/1WQbTWxf_hIIa4n49q-8VVR7D_CRS1C8TKOUwGq1Vc2g/edit?usp=sharing).


## Usage

```bash
$ qc2tsv [JSON_FILE1] [JSON_FILE2] ...
```

Read QC JSON file URIs from a text file `TXT`.
```bash
$ qc2tsv --file [TXT]
```

## Split rules

Define a regular expression (`NAME:REGEX`) to split row into multiple rows. This is useful to have a new row for each biological replicate in genomic pipeline's QC JSON output. Make sure that backslashes in `REGEX` are correctly escaped. You can also define multiple split rules.
```bash
$ qc2tsv ... --regex-split-rule "replicate:^(rep|ctl)\\d+$" --regex-split-rule "[RULE_NAME:REGEX]" ...
```

