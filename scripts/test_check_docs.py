#!/usr/bin/env python3
"""Regression tests for Markdown-sensitive documentation quality gates."""

import unittest

from check_docs import numbered_ordinals, question_answer_coverage


class NumberedOrdinalsTests(unittest.TestCase):
    """Exercise list rules from https://spec.commonmark.org/current/#list-items."""

    def assert_ordinals(self, source: str, expected: list[int]) -> None:
        self.assertEqual(numbered_ordinals(source), expected)

    def test_dot_and_parenthesis_markers(self) -> None:
        self.assert_ordinals("1. One\n2. Two", [1, 2])
        self.assert_ordinals("1) One\n2) Two", [1, 2])

    def test_root_items_may_have_up_to_three_leading_spaces(self) -> None:
        for indent in ("", " ", "  ", "   "):
            with self.subTest(indent=len(indent)):
                self.assert_ordinals(f"{indent}1. One\n{indent}2. Two", [1, 2])

    def test_four_space_indented_markers_are_code(self) -> None:
        self.assert_ordinals("    1. output\n1. Answer", [1])

    def test_nested_ordered_lists_are_excluded(self) -> None:
        self.assert_ordinals("1. Answer\n   1. Detail\n2. Answer", [1, 2])

    def test_nested_list_after_wide_marker_is_excluded(self) -> None:
        self.assert_ordinals("10. Answer\n    1. Detail\n11. Answer", [10, 11])

    def test_two_space_marker_after_dot_item_is_still_root(self) -> None:
        source = "1. First\n  1. Duplicate\n2. Second"
        self.assert_ordinals(source, [1, 1, 2])

    def test_list_context_resets_after_root_paragraph(self) -> None:
        source = "1. First\n\nroot paragraph\n\n   2. Second"
        self.assert_ordinals(source, [1, 2])

    def test_separate_root_lists_are_combined(self) -> None:
        source = "1. First\n\n---\n\n2. Second"
        self.assert_ordinals(source, [1, 2])

    def test_backtick_and_tilde_fenced_content_is_excluded(self) -> None:
        for fence in ("```text", "~~~text"):
            with self.subTest(fence=fence):
                closing = fence[:3]
                source = f"1. First\n\n{fence}\n2. output\n{closing}\n\n2. Second"
                self.assert_ordinals(source, [1, 2])

    def test_invalid_backtick_info_string_does_not_open_fence(self) -> None:
        source = "1. First\n\n```bad`info\n\n2. Second"
        self.assert_ordinals(source, [1, 2])

    def test_marker_is_limited_to_nine_digits(self) -> None:
        source = "123456789. Valid\n1234567890. Paragraph"
        self.assert_ordinals(source, [123456789])

    def test_tab_indented_marker_is_code_not_root_list(self) -> None:
        self.assert_ordinals("\t1. output\n1. Answer", [1])

    def test_ordered_list_inside_bullet_list_is_excluded(self) -> None:
        source = "- Context\n  1. Nested\n\n1. Answer"
        self.assert_ordinals(source, [1])

    def test_ordered_list_inside_block_quote_is_excluded(self) -> None:
        source = "> 1. Quoted example\n\n1. Answer"
        self.assert_ordinals(source, [1])

    def test_marker_like_text_that_does_not_render_as_a_list_is_excluded(self) -> None:
        source = "Paragraph\n2. This cannot interrupt a paragraph\n\n1. Answer"
        self.assert_ordinals(source, [1])


