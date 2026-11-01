"""New topic names must not reclassify existing nested Android routes."""
import unittest
from unittest.mock import patch
import check_completion


class AuditTreeTests(unittest.TestCase):
    def test_nested_observability_remains_android(self):
        with patch.object(check_completion.build, 'BASE', '/'):
            self.assertEqual(check_completion.audit_tree('/android/observability/logging/'), 'android')
            self.assertEqual(check_completion.audit_tree('/observability/logging/'), 'observability')

    def test_project_prefix_is_removed_before_tree_classification(self):
        prefix = '/android-staff-engineer-playbook-website/'
        with patch.object(check_completion.build, 'BASE', prefix):
            self.assertEqual(check_completion.audit_tree(prefix + 'android/observability/logging/'), 'android')
            self.assertEqual(check_completion.audit_tree(prefix + 'observability/logging/'), 'observability')
            self.assertEqual(check_completion.audit_tree('/android/observability/logging/'), 'android')


if __name__ == '__main__':
    unittest.main()
