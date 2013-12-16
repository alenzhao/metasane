#!/usr/bin/env python
from __future__ import division

from csv import DictReader
from collections import defaultdict

class MetadataTable(object):
    OntologyDelimiter = ':'

    def __init__(self, metadata_f, delimiter='\t'):
        reader = DictReader(metadata_f, delimiter=delimiter)
        self.FieldNames = reader.fieldnames
        self._table = [row for row in reader]

    def candidateOntologyColumns(self):
        ont_cols = defaultdict(set)

        for row in self._table:
            for field, value in row.items():
                split_val = value.split(self.OntologyDelimiter, 1)

                if len(split_val) > 1:
                    ont_cols[field].add(split_val[0])

        return ont_cols
