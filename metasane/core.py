#!/usr/bin/env python
from __future__ import division

from csv import DictReader
from collections import defaultdict
from glob import glob
from os.path import basename, join, splitext

class MetadataTable(object):
    OntologyDelimiter = ':'

    def __init__(self, metadata_f, delimiter='\t'):
        reader = DictReader(metadata_f, delimiter=delimiter)
        self.FieldNames = reader.fieldnames
        self._table = [row for row in reader]

    def candidateOntologyColumns(self, vocab=None):
        ont_cols = defaultdict(set)

        for row in self._table:
            for field, value in row.items():
                split_val = value.split(self.OntologyDelimiter, 1)

                if len(split_val) > 1:
                    ont_id = split_val[0]

                    if vocab is None or ont_id in vocab:
                        ont_cols[field].add(ont_id)

        return ont_cols

class VocabularySet(object):
    Wildcard = '*.txt'

    def __init__(self, vocab_dir):
        self._vocabs = {}

        for fp in glob(join(vocab_dir, self.Wildcard)):
            vocab_id = splitext(basename(fp))[0]
            vocab = set()

            with open(fp, 'U') as f:
                for line in f:
                    line = line.strip()

                    if line:
                        vocab.add(line)

            self._vocabs[vocab_id] = vocab

    def __contains__(self, key):
        return key in self._vocabs

    def __getitem__(self, key):
        return self._vocabs[key]
