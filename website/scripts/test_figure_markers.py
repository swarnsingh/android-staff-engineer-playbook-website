"""Arrowheads must reference marker definitions in their own rendered SVG."""
import re
import unittest
import xml.etree.ElementTree as ET

import figure_maps


class FigureMarkerTests(unittest.TestCase):
    def assert_resolved_markers(self, markup):
        svg = ET.fromstring(re.search(r'<svg\b.*?</svg>', markup, re.S).group())
        markers = {node.attrib['id'] for node in svg.iter('marker')}
        references = []
        for node in svg.iter():
            for attribute in ('marker-start', 'marker-end'):
                if attribute in node.attrib:
                    target = re.fullmatch(r'url\(#([^)]*)\)', node.attrib[attribute])
                    self.assertIsNotNone(target)
                    references.append(target.group(1))
        self.assertTrue(references, 'Fixture must exercise arrowheads')
        self.assertTrue(set(references) <= markers, f'Unresolved markers: {set(references) - markers}')
        return markers

    def fixture(self, kind, key='marker-fixture'):
        row = dict(path='fixture', diagram=key, kind=kind, number=1,
                   title='Marker fixture', caption='Every arrow has a direction.',
                   sources=['https://www.w3.org/TR/SVG2/painting.html'])
        actors = [dict(id='a', title='Source', role='runtime'),
                  dict(id='b', title='Target', role='storage')]
        if kind == 'map':
            row.update(nodes=actors, edges=[dict(**{'from': 'a', 'to': 'b'}, label='Exchange', both=True)])
        else:
            row.update(participants=actors, events=[dict(**{'from': 'a', 'to': 'b'}, label='Deliver'),
                                                    dict(at='a', label='Continue locally')])
        return figure_maps.render(row, 'original source')[0]

    def test_map_arrowheads_resolve_including_bidirectional_edges(self):
        self.assert_resolved_markers(self.fixture('map'))

    def test_sequence_message_and_self_arrowheads_resolve(self):
        self.assert_resolved_markers(self.fixture('sequence'))

    def test_different_figures_have_distinct_marker_ids(self):
        first = self.assert_resolved_markers(self.fixture('map', 'first-fixture'))
        second = self.assert_resolved_markers(self.fixture('sequence', 'second-fixture'))
        self.assertFalse(first & second)


if __name__ == '__main__':
    unittest.main()
