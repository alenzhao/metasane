#!/usr/bin/env python
from __future__ import division

from unittest import TestCase, main
from metasane.core import MetadataTable, VocabularySet

class MetadataTableTests(TestCase):
    def setUp(self):
        """Initialize data used in the tests."""
        self.md_table = MetadataTable(METADATA_1.split('\n'))
        self.vocabs = {
                'vocab_1': VOCAB_1.split('\n'),
                'vocab_2': VOCAB_2.split('\n')
        }

    def test_candidate_controlled_fields(self):
        """Test finding fields that look like they use controlled vocabs."""
        obs = self.md_table.candidate_controlled_fields()
        self.assertEqual(obs, {'Baz': {'vocab_1', 'vocab_3'}})

        obs = self.md_table.candidate_controlled_fields(self.vocabs)
        self.assertEqual(obs, {'Baz': {'vocab_1'}})

    def test_field_values(self):
        """Test collecting all values in each field."""
        exp = {
                '#ID': {'A', 'B', 'C', 'D', 'E'},
                'Foo': {'Yes', 'yes', 'nO ', ' NO'},
                'Bar': {'foobar', 'foo bar', 'baz', ' foo  bar '},
                'Baz': {'vocab_1:foo', 'vocab_1:bar', 'vocab_3:baz', 'na'}
        }
        obs = self.md_table.field_values()
        self.assertEqual(obs, exp)

    def test_extract_vocab_id(self):
        """Test extracting vocabulary ID from a cell value."""
        obs = self.md_table._extract_vocab_id('ENVO:foo')
        self.assertEqual(obs, ('ENVO', 'foo'))

        obs = self.md_table._extract_vocab_id('foo')
        self.assertEqual(obs, (None, 'foo'))

class VocabularySetTests(TestCase):
    def setUp(self):
        """Initialize data used in the tests."""
        self.single_vocab = {'vocab_1': VOCAB_1.split('\n')}
        self.multi_vocab = {
                'vocab_1': VOCAB_1.split('\n'),
                'vocab_2': VOCAB_2.split('\n')
        }
        self.multi_vocab_inst = VocabularySet(self.multi_vocab)

    def test_init_empty(self):
        """Test constructing an instance with no vocabs."""
        obs = VocabularySet({})
        self.assertEqual(len(obs), 0)

    def test_init_single(self):
        """Test constructing an instance with a single vocab."""
        obs = VocabularySet(self.single_vocab)
        self.assertEqual(len(obs), 1)
        self.assertTrue('vocab_1' in obs)

    def test_init_multi(self):
        """Test constructing an instance with multiple vocabs."""
        self.assertEqual(len(self.multi_vocab_inst), 2)
        self.assertTrue('vocab_1' in self.multi_vocab_inst)
        self.assertTrue('vocab_2' in self.multi_vocab_inst)

    def test_contains(self):
        """Test membership based on ID."""
        self.assertTrue('vocab_1' in self.multi_vocab_inst)
        self.assertTrue('vocab_2' in self.multi_vocab_inst)
        self.assertFalse('vocab_3' in self.multi_vocab_inst)

    def test_getitem(self):
        """Test retrieving vocab based on ID."""
        obs = self.multi_vocab_inst['vocab_1']
        self.assertEqual(obs, set(['foo', 'bar', 'baz']))

        obs = self.multi_vocab_inst['vocab_2']
        self.assertEqual(obs, set(['xyz', '123', 'abc']))

    def test_getitem_nonexistent(self):
        """Test retrieving vocab based on nonexistent ID."""
        with self.assertRaises(KeyError):
            _ = self.multi_vocab_inst['vocab_3']

    def test_len(self):
        """Test retrieving the number of vocabs."""
        self.assertEqual(len(self.multi_vocab_inst), 2)

METADATA_1 = """#ID\tFoo\tBar\tBaz
A\tYes\tfoo bar\tna
B\t NO\tfoobar\tvocab_1:bar
C\tyes\tbaz\tvocab_1:foo
D\tnO \t foo  bar \tna
E\tyes\t foo  bar \tvocab_3:baz
"""

VOCAB_1 = """foo
    \t  \t
baR\t\t

\t\tBAZ

"""

VOCAB_2 = """abc
123
xyz"""

if __name__ == '__main__':
    main()
