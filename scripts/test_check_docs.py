#!/usr/bin/env python3
"""Regression tests for Markdown-sensitive documentation quality gates."""

import unittest

from check_docs import numbered_ordinals


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


if __name__ == "__main__":
    unittest.main()
