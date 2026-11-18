"""Check the repair-round examples against the rebuilt extraction."""
from collections import Counter, defaultdict
import csv
import json
import unittest

from audit import repair_samples
from extract import ROOT, trim_full_stop


CLARK = 'ferg1922:p468:b6:r5'
BOIS = 'ferg1922:p470:b2:r3'
DUNLOP = 'ferg1922:p481:b2:r2'
EASTERN = 'ferg1922:p481:b2:r5'
POPOFF = 'ferg1922:p497:b2:r1'
WEBSTER = 'ferg1922:p499:b2:r2'

# Spacing and case variants are retained in the data.
REVIEWED_HONORIFICS = {
    'A. C. A.', 'A. S. A. A.', 'A.C.A.', 'A.I.M.M.', 'A.M. I.C.E.', 'A.M.I.E.S.', 'AMIEE',
    'B.A.', 'c. c. s.', 'C.A.', 'c.a.', 'Col', 'Dr', 'Dr.', 'Effendi', 'ESQ.', 'Esq.',
    'F.C.A.', 'G.B.V.C.', 'Gate Muhandiram', 'Hon.', 'J. P.', 'J.P.', 'J.P.M.M.C.',
    'M.A.', 'M.P.S.', 'Madame', 'Miss', 'Mlle.', 'Mr.', 'Mrs', 'Mrs.', 'Sir',
    'The Hon.', 'the Hon.', 'U.P.M.',
}


def read_jsonl(stem):
    with (ROOT / f'{stem}.jsonl').open(encoding='utf-8') as src:
        return [json.loads(line) for line in src]


class RepairExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.listings = {row['listing_id']: row for row in read_jsonl('listings')}
        cls.roles = defaultdict(list)
        cls.connections = defaultdict(list)
        for stem, index in (('roles', cls.roles), ('connections', cls.connections)):
            for row in read_jsonl(stem):
                index[row['listing_id']].append(row)
        cls.validation = json.loads((ROOT / 'validation.json').read_text(encoding='utf-8'))

    def test_names_and_honorifics(self):
        for listing, initials, surname in (
            (DUNLOP, 'E. R.', 'Park'),
            (EASTERN, 'R. C.', 'Short'),
            (EASTERN, 'J. M.', 'Menzies'),
            (WEBSTER, 'W. H.', 'Atkinson'),
            (WEBSTER, 'L. H.', 'Watkinson'),
        ):
            name = f'{initials} {surname}'
            with self.subTest(name=name):
                roles = [row for row in self.roles[listing] if row['surname'] == surname]
                self.assertTrue(roles)
                for row in roles:
                    self.assertEqual((row['person_as_printed'], row['given_or_initials'], row['honorifics']),
                                     (name, initials, []))
        self.assertIn('The City Line', {row['target_as_printed'] for row in self.connections[CLARK]})
        for suffix in ('Ltd.', 'Co.', 'Bros.', 'Jr.', 'St.', 'J.P.'):
            self.assertEqual(trim_full_stop(f'Name {suffix}'), f'Name {suffix}')
        observed = {value for rows in self.roles.values() for row in rows for value in row['honorifics']}
        self.assertEqual(observed, REVIEWED_HONORIFICS)
        self.assertEqual(observed, set(self.validation['honorific_values']))
        print('Distinct honorifics:', ', '.join(self.validation['honorific_values']))

    def test_own_trades_and_dropped_promotion(self):
        self.assertEqual(self.listings[WEBSTER]['trades'],
                         ['Tea Buyers', 'Blenders', 'Packers', 'Exporters', 'Estate Agents'])
        self.assertEqual({row['target_as_printed'] for row in self.connections[WEBSTER]}, {
            'J. & J. Makin, Ltd.', 'Tea Planters, Ltd.', 'Brown & Dureau, Ltd.',
            'Co-operative Tea Gardens Co.', 'Maravilla Ceylon Tea Co.',
        })
        self.assertEqual(self.validation['dropped_phrases'][DUNLOP], 1)
        self.assertEqual(len(self.connections[DUNLOP]), 5)

    def test_branch_and_office_addresses(self):
        self.assertEqual([(row['target_as_printed'], row['target_address_as_printed'])
                          for row in self.connections[DUNLOP] if row['relation_class'] == 'branch_at'], [
            ('Bombay', 'Dadysett Road, Chowpatti'), ('Calcutta', '8, Lindsay Street'),
            ('Madras', '16/2, Mount Road'), ('Delhi', 'Mori Gate'),
        ])
        for listing, town, address in (
            (DUNLOP, 'London', 'Dunlop House, 1, Albany St.'),
            (EASTERN, 'London', 'Electrica House, Finsbury Pavement'),
            (POPOFF, 'Moscow', None),
        ):
            offices = [row for row in self.connections[listing] if row['relation_class'] == 'head_office']
            self.assertEqual(len(offices), 1)
            office = offices[0]
            self.assertEqual(office['target_as_printed'], town)
            self.assertEqual(office['target_place_as_printed'], town)
            self.assertEqual(office['target_address_as_printed'], address)
        branches = [row for row in self.connections[POPOFF] if row['relation_class'] == 'branch_at']
        self.assertEqual([row['target_as_printed'] for row in branches],
                         ['Hankow', 'Colombo', 'London', 'Calcutta', 'all Principal Cities in Russia'])
        self.assertIn('unspecific_place', branches[-1]['flags'])

    def test_correspondent_places_and_addresses(self):
        planters, = [row for row in self.connections[WEBSTER] if row['target_as_printed'] == 'Tea Planters, Ltd.']
        self.assertEqual(planters['target_place_as_printed'], 'Bale & Paris')
        self.assertIsNone(planters['target_address_as_printed'])
        correspondents = [row for row in self.connections[BOIS] if row['source_locator'] == BOIS
                          and row['relation_class'] == 'correspondent']
        roadside = [(row['target_as_printed'], row['target_place_as_printed'], row['target_address_as_printed'])
                    for row in correspondents if row['target_address_as_printed']]
        self.assertEqual(roadside, [
            ('Anglo-Ceylon & General Estates Co., Ltd.', 'London, E. C.', '20, Essex-chap'),
            ('Robertson, Bois & Co.', 'London, E. C.', '12, Feuchurch Street'),
            ('M P. Evans & Co.', 'London', '30, Mincing Lane'),
            ('Jaeger & Co.', 'London; New York', '21, Mincing Lane; 150, Nassau St.'),
        ])
        self.assertEqual(len(correspondents), 9)

    def test_per_pro_and_second_name(self):
        assistants = {row['surname']: row['per_pro'] for row in self.roles[CLARK]
                      if row['role_as_printed'] == 'Assistants'}
        self.assertEqual(assistants, {'Bell': True, 'Kenyon': True, 'Bostock': True,
                                     'Francillon': False, 'Howard-Smith': False, 'Edge': False, 'Spence': False})
        self.assertEqual(self.listings[CLARK]['other_names_as_printed'], ['Walkers & Clark Spence (Galle)'])
        self.assertIn('ferg1922:p468:b6:r7', self.listings)
        self.assertTrue(all(isinstance(row['other_names_as_printed'], list) for row in self.listings.values()))
        self.assertTrue(all(type(row['per_pro']) is bool for rows in self.roles.values() for row in rows))

    def test_direction_of_agents(self):
        for listing, name in (
            (POPOFF, 'James Finlay & Co, Ltd'),
            ('ferg1922:p467:b3:r0', 'George Stewart & Co.'),
            ('ferg1922:p464:b3:r25', 'Henderson & Co.'),
        ):
            agent, = [row for row in self.connections[listing] if row['relation_class'] == 'has_agent']
            self.assertEqual(agent['target_as_printed'], name)
            self.assertIsNone(agent['target_place_as_printed'])

    def test_overflow(self):
        shipping = {row['target_as_printed']: row for row in self.connections[CLARK]}
        self.assertIn('The Ellerman & Bucknall Steamship Co., Ld.', shipping)
        self.assertEqual(shipping['The Northern Steamship Co., Ltd.']['target_place_as_printed'], 'Petrograd')
        all_connections = [row for rows in self.connections.values() for row in rows]
        self.assertTrue(any(row['target_as_printed'] == 'The Duff Estates Co., Ltd' for row in all_connections))
        unknown, = [row for row in all_connections if row['target_as_printed'] == "Ant. Jurgens' Marine Works gen"]
        self.assertIn('ocr_doubtful', unknown['flags'])
        for row in all_connections:
            for field in ('target_as_printed', 'target_place_as_printed', 'target_address_as_printed'):
                self.assertIn(field, row)
                self.assertNotRegex(row[field] or '', r'[\[\]]')

    def test_validation(self):
        for check in ('unique_ids', 'valid_references', 'fields_at_most_200'):
            self.assertIs(self.validation[check], True)
        for field, index in (('role_class', self.roles), ('relation_class', self.connections)):
            self.assertEqual(self.validation[field + '_counts'],
                             Counter(row[field] for rows in index.values() for row in rows))

    def test_audit_samples_and_totals(self):
        with (ROOT / 'audit_repair1.tsv').open(encoding='utf-8', newline='') as src:
            observations = list(csv.DictReader(src, delimiter='\t'))
        for phase, sample, expected in zip(('1', '2'), repair_samples(), ((573, 123, 30), (346, 48, 8))):
            rows = [row for row in observations if row['round'] == phase]
            self.assertEqual(set(sample) - {row['listing_id'] for row in rows},
                             set() if phase == '1' else {'ferg1922:p500:b2:r4'})
            checked = [row for row in rows if row['kind'] in ('role', 'connection')]
            missing = [row for row in rows if row['kind'] in ('missing_role', 'missing_connection')]
            self.assertEqual((len(checked), sum(row['agrees'] == 'no' for row in checked), len(missing)), expected)
            self.assertTrue(all(row['record_id'].startswith(row['listing_id'] + ':') for row in checked))
            self.assertTrue(all(not row['record_id'] and row['agrees'] == 'no' and row['comment'] for row in missing))
            self.assertTrue(all(row['listing_id'] in sample for row in rows))


if __name__ == '__main__':
    unittest.main()