class QuestionAnswerCoverageTests(unittest.TestCase):
    def check(self, body: str) -> tuple[bool, list[str]]:
        return question_answer_coverage("## Probing Questions\n\n" + body)

    def test_legacy_numbered_key_still_passes(self) -> None:
        self.assertEqual(self.check("1. Why?\n2. When?\n\n## Answer Key\n\n1. Because.\n2. Now."), (False, []))

    def test_legacy_mismatched_and_duplicate_answers_fail(self) -> None:
        for answers in ("1. First.", "1. First.\n1. Duplicate.", "1. First.\n3. Third."):
            with self.subTest(answers=answers):
                missing, errors = self.check("1. Why?\n2. When?\n\n## Answer Key\n\n" + answers)
                self.assertFalse(missing)
                self.assertTrue(errors)

    def test_missing_legacy_key_retains_warning_only(self) -> None:
        self.assertEqual(self.check("1. Why?"), (True, []))

    def test_present_empty_legacy_key_fails(self) -> None:
        missing, errors = self.check("1. Why?\n\n## Answer Key\n")
        self.assertFalse(missing)
        self.assertTrue(errors)

    def test_adjacent_pairs_with_prose_questions_pass(self) -> None:
        body = "### Question 1\n\nWhy?\n\n#### Answer\n\nBecause.\n\n### Question 2\n\nWhen?\n\n#### Answer\n\nNow."
        self.assertEqual(self.check(body), (False, []))

    def test_question_text_in_numbered_heading_passes(self) -> None:
        self.assertEqual(self.check("### Question 1: Why?\n\n#### Answer\n\nBecause."), (False, []))

    def test_missing_paired_answer_fails_instead_of_warning(self) -> None:
        missing, errors = self.check("### Question 1\n\nWhy?")
        self.assertFalse(missing)
        self.assertTrue(errors)

    def test_empty_paired_answer_and_heading_only_answer_fail(self) -> None:
        for body in ("", "##### Additional detail\n", "<!-- Answer pending -->"):
            with self.subTest(body=body):
                _, errors = self.check("### Question 1\n\nWhy?\n\n#### Answer\n\n" + body)
                self.assertTrue(any("answer text is empty" in error for error in errors))

    def test_empty_question_fails(self) -> None:
        _, errors = self.check("### Question 1\n\n#### Answer\n\nBecause.")
        self.assertTrue(any("question text is empty" in error for error in errors))

    def test_paired_numbering_gap_and_duplicate_fail(self) -> None:
        for number in (1, 3):
            with self.subTest(number=number):
                body = f"### Question 1: Why?\n\n#### Answer\n\nBecause.\n\n### Question {number}: When?\n\n#### Answer\n\nNow."
                _, errors = self.check(body)
                self.assertTrue(any("question numbers" in error for error in errors))

    def test_answer_markers_in_code_and_nested_lists_do_not_count(self) -> None:
        for fake in ("```markdown\n#### Answer\nBecause.\n```", "- Example\n  #### Answer\n  Because.", "> #### Answer\n> Because."):
            with self.subTest(fake=fake):
                _, errors = self.check("### Question 1\n\nWhy?\n\n" + fake)
                self.assertTrue(any("found 0" in error for error in errors))

    def test_intervening_heading_fails_immediate_pairing(self) -> None:
        _, errors = self.check("### Question 1\n\nWhy?\n\n#### Other material\n\nLater.\n\n#### Answer\n\nBecause.")
        self.assertTrue(any("next heading" in error for error in errors))

    def test_duplicate_paired_answer_and_mixed_formats_fail(self) -> None:
        body = "### Question 1: Why?\n\n#### Answer\n\nBecause."
        for extra in ("\n\n#### Answer\n\nAgain.", "\n\n## Answer Key\n\n1. Because."):
            with self.subTest(extra=extra):
                self.assertTrue(self.check(body + extra)[1])

    def test_code_example_does_not_create_a_probing_section(self) -> None:
        self.assertEqual(question_answer_coverage("```markdown\n## Probing Questions\n### Question 1\nWhy?\n```"), (False, []))

    def test_ordinary_checklists_need_no_answers(self) -> None:
        self.assertEqual(question_answer_coverage("## Review Checklist\n\n- [ ] Check cancellation.\n- [ ] Verify ownership."), (False, []))

    def test_unrelated_next_section_is_not_an_answer(self) -> None:
        _, errors = self.check("### Question 1: Why?\n\n#### Answer\n\n### Notes\n\nUnrelated prose.")
        self.assertTrue(any("answer text is empty" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
