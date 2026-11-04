"""The editorial inventory measures narrative, rather than diagram payloads."""
import unittest

from lesson_length import words


class LessonLengthTest(unittest.TestCase):
    def test_excludes_figures_and_fenced_examples_but_keeps_inline_identifiers(self):
        self.assertEqual(words('Keep `operationId` stable.\n\n```kotlin\nval ignored = true\n```\n\n'
                               '<figure><div>Ignore this picture</div><svg><text>label</text></svg></figure>\n\n'
                               'Then retry.'), 5)

    def test_nested_skips_and_void_tags_do_not_hide_following_prose(self):
        self.assertEqual(words('<div class="pb-figure"><div>Ignore<br>all</div></div>\n\n'
                               'Visible<br>words after.'), 3)

    def test_ordinary_tables_and_answer_guidance_count(self):
        self.assertEqual(words('| Choice | Cost |\n|---|---|\n| Retry | Duplicate |\n\n'
                               '<details><summary>Answer</summary>Keep the record.</details>'), 8)


if __name__ == '__main__':unittest.main()
