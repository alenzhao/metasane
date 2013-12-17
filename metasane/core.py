#!/usr/bin/env python
from __future__ import division

from csv import DictReader
from collections import defaultdict
from glob import glob
from os.path import basename, join, splitext

class MetadataTable(object):
    vocab_delimiter = ':'
    discrepancy_removers = {
            'capitalization': lambda e: e.lower(),
            'hanging whitespace': lambda e: e.strip(),
            'whitespace': lambda e: ''.join(e.split())
    }

    @classmethod
    def from_file(cls, metadata_fp, delimiter='\t'):
        with open(metadata_fp, 'U') as metadata_f:
            return cls(metadata_f, delimiter=delimiter)

    def __init__(self, metadata_f, delimiter='\t'):
        reader = DictReader(metadata_f, delimiter=delimiter)
        self._table = [row for row in reader]

    def candidate_controlled_fields(self, known_vocabs=None):
        cols = defaultdict(set)

        for row in self._table:
            for field in row:
                vocab_id, _ = self._extract_vocab_id(row[field])

                if vocab_id is not None:
                    if known_vocabs is None or vocab_id in known_vocabs:
                        cols[field].add(vocab_id)

        return cols

    def validate_controlled_fields(self, known_vocabs):
        cont_fields = self.candidate_controlled_fields(
                known_vocabs=known_vocabs)

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

    def find_discrepancies(self):
        """Currently checks all fields."""
        field_results = defaultdict(dict)

        for field, values in self.field_values().iteritems():
            for discrep_name, discrep_remover in \
                    self.discrepancy_removers.iteritems():
                equal_values = defaultdict(set)

                for value in values:
                    equal_values[discrep_remover(value)].add(value)

                discreps = [e for e in equal_values.values() if len(e) > 1]

                if discreps:
                    field_results[field][discrep_name] = discreps

        return field_results

    def field_values(self):
        field_vals = defaultdict(set)

        for row in self._table:
            for field in row:
                field_vals[field].add(row[field])

        return field_vals

    def _extract_vocab_id(self, cell_value):
        split_val = cell_value.split(self.vocab_delimiter, 1)

        if len(split_val) == 1:
            vocab_id = None
            value = split_val[0]
        else:
            vocab_id, value = split_val

        return vocab_id, value

class VocabularySet(object):
    wildcard = '*.txt'

    #@classmethod
    #def from_dir(cls, vocab_dir):

    def __init__(self, vocab_dir):
        self._vocabs = {}

        for vocab_fp in glob(join(vocab_dir, self.wildcard)):
            vocab_id = splitext(basename(vocab_fp))[0]
            vocab = set()

            with open(vocab_fp, 'U') as vocab_f:
                for line in vocab_f:
                    line = line.strip()

                    if line:
                        vocab.add(line.lower())

            self._vocabs[vocab_id] = vocab

    def __contains__(self, key):
        return key in self._vocabs

    def __getitem__(self, key):
        return self._vocabs[key]

    def __len__(self):
        return len(self._vocabs)

class MultipleVocabulariesError(Exception):
    pass
