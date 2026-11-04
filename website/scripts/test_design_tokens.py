"""Token substitutions preserve CSS scope; malformed authoring fails the build."""
import unittest
from unittest.mock import patch

import design_tokens
import figure_maps


class DesignTokensTest(unittest.TestCase):
    def test_composite_values_keep_relative_units_and_local_variables(self):
        css = '@media(max-width:{{phone}}){.node{padding:{{pad}};color:var(--actor)}}'
        self.assertEqual(design_tokens.compile_css(css, {'phone':'640px','pad':'.5em var(--inset)'}),
                         '@media(max-width:640px){.node{padding:.5em var(--inset);color:var(--actor)}}')

    def test_unknown_or_malformed_tokens_fail(self):
        for source in ['a{width:{{missing}}}', 'a{width:{{Bad name}}}']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                design_tokens.compile_css(source, {})

    def test_boundary_rejects_new_dimensions_including_media_queries(self):
        for source in ['a{padding:2rem}', '@media(max-width:500px){}',
                       'a{transform:rotate(20deg)}', 'a{width:90%}', 'a{animation:x .5s}']:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'Raw component dimension'):
                design_tokens.check_source(source)

    def test_boundary_allows_structural_constants_and_quoted_labels(self):
        design_tokens.check_source('/* 12px */ a{width:100%;padding:0;grid:1fr 1fr;content:"12px";gap:{{gap}}}')

    def test_geometry_rejects_duplicates_and_invalid_values(self):
        bad = [
            [{'name':'x','value':2}, {'name':'x','value':3}],
            [{'name':'x','value':float('nan')}],
            [{'name':'x','value':True}],
            [{'name':'x','value':'<script>'}],
        ]
        for rows in bad:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                design_tokens.geometry_values(rows)

    def test_sequence_layout_uses_geometry_token(self):
        row = {'participants':[{'id':'sender','title':'Sender','role':'client'},
                               {'id':'receiver','title':'Receiver','role':'runtime'}],
               'events':[{'from':'sender','to':'receiver','label':'send'}]}
        before = figure_maps.render_sequence(row, 'token-test')
        with patch.dict(figure_maps.GEOMETRY, {'sequence-lane-gap':figure_maps.GEOMETRY['sequence-lane-gap']-20}):
            after = figure_maps.render_sequence(row, 'token-test')
        self.assertNotEqual(before, after)


if __name__ == '__main__':unittest.main()
