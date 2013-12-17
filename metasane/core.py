#!/usr/bin/env python
from __future__ import division

from csv import DictReader
from collections import defaultdict
from glob import glob
from os.path import basename, join, splitext

class MetadataTable(object):
    VocabDelimiter = ':'

    @classmethod
    def fromFile(cls, fp, delimiter='\t'):
        with open(fp, 'U') as f:
            return cls(f, delimiter=delimiter)

    def __init__(self, metadata_f, delimiter='\t'):
        reader = DictReader(metadata_f, delimiter=delimiter)
        self.FieldNames = reader.fieldnames
        self._table = [row for row in reader]

    def candidateControlledFields(self, known_vocabs=None):
        cols = defaultdict(set)

        for row in self._table:
            for field in row:
                vocab_id, value = self._extract_vocab_id(row[field])

                if vocab_id is not None:
                    if known_vocabs is None or vocab_id in known_vocabs:
                        cols[field].add(vocab_id)

        return cols

    def validateControlledFields(self, known_vocabs):
        cont_fields = self.candidateControlledFields(known_vocabs=known_vocabs)

        field_to_vocab_id = {}
        for field, vocab_ids in cont_fields.iteritems():
            if len(vocab_ids) > 1:
                raise MultipleVocabulariesError("A controlled field should "
                        "only reference a single vocabulary. The field '%s' "
                        "references %d vocabularies." % (field,
                                                         len(vocab_ids)))
            else:
                (vocab_id,) = vocab_ids
                field_to_vocab_id[field] = vocab_id

        # Can remove this second pass though the file, but not important for
        # this first iteration.
        field_results = defaultdict(set)
        for row in self._table:
            for field in field_to_vocab_id:
                cell_value = row[field]
                vocab_id, value = self._extract_vocab_id(cell_value)

                if (vocab_id is None or vocab_id not in known_vocabs or
                    value.lower() not in known_vocabs[vocab_id]):
                    field_results[field].add(cell_value)

        return field_results

    def findCapitalizationDiscrepancies(self):
        """

        Currently checks all fields.
        """
        field_results = {}

        for field, values in self.fieldValues().iteritems():
            equal_values = defaultdict(set)

            for value in values:
                equal_values[value.lower()].add(value)

            discreps = [e for e in equal_values.values() if len(e) > 1]

            if discreps:
                field_results[field] = discreps

        return field_results

    def fieldValues(self):
        field_values = defaultdict(set)

        for row in self._table:
            for field in row:
                field_values[field].add(row[field])

        return field_values

    def _extract_vocab_id(self, cell_value):
        split_val = cell_value.split(self.VocabDelimiter, 1)

        if len(split_val) == 1:
            vocab_id = None
            value = split_val[0]
        else:
            vocab_id, value = split_val

        return vocab_id, value

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
                        vocab.add(line.lower())

            self._vocabs[vocab_id] = vocab

    def __contains__(self, key):
        return key in self._vocabs

    def __getitem__(self, key):
        return self._vocabs[key]

class MultipleVocabulariesError(Exception):
    pass
