"""The phone ladder must keep every card, owner and numbered relationship of the wide drawing."""
import re
import unittest
import xml.etree.ElementTree as ET

import figure_maps as fm


def model(**extra):
    row = dict(path='fixture', diagram='ladder-fixture', kind='map', number=1, title='Ladder fixture',
               caption='Relationships keep their labels on a phone.', sources=['https://www.w3.org/TR/SVG2/'],
               nodes=[dict(id='ask', title='Do you query many items?', role='neutral'),
                      dict(id='room', title='Room', detail='tables and observable queries', role='storage'),
                      dict(id='doc', title='One settings document?', role='neutral'),
                      dict(id='proto', title='Proto DataStore', role='storage'),
                      dict(id='prefs', title='Preferences DataStore', role='storage')],
               edges=[{'from': 'ask', 'to': 'room', 'label': 'yes: query structured items'},
                      {'from': 'ask', 'to': 'doc', 'label': 'no: consider document shape'},
                      {'from': 'doc', 'to': 'proto', 'label': 'structured settings'},
                      {'from': 'doc', 'to': 'prefs', 'label': 'simple flags'},
                      {'from': 'prefs', 'to': 'ask', 'label': 'revisit when data grows', 'style': 'dashed'},
                      {'from': 'room', 'to': 'room', 'label': 'invalidates its own queries'}],
               groups=[{'id': 'stores', 'label': 'Stores', 'nodes': ['proto', 'prefs']}])
    row.update(extra)
    return row


def ladder(row, budget=None):
    budget = budget or fm.px('figure-phone-width')
    for wrap in fm.geometry_value('phone-label-wraps'):
        layout = fm.phone_ladder(row, 'fixture', budget, wrap)
        if layout:
            return layout
    return None


def pills(svg):
    """(number, label) for every numbered relationship, in drawing order."""
    found = []
    for group in ET.fromstring(svg).iter('g'):
        if group.attrib.get('class') == 'fm-pill':
            texts = list(group.iter('text'))
            found.append((texts[0].text, ' '.join(t.text for t in texts[1:])))
    return found


class PhoneLadderTests(unittest.TestCase):
    def test_compact_drawing_keeps_every_numbered_relationship_and_text(self):
        result = fm.render(model(), '')[0]
        wide, compact = re.findall(r'<svg\b.*?</svg>', result, re.S)
        self.assertIn('data-figure-variant="compact"', compact)
        self.assertEqual(pills(wide), pills(compact))
        self.assertEqual(len(pills(compact)), len(model()['edges']))
        words = lambda svg: sorted(' '.join(ET.fromstring(svg).itertext()).split())
        self.assertEqual(words(wide), words(compact))
        width = float(re.search(r'width="([\d.]+)"', compact).group(1))
        self.assertLessEqual(width, fm.px('figure-phone-width'))

    def test_every_edge_leaves_its_source_and_enters_its_target(self):
        layout = ladder(model())
        cards = {n['id']: n for n in layout['nodes']}
        for e in layout['edges']:
            a, b = cards[e['from']], cards[e['to']]
            (sx, sy), (tx, ty) = e['points'][0], e['points'][-1]
            self.assertAlmostEqual(sy, a['y'] + fm.card_height(a))
            self.assertTrue(a['x'] < sx < a['x'] + a['w'])
            on_top = abs(ty - b['y']) < 1e-6 and b['x'] < tx < b['x'] + b['w']
            on_side = abs(tx - (b['x'] + b['w'])) < 1e-6 and b['y'] < ty < b['y'] + fm.card_height(b)
            self.assertTrue(on_top or on_side, e)

    def test_boundaries_enclose_exactly_their_members(self):
        layout = ladder(model())
        cards = {n['id']: dict(n, h=fm.card_height(n)) for n in layout['nodes']}
        x0, y0, x1, y1 = fm.group_box(layout['groups'][0], cards, layout['groups'])
        for nid, n in cards.items():
            inside = x0 <= n['x'] and n['x'] + n['w'] <= x1 and y0 <= n['y'] and n['y'] + n['h'] <= y1
            self.assertEqual(inside, nid in layout['groups'][0]['nodes'], nid)

    def test_no_label_hides_another_relationship(self):
        layout = ladder(model())
        self.assertTrue(fm.phone_lines_clear(layout))
        hidden = dict(layout, edges=[dict(e) for e in layout['edges']])
        hidden['edges'][1]['label_at'] = hidden['edges'][0]['points'][0]
        self.assertFalse(fm.phone_lines_clear(hidden))

    def test_words_are_never_split_to_fit_a_phone_card(self):
        row = model(nodes=[dict(n, title='ActivityTaskManagerServiceStartActivity') if n['id'] == 'room' else n for n in model()['nodes']])
        self.assertIsNone(ladder(row))
        self.assertIsNotNone(ladder(model()))

    def test_long_boundary_label_wraps_between_words_only_on_the_phone(self):
        label = 'Stores kept on the device for offline reads'
        row = model(groups=[{'id': 'stores', 'label': label, 'nodes': ['proto', 'prefs']}])
        layout = ladder(row)
        self.assertIsInstance(layout['groups'][0]['label'], list)
        self.assertEqual(' '.join(layout['groups'][0]['label']), label)
        wide, compact = re.findall(r'<svg\b.*?</svg>', fm.render(row, '')[0], re.S)
        group_texts = lambda svg: [[t.text for t in g.iter('text')] for g in ET.fromstring(svg).iter('g') if g.attrib.get('class') == 'fm-group']
        self.assertEqual(group_texts(wide), [[label]])
        self.assertGreater(len(group_texts(compact)[0]), 1)
        self.assertEqual(' '.join(group_texts(compact)[0]), label)
        cards = {n['id']: dict(n, h=fm.card_height(n)) for n in layout['nodes']}
        x0, y0, x1, y1 = fm.group_box(layout['groups'][0], cards, layout['groups'])
        for nid, n in cards.items():
            self.assertEqual(y0 <= n['y'] and n['y'] + n['h'] <= y1, nid in ('proto', 'prefs'), nid)

    def test_edges_sharing_a_wide_bus_keep_its_single_number_on_each_line(self):
        row = model(layout='layers', nodes=model()['nodes'][:4] + [dict(id='cache', title='Cache', role='storage')],
                    edges=[{'from': 'ask', 'to': t, 'label': 'reads from'} for t in ('room', 'doc', 'proto', 'cache')]
                    + [{'from': 'doc', 'to': 'proto', 'label': 'structured settings'}], groups=[])
        wide, compact = re.findall(r'<svg\b.*?</svg>', fm.render(row, '')[0], re.S)
        self.assertEqual(pills(wide), [('1', 'reads from'), ('2', 'structured settings')])
        self.assertEqual(sorted(set(pills(compact))), pills(wide))
        self.assertEqual(sum(1 for p in pills(compact) if p == ('1', 'reads from')), 4)

    def test_too_narrow_a_column_keeps_the_scrolling_drawing(self):
        self.assertIsNone(ladder(model(), budget=fm.geometry_value('phone-card-min')))


if __name__ == '__main__':
    unittest.main()
