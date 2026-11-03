"""Presentation changes must preserve source explanations and reject stale metadata."""
import hashlib
import unittest
from unittest.mock import patch
import static_figures as sf


class StaticFigureTest(unittest.TestCase):
    source='<figure class="viz"><div class="viz-cols"><div class="col"><div class="node"><strong>Owner</strong><small>Local state</small><div class="node"><strong>Child</strong><small>Nested detail</small></div></div></div></div><figcaption>The child belongs to its owner.</figcaption></figure>'

    def model(self, **extra):
        return dict(path='fixture',figure=1,source_sha256=hashlib.sha256(self.source.encode()).hexdigest(),
                    title='Nested ownership',roles=['runtime','storage'],kind='comparison',
                    sources=['https://developer.android.com/topic/libraries/architecture/viewmodel'],**extra)

    def render(self,row,source=None):
        with patch.object(sf,'load',return_value={('fixture',1):row}):
            return sf.render('fixture.md',source or self.source)

    def test_comparison_keeps_nested_structure_and_all_words(self):
        result=self.render(self.model())
        tree,nodes=sf.content(result)
        self.assertEqual(len(nodes),2)
        self.assertIs(nodes[1].parent,nodes[0])
        self.assertEqual(sf.describe(nodes[0]),('Owner','Local state'))
        self.assertEqual(sf.describe(nodes[1]),('Child','Nested detail'))
        self.assertIn('Visual 1.',result)
        self.assertIn('Figure sources',result)
        self.assertIn('actor-storage',nodes[1].classes())

    def test_changed_source_requires_review_instead_of_reusing_roles(self):
        with self.assertRaisesRegex(ValueError,'changed; review'):
            self.render(self.model(),self.source.replace('Child','Other actor'))

    def test_missing_model_fails_outside_pending_preview(self):
        with patch.object(sf,'load',return_value={}),patch.dict('os.environ',{'WEBSITE_PENDING_FIGURES':'0'}):
            with self.assertRaisesRegex(ValueError,'missing static figure model'):
                sf.render('fixture',self.source)

    def test_roles_must_cover_every_card(self):
        row=self.model();row['roles']=['runtime']
        with self.assertRaisesRegex(ValueError,'one valid role per node'):
            self.render(row)

    def test_relationship_cannot_drop_a_source_card(self):
        row=self.model(edges=[],keep_nodes=[1]);row['kind']='map'
        with self.assertRaisesRegex(ValueError,'Every source card'):
            sf.as_map(row,self.source)

    def test_card_can_become_an_explicit_edge_annotation_without_losing_text(self):
        row=self.model(edges=[[1,1,{'card':2}]],keep_nodes=[1]);row['kind']='map'
        result=sf.as_map(row,self.source)
        self.assertEqual(result['edges'][0]['label'],'Child — Nested detail')
        self.assertEqual(result['nodes'][0]['detail'],'Local state')
        self.assertTrue(result['node_descriptions'])

    def test_order_does_not_silently_create_relationships(self):
        source=self.source.replace('<div class="viz-cols">','<div class="viz-flow"><span class="arrow"></span>')
        row=self.model();row['source_sha256']=hashlib.sha256(source.encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,'explicit endpoints'):
            self.render(row,source)

    def test_unused_models_cannot_survive_a_complete_build(self):
        with patch.object(sf,'load',return_value={('fixture',1):self.model()}),patch.object(sf,'SEEN',set()):
            with self.assertRaisesRegex(ValueError,'Unused static figure'):
                sf.check_coverage()


if __name__=='__main__':unittest.main()
