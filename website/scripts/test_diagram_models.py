"""Regressions for diagram identity, source-label safety, and ownership semantics."""
from contextlib import contextmanager
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import tempfile
import unittest
from unittest.mock import patch

import diagram_models


def model(path='sample', figure=0, *, nodes=('owner', 'child')):
    return {
        'path': path, 'figure': figure,
        'problem': 'Which owner retains this child?',
        'reading': 'The arrow means ownership, not an inferred value transfer.',
        'groups': [],
        'edges': [{'from': nodes[0], 'to': nodes[1], 'label': 'owns this child'}],
        'labels': {nodes[0]: 'Owner instance', nodes[1]: 'Child instance'},
        'sources': ['https://kotlinlang.org/docs/coroutines-basics.html'],
    }


@contextmanager
def registry(rows, coverage=None):
    """Use a disposable authored registry, never the user's production files."""
    if coverage is None:
        coverage = [{'path': r['path'], 'figure': r['figure'], 'nodes': [
            {'id': n, 'kind': 'worker', 'role': 'runtime'} for n in r['labels']
        ]} for r in rows]
    with tempfile.TemporaryDirectory() as temporary:
        web = Path(temporary)
        (web/'content/diagram-models').mkdir(parents=True)
        (web/'content/diagram-models/test.json').write_text(json.dumps(rows))
        (web/'content/illustrated-stepper-coverage.json').write_text(json.dumps({'figures': coverage}))
        out = web/'dist'
        (out/'diagram-sources').mkdir(parents=True)
        with patch.object(diagram_models, 'WEB', web):
            yield out


