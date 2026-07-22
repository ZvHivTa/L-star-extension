"""Cache dependency tests for the integrated learner."""

import unittest

from learner import Learner


class CacheInvalidationTests(unittest.TestCase):
    def setUp(self):
        self.learner = Learner(None, {"a", "b"}, verbose=False)
        self.learner.row_cache["x"] = (False,)
        self.learner.suffix_row_cache["x"] = (False,)
        self.learner.sorted_p_cache = ("",)
        self.learner.sorted_s_cache = ("",)
        self.learner.sorted_i_cache = ("",)
        self.learner.right_extensions_cache = {"a", "b"}

    def test_p_change_preserves_suffix_and_i_caches(self):
        self.learner.invalidate_context_cache(p_changed=True)

        self.assertEqual(self.learner.row_cache, {})
        self.assertEqual(self.learner.suffix_row_cache["x"], (False,))
        self.assertIsNone(self.learner.sorted_p_cache)
        self.assertEqual(self.learner.sorted_s_cache, ("",))
        self.assertEqual(self.learner.sorted_i_cache, ("",))
        self.assertEqual(self.learner.right_extensions_cache, {"a", "b"})

    def test_s_change_invalidates_both_row_views(self):
        self.learner.invalidate_context_cache(s_changed=True)

        self.assertEqual(self.learner.row_cache, {})
        self.assertEqual(self.learner.suffix_row_cache, {})
        self.assertEqual(self.learner.sorted_p_cache, ("",))
        self.assertIsNone(self.learner.sorted_s_cache)

    def test_i_change_only_invalidates_i_derived_caches(self):
        self.learner.invalidate_context_cache(i_changed=True)

        self.assertEqual(self.learner.row_cache["x"], (False,))
        self.assertEqual(self.learner.suffix_row_cache["x"], (False,))
        self.assertIsNone(self.learner.sorted_i_cache)
        self.assertIsNone(self.learner.right_extensions_cache)


if __name__ == "__main__":
    unittest.main()
