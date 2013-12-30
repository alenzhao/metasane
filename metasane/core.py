#!/usr/bin/env python
from __future__ import division

import re
from csv import DictReader
from collections import Counter, defaultdict
from glob import glob
from os.path import basename, join, splitext

import dateutil.parser

class MetadataTable(object):
    _vocab_delimiter = ':'
    _discrepancy_removers = {
            'capitalization': lambda e: e.lower(),
            'hanging whitespace': lambda e: e.strip(),
            'whitespace': lambda e: ''.join(e.split()),
            # Not exactly thrilled about this... can define a helper function
            # to generate these lambdas, but not worth the effort right now.
            'pipe': lambda e: e.replace('|', ''),
            'underscore': lambda e: e.replace('_', ''),
            'hyphen': lambda e: e.replace('-', ''),
            'forward slash': lambda e: e.replace('/', ''),
            'backslash': lambda e: e.replace('\\', ''),
            'period': lambda e: e.replace('.', ''),
            'single quote': lambda e: e.replace('\'', ''),
            'double quote': lambda e: e.replace('"', ''),
            'ampersand': lambda e: e.replace('&', ''),
            'comma': lambda e: e.replace(',', ''),
            'brackets': lambda e: re.sub('[(){}<>\[\]]', '', e)
    }
    _ignore_list = ['', 'na', 'n/a', 'none']

    @classmethod
    def from_file(cls, metadata_fp, delimiter='\t'):
        with open(metadata_fp, 'U') as metadata_f:
            return cls(metadata_f, delimiter=delimiter)

    def __init__(self, metadata_f, delimiter='\t'):
        reader = DictReader(metadata_f, delimiter=delimiter)
        self._table = [row for row in reader]
        self.field_names = reader.fieldnames
        self.shape = len(self._table), len(self.field_names)

    @property
    def size(self):
        return self.shape[0] * self.shape[1]

    @property
    def numeric_fields(self):
        """Order is *not* guaranteed!"""
        if not hasattr(self, '_numeric_fields'):
            self._numeric_fields = self._validate_fields(self.field_names,
                                                         self._is_numeric)
        return self._numeric_fields

    @property
    def timestamp_fields(self):
        """Order is *not* guaranteed!"""
        if not hasattr(self, '_timestamp_fields'):
            nonnumeric_fields = set(self.field_names) - self.numeric_fields
            self._timestamp_fields = self._validate_fields(nonnumeric_fields,
                                                           self._is_timestamp)
        return self._timestamp_fields

    @property
    def categorical_fields(self):
        """Order is *not* guaranteed!"""
        if not hasattr(self, '_categorical_fields'):
            self._categorical_fields = ((set(self.field_names) - self.numeric_fields) - self.timestamp_fields)

        return self._categorical_fields

    def candidate_controlled_fields(self, known_vocabs=None):
        """Ignores numeric fields."""
        cols = defaultdict(set)
        cat_fields = self.categorical_fields

        for row in self._table:
            for field in cat_fields:
                vocab_id, _ = self._extract_vocab_id(row[field])

                if vocab_id is not None:
                    if known_vocabs is None or vocab_id in known_vocabs:
                        cols[field].add(vocab_id)

        return cols

    def validate_controlled_fields(self, known_vocabs):
        cont_fields = self.candidate_controlled_fields(known_vocabs)

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
        invalid_count = 0
        for row in self._table:
            for field in field_to_vocab_id:
                cell_value = row[field]
                vocab_id, value = self._extract_vocab_id(cell_value)

                if (vocab_id is None or vocab_id not in known_vocabs or
                    value.lower() not in known_vocabs[vocab_id]):
                    field_results[field].add(cell_value)
                    invalid_count += 1

        return field_results, invalid_count

    def find_discrepancies(self):
        """

        Ignores numeric fields. Checks all remaining fields, including those
        with controlled vocabularies.
        """
        # These native python data structures are getting a little complicated
        # for my tastes. Will refactor into proper classes later on.

        # discrep name -> [unique discrep count, total discrep cell count]
        discrep_counts = defaultdict(lambda: [0, 0])

        # field name -> discrep name -> [['foo', 'FOO'], ['bar', 'bAr']]
        field_results = defaultdict(lambda: defaultdict(list))

        for field, values in self.categorical_field_values().iteritems():
            for discrep_name, discrep_remover in \
                    self._discrepancy_removers.iteritems():
                equal_values = defaultdict(Counter)

                for value, value_count in values.iteritems():
                    equal_values[discrep_remover(value)][value] += value_count

                discreps = [e for e in equal_values.values() if len(e) > 1]

                if discreps:
                    discrep_counts[discrep_name][0] += len(discreps)

                    for discrep in discreps:
                        discrep_counts[discrep_name][1] += \
                                sum(discrep.values())
                        field_results[field][discrep_name].append(
                                discrep.keys())

        return discrep_counts, field_results

    def categorical_field_values(self):
        field_vals = defaultdict(Counter)
        cat_fields = self.categorical_fields

        for row in self._table:
            for field in cat_fields:
                field_vals[field][row[field]] += 1

        return field_vals

    def _validate_fields(self, fields, validator):
        results = defaultdict(list)

        for row in self._table:
            for field in fields:
                results[field].append(validator(row[field]))

        return set([field for field in results if all(results[field])])

    def _is_numeric(self, cell_value):
        return self._validate_cell(cell_value, float, (ValueError,))

    def _is_timestamp(self, cell_value):
        # OverflowError occurs with stuff like 1843:2915940910 (example taken
        # from American Gut metadata).
        return self._validate_cell(cell_value, dateutil.parser.parse,
                                   (OverflowError, TypeError, ValueError))

    def _validate_cell(self, cell_value, validator, error_types):
        is_valid = False

        try:
            _ = validator(cell_value)
        except error_types:
            if cell_value.strip().lower() in self._ignore_list:
                is_valid = True
        else:
            is_valid = True

        return is_valid

    def _extract_vocab_id(self, cell_value):
        split_val = cell_value.split(self._vocab_delimiter, 1)

        if len(split_val) == 1:
            vocab_id = None
            value = split_val[0]
        else:
            vocab_id, value = split_val

        return vocab_id, value

class VocabularySet(object):
    @classmethod
    def from_dir(cls, vocab_dir, wildcard='*.txt'):
        vocab_files = {}
        files_to_close = []

        for vocab_fp in glob(join(vocab_dir, wildcard)):
            vocab_id = splitext(basename(vocab_fp))[0]
            vocab_f = open(vocab_fp, 'U')
            vocab_files[vocab_id] = vocab_f
            files_to_close.append(vocab_f)

        vocab_set = cls(vocab_files)

        for file_handle in files_to_close:
            file_handle.close()

        return vocab_set

    def __init__(self, vocab_files):
        self._vocabs = {}

        for vocab_id, vocab_f in vocab_files.iteritems():
            vocab = set()

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