def figure(*actors):
    return '<figure class="stepper"><span class="stepper-title">Example</span><div class="stage">' + ''.join(
        '<div class="node" data-el="'+actor+'" data-art-role="runtime"><strong>'+actor+'</strong></div>'
        for actor in actors
    ) + '</div><script type="application/json" class="steps">[]</script></figure>'


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class DiagramModelTest(unittest.TestCase):
    def test_reordered_figures_keep_their_actor_bound_explanations(self):
        """Blend insertion order must not swap two different lessons' explanations."""
        first = model('sample', 0, nodes=('binding', 'collection'))
        first['problem'] = 'Can a fixed binding still refer to a mutable collection?'
        second = model('sample', 1, nodes=('closure', 'captured'))
        second['problem'] = 'What survives after the creating call returns?'
        with registry([first, second]) as out:
            enhanced = diagram_models.enhance(
                figure('closure', 'captured') + figure('binding', 'collection'),
                'kotlin/language-core/sample.md', out, '/', diagram_models.check(),
            )
            payloads = [json.loads(s) for s in re.findall(
                r'<script type="application/json" class="relationship-model">(.*?)</script>', enhanced, re.S
            )]
            self.assertEqual([r['figure'] for r in payloads], [1, 0])
            self.assertEqual([r['problem'] for r in payloads], [second['problem'], first['problem']])
            self.assertEqual([[n['id'] for n in r['actors']] for r in payloads],
                             [['closure', 'captured'], ['binding', 'collection']])
            # Each drawn map must carry its own lesson's labels, in the same order as its payload.
            maps = re.findall(r'<div class="relationship-map".*?</svg></div>', enhanced, re.S)
            for row, payload, drawn in zip([second, first], payloads, maps):
                self.assertIn(row['labels'][payload['actors'][0]['id']], drawn)

    def test_missing_actor_binding_fails_instead_of_using_figure_position(self):
        row = model()
        with registry([row]) as out:
            with self.assertRaisesRegex(ValueError, 'Ambiguous/missing relationship map'):
                diagram_models.enhance(figure('owner', 'unrelated'), 'kotlin/language-core/sample.md',
                                       out, '/', diagram_models.check())

    def test_reused_actor_ids_are_ambiguous_instead_of_silently_mislabelled(self):
        first = model('sample', 0)
        second = model('sample', 1)
        second['problem'] = 'Different mechanism with accidentally reused actor IDs'
        with registry([first, second]) as out:
            with self.assertRaisesRegex(ValueError, 'Ambiguous/missing relationship map'):
                diagram_models.enhance(figure('owner', 'child'), 'kotlin/language-core/sample.md',
                                       out, '/', diagram_models.check())

    def test_label_text_cannot_inject_html_into_the_drawn_map(self):
        row = model()
        malicious = '"][Injected] --> rogue <script>alert("x")</script>&'
        row['labels']['owner'] = malicious
        row['groups'] = [{'id': 'scope', 'label': 'Scope', 'nodes': ['child']}]
        row['edges'][0]['label'] = malicious
        with registry([row]) as out:
            enhanced = diagram_models.enhance(figure('owner', 'child'), 'kotlin/language-core/sample.md',
                                               out, '/', diagram_models.check())
        drawn = re.search(r'<div class="relationship-map".*?</svg></div>', enhanced, re.S)[0]
        self.assertNotIn('<script>', drawn)
        self.assertIn('&lt;script&gt;', drawn)
        self.assertIn('&quot;', drawn)
        # Two actors and one relationship: the label text adds no extra cards or arrows.
        self.assertEqual(len(re.findall(r'class="fm-node ', drawn)), 2)
        self.assertEqual(len(re.findall(r'class="fm-edge', drawn)), 1)

    def test_script_terminator_in_explanation_stays_json_text(self):
        row = model()
        row['problem'] = '</script><img src=x onerror="alert(1)">'
        with registry([row]) as out:
            enhanced = diagram_models.enhance(figure('owner', 'child'), 'kotlin/language-core/sample.md',
                                               out, '/', diagram_models.check())
        parser = Tags(); parser.feed(enhanced)
        self.assertFalse(any(tag == 'img' for tag, _ in parser.tags))
        self.assertEqual(sum(tag == 'script' for tag, _ in parser.tags), 2)  # steps + model
        payload = re.search(r'class="relationship-model">(.*?)</script>', enhanced, re.S)[1]
        self.assertEqual(json.loads(payload)['problem'], row['problem'])

    def test_nested_ownership_remains_nested_and_each_actor_occurs_once(self):
        row = model(nodes=('owner', 'request'))
        row['labels']['worker'] = 'Worker child'
        row['groups'] = [
            {'id': 'application', 'label': 'Application scope', 'nodes': ['owner']},
            {'id': 'request-scope', 'label': 'Request subtree', 'nodes': ['request'], 'parent': 'application'},
            {'id': 'workers', 'label': 'Worker children', 'nodes': ['worker'], 'parent': 'request-scope'},
        ]
        coverage = [{'path': 'sample', 'figure': 0, 'nodes': [{'id': n, 'kind': 'worker', 'role': 'runtime'} for n in row['labels']]}]
        with registry([row], coverage) as out:
            enhanced = diagram_models.enhance(figure('owner', 'request', 'worker'), 'kotlin/language-core/sample.md',
                                               out, '/', diagram_models.check())
        drawn = re.search(r'<div class="relationship-map".*?</svg></div>', enhanced, re.S)[0]
        boxes = {re.sub(r'<[^>]+>', '', m[4]): tuple(float(v) for v in m[:4]) for m in re.findall(
            r'<g class="fm-group"><rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.]+)" height="([\d.]+)"[^>]*/>(<text.*?</text>)', drawn)}
        inside = lambda a, b: b[0] <= a[0] and b[1] <= a[1] and a[0] + a[2] <= b[0] + b[2] and a[1] + a[3] <= b[1] + b[3]
        self.assertTrue(inside(boxes['Request subtree'], boxes['Application scope']))
        self.assertTrue(inside(boxes['Worker children'], boxes['Request subtree']))
        for actor in ('Owner instance', 'Worker child'):
            self.assertEqual(drawn.count('· ' + actor + '<'), 1, 'An actor drawn twice suggests conflicting ownership')

    def test_unknown_relationship_endpoint_is_rejected(self):
        row = model(); row['edges'][0]['to'] = 'missing-owner'
        with registry([row]), self.assertRaisesRegex(ValueError, 'Invalid relationship'):
            diagram_models.check()

    def test_unknown_boundary_member_is_rejected(self):
        row = model(); row['groups'] = [{'id': 'scope', 'label': 'Scope', 'nodes': ['not-an-actor']}]
        with registry([row]), self.assertRaisesRegex(ValueError, 'Invalid boundary'):
            diagram_models.check()

    def test_actor_cannot_have_two_owners(self):
        row = model(); row['groups'] = [
            {'id': 'first', 'label': 'First owner', 'nodes': ['child']},
            {'id': 'second', 'label': 'Second owner', 'nodes': ['child']},
        ]
        with registry([row]), self.assertRaisesRegex(ValueError, 'two owners'):
            diagram_models.check()

    def test_unknown_parent_boundary_is_rejected(self):
        row = model(); row['groups'] = [{'id': 'scope', 'label': 'Scope', 'nodes': [], 'parent': 'absent'}]
        with registry([row]), self.assertRaisesRegex(ValueError, 'Unknown parent boundary'):
            diagram_models.check()

    def test_cyclic_ownership_is_rejected(self):
        for groups in [
            [{'id': 'a', 'label': 'A', 'nodes': [], 'parent': 'a'}],
            [{'id': 'a', 'label': 'A', 'nodes': [], 'parent': 'b'},
             {'id': 'b', 'label': 'B', 'nodes': [], 'parent': 'a'}],
        ]:
            row = model(); row['groups'] = deepcopy(groups)
            with self.subTest(groups=groups), registry([row]), self.assertRaisesRegex(ValueError, 'Cyclic ownership'):
                diagram_models.check()

    def test_duplicate_models_are_rejected_instead_of_overwriting_content(self):
        row = model()
        with registry([row, deepcopy(row)]), self.assertRaisesRegex(ValueError, 'Duplicate relationship map'):
            diagram_models.check()


if __name__ == '__main__':
    unittest.main()
