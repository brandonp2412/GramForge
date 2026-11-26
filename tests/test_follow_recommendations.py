import runpy
import tempfile
import unittest
from pathlib import Path

PATCH = runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools/patch-follow-recommendations.py"))

class FollowRecommendationsTest(unittest.TestCase):
    def test_force_block_even_with_existing_preferences(self):
        before = ".method public static isSuggestedBlocked()Z\n    .locals 1\n    invoke-static {}, LExample;->getSavedValue()Z\n    move-result v0\n    return v0\n.end method"
        after = PATCH["config"](before)
        self.assertIn("const/4 v0, 0x1", after)
        self.assertNotIn("getSavedValue", after)

    def test_follow_requests_keeps_real_requests_and_followers(self):
        before = """    const-string v2, "exclude_suggested_users"
    move/from16 v3, p2
    invoke-static {v5, v2, v3}, LX/0222;->A1N(LX/06ux;Ljava/lang/String;Z)V
    const-string v2, "include_recent_auto_rf_followers"
    move/from16 v3, p3
    invoke-static {v5, v2, v3}, LX/0222;->A1N(LX/06ux;Ljava/lang/String;Z)V"""
        after = PATCH["follow_requests"](before)
        self.assertIn("const/4 v3, 0x1", after)
        self.assertIn('include_recent_auto_rf_followers"\n    move/from16 v3, p3', after)
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["follow_requests"](before.replace("exclude_suggested_users", "other"))

    def test_carousel_only_hides_dedicated_row_after_binding(self):
        before = """const v0, 0x7f0b3c6b
->A09:Lcom/instagram/ui/widget/nestablescrollingview/NestableHorizontalRecyclerPager;
.method public static final A01(LX/0O5i;)V
    .locals 15
    move-object/from16 v3, p9
    const-string v0, "see_all_in_header"
    return-void
.end method"""
        after = PATCH["carousel"](before)
        self.assertIn('const-string v0, "see_all_in_header"', after)
        self.assertIn("LX/06Nf;->A0I:Landroid/view/View;", after)
        self.assertIn("const/16 v1, 0x8", after)
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["carousel"](before.replace("0x7f0b3c6b", "0x123"))

    def test_narrowing_account_units_and_paths(self):
        # Actual upstream initializer register order.
        paths = [
            "/discover/ayml/", "/discover/sectioned_ayml/", "/discover/chaining/",
            "/discover/recommended_accounts_for_category/", "/discover/suggested_businesses/",
            "/discover/recs_from_friends_suggestions/", "/discover/recs_from_friends_user_info/",
            "/discover/fetch_suggestion_details/", "/discover/account_discovery/",
            "/discover/reshare_suggestions/", "/fbsearch/accounts_recs/",
            "/friendships/feed_favorites_suggestions/", "/friendships/share_to_friends_story_suggested_users/",
            "/direct_v2/search_friending_suggestions/", "/business/discovery/suggest_business/",
        ]
        source = "\n".join(f'const-string v{i}, "{path}"' for i, path in enumerate(paths)) + """
    filled-new-array/range {v0 .. v14}, [Ljava/lang/String;
    move-result-object v0
    sput-object v0, Lcom/feurstagram/extension/Block;->SUGGESTED:[Ljava/lang/String;
    const-string v5, "suggested_users"
    const-string v6, "suggested_top_accounts"
    filled-new-array/range {v1 .. v7}, [Ljava/lang/String;
    move-result-object v0
    sput-object v0, Lcom/feurstagram/extension/Block;->SUGGESTED_FEED_UNITS:[Ljava/lang/String;
    invoke-static {}, Lcom/feurstagram/extension/Config;->isSuggestedBlocked()Z
"""
        after = PATCH["block"](source)
        self.assertIn("filled-new-array/range {v0 .. v8}", after)
        self.assertIn("filled-new-array {v5, v6}", after)
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["block"](source.replace('v8, "/discover/account_discovery/"', 'v9, "/discover/account_discovery/"'))

if __name__ == "__main__":
    unittest.main()
