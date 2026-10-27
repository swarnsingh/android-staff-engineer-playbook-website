"""Regression for inline correction marks crossing Markdown table cells."""
import unittest
from unittest.mock import patch
import build
class CorrectionRenderingTest(unittest.TestCase):
 def corrected(self,source,old,new):
  with patch.object(build,'APPROVED_CORRECTIONS',[dict(path='test.md',old=old,new=new,reason='fixture',sources=[])]):
   return build.corrected(source,'test.md',mark=True)[0]
 def test_partial_row_spanning_cells_uses_section_disclosure(self):
  source='| Dispatcher | Policy |\n|---|---|\n| `Main` | old |\n| `IO` | next |\n'
  corrected=self.corrected(source,'`Main` | old','`Main` | corrected')
  self.assertNotIn('<mark',corrected)
  html=build.MD.render(corrected)
  self.assertIn('<td>next</td>',html)
  self.assertEqual(html.count('<tr>'),3)
 def test_normal_prose_keeps_visible_mark(self):
  self.assertIn('<mark',self.corrected('The old claim.','old','corrected'))
 def test_fenced_code_is_not_marked(self):
  self.assertNotIn('<mark',self.corrected('```kotlin\nval x = 1\n```','val x = 1','val x = 2'))
if __name__=='__main__':unittest.main()
