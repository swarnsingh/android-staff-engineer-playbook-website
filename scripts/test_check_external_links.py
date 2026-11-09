import unittest

import check_external_links as checker


class PrivateRepositoryTest(unittest.TestCase):
    def test_skips_private_source_repository_and_its_pages(self):
        self.assertTrue(checker.is_private("https://github.com/swarnsingh/android-staff-engineer-playbook"))
        self.assertTrue(checker.is_private("https://github.com/swarnsingh/android-staff-engineer-playbook/pull/81"))

    def test_checks_public_website_repository(self):
        self.assertFalse(checker.is_private("https://github.com/swarnsingh/android-staff-engineer-playbook-website"))
        self.assertFalse(checker.is_private("https://github.com/swarnsingh/android-staff-engineer-playbook-website/pull/3"))


if __name__ == "__main__":
    unittest.main()
