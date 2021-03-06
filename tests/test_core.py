#!/usr/bin/env python
from __future__ import division

from unittest import TestCase, main
from metasane.core import (MetadataTable, MultipleVocabulariesError,
                           VocabularySet)

class MetadataTableTests(TestCase):
    def setUp(self):
        """Initialize data used in the tests."""
        self.md_table = MetadataTable(METADATA_1.split('\n'))
        self.vocabs_1 = VocabularySet({
                'vocab_1': VOCAB_1.split('\n'),
                'vocab_2': VOCAB_2.split('\n')
        })

        self.vocabs_2 = VocabularySet({
                'vocab_1': VOCAB_1.split('\n'),
                'vocab_3': VOCAB_2.split('\n')
        })

        def fail_all(e):
            raise ValueError
        self.fail_all_fn = fail_all

        def pass_all(e):
            pass
        self.pass_all_fn = pass_all

    def test_shape(self):
        """Test that shape can properly be retrieved."""
        self.assertEqual(self.md_table.shape, (5, 6))

    def test_size(self):
        """Test that number of elements can be retrieved."""
        self.assertEqual(self.md_table.size, 30)

    def test_numeric_fields(self):
        """Test finding fields that are numeric."""
        obs = self.md_table.numeric_fields
        self.assertEqual(obs, {'Num'})

    def test_timestamp_fields(self):
        """Test finding fields that contain timestamps."""
        obs = self.md_table.timestamp_fields
        self.assertEqual(obs, {'Timestamp'})

    def test_categorical_fields(self):
        """Test finding fields that are categorical."""
        obs = self.md_table.categorical_fields
        self.assertEqual(obs, {'Bar', 'Foo', 'Baz', '#ID'})

    def test_candidate_controlled_fields(self):
        """Test finding fields that look like they use controlled vocabs."""
        obs = self.md_table.candidate_controlled_fields()
        self.assertEqual(obs, {'Baz': {'vocab_1', 'vocab_3'}})

        obs = self.md_table.candidate_controlled_fields(self.vocabs_1)
        self.assertEqual(obs, {'Baz': {'vocab_1'}})

    def test_validate_controlled_fields(self):
        """Test validating fields that look like they use controlled vocabs."""
        obs = self.md_table.validate_controlled_fields(self.vocabs_1)
        self.assertEqual(obs,
                         ({'Baz': {'na', 'vocab_3:baz', 'vocab_1:foobar'}}, 4))

        with self.assertRaises(MultipleVocabulariesError):
            _ = self.md_table.validate_controlled_fields(self.vocabs_2)

    def test_find_discrepancies(self):
        """Test finding discrepancies in fields."""
        exp_0 = {
                'hanging whitespace': [1, 2],
                'capitalization': [1, 3],
                'whitespace': [2, 6]
        }

        exp_1 = {
                'Foo': {
                        'hanging whitespace': [['NO ', ' NO']],
                        'capitalization': [['Yes', 'yes']],
                        'whitespace': [['NO ', ' NO']]
                },
                
                'Bar': {
                        'whitespace': [['foo bar', 'foobar', ' foo  bar ']]
                }
        }
        obs = self.md_table.find_discrepancies()
        self.assertEqual(obs[0], exp_0)
        self.assertEqual(obs[1], exp_1)

    def test_categorical_field_values(self):
        """Test collecting all values in each categorical field."""
        exp = {
                '#ID': {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1},
                'Foo': {'Yes': 1, 'yes': 2, 'NO ': 1, ' NO': 1},
                'Bar': {'foobar': 1, 'foo bar': 1, 'na': 1, ' foo  bar ': 2},
                'Baz': {'vocab_1:foobar': 1, 'vocab_1:BAr': 1,
                        'vocab_3:baz': 1, 'na': 2}
        }
        obs = self.md_table.categorical_field_values()
        self.assertEqual(obs, exp)

    def test_is_numeric_true(self):
        """Test checking cell values that are numeric."""
        self.assertTrue(self.md_table._is_numeric('1'))
        self.assertTrue(self.md_table._is_numeric('1.0'))
        self.assertTrue(self.md_table._is_numeric('-1.0'))
        self.assertTrue(self.md_table._is_numeric('-1e-12'))

    def test_is_numeric_false(self):
        """Test checking cell values that are not numeric."""
        self.assertFalse(self.md_table._is_numeric('abc'))
        self.assertFalse(self.md_table._is_numeric('three'))

    def test_is_timestamp_true(self):
        """Test checking cell values that are timestamps."""
        self.assertTrue(self.md_table._is_timestamp('2013-12-30'))
        self.assertTrue(self.md_table._is_timestamp('12/30/2013'))
        self.assertTrue(self.md_table._is_timestamp('08:30 AM'))
        self.assertTrue(self.md_table._is_timestamp('08:30PM'))
        self.assertTrue(self.md_table._is_timestamp('12/30/2013 8:30 AM'))

    def test_is_timestamp_false(self):
        """Test checking cell values that are not timestamps."""
        self.assertFalse(self.md_table._is_timestamp('abc'))
        self.assertFalse(self.md_table._is_timestamp('now'))

    def test_validate_cell_pass(self):
        """Test validating cell values (pass)."""
        self.assertTrue(self.md_table._validate_cell('foo',
                self.pass_all_fn, (ValueError,)))

    def test_validate_cell_fail(self):
        """Test validating cell values (fail)."""
        self.assertFalse(self.md_table._validate_cell('foo',
                self.fail_all_fn, (ValueError,)))

    def test_validate_cell_ignore(self):
        """Test validating cell values that have valid ignore values."""
        for ignore_val in ['', ' ', 'na', 'NA', 'N/A', 'None', '  \tn/a',
                           'nonE']:
            self.assertTrue(self.md_table._validate_cell(ignore_val,
                    self.fail_all_fn, (ValueError,)))

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

METADATA_1 = """#ID\tFoo\tBar\tBaz\tNum\tTimestamp
A\tYes\tfoo bar\tna\t0.001\tNone
B\t NO\tfoobar\tvocab_1:BAr\t NA\t1:55 PM
C\tyes\tna\tvocab_1:foobar\t-1e-2\tna
D\tNO \t foo  bar \tna\t N/A\t2013-12-30
E\tyes\t foo  bar \tvocab_3:baz\t36.446\t1:55PM
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
