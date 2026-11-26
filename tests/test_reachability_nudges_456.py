import runpy
import tempfile
import unittest
from pathlib import Path

PATCH = runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools/patch-notification-nudges.py"))
SURFACE = """const-string v0, "RESHARE_REEL_PROMO_DIALOG"
const-string v0, "STORY_REPLY_PROMO_DIALOG"
const-string v0, "DIRECT_THREAD_BANNER"
const-string v0, "COMMENT_POSTED"
.method public static final A00(LX/02mo;Lcom/instagram/common/session/UserSession;LX/05xR;)Z
    .locals 5
    invoke-virtual {p2}, Ljava/lang/Enum;->ordinal()I
    invoke-interface {v3, p0, v0, v1}, Lcom/facebook/mobileconfig/factory/MobileConfigUnsafeContext;->Be6(LX/02mo;J)Z
    .packed-switch 0x0
    .end packed-switch
    return v0
.end method
.method public final A01(Lcom/instagram/common/session/UserSession;)Z
    .locals 3
    invoke-virtual {p0}, Ljava/lang/Enum;->ordinal()I
    invoke-interface {v2, v0, v1}, Lcom/facebook/mobileconfig/factory/MobileConfigUnsafeContext;->Bdz(J)Z
    .packed-switch 0x0
    .end packed-switch
    return v0
.end method
.method public final A02(Lcom/instagram/common/session/UserSession;)Z
    .locals 1
    invoke-static {v0, p1, p0}, LX/05xR;->A00(LX/02mo;Lcom/instagram/common/session/UserSession;LX/05xR;)Z
    move-result v0
    return v0
.end method
"""

class ReachabilityTests(unittest.TestCase):
    def test_disables_both_config_paths_and_keeps_delegate(self):
        result = PATCH["suppress_456_reachability_surfaces"](SURFACE)
        self.assertEqual(result.count("const/4 v0, 0x0"), 2)
        self.assertNotIn("->Be6(", result)
        self.assertNotIn("->Bdz(", result)
        self.assertIn(SURFACE[SURFACE.index(".method public final A02"):], result)

    def test_rejects_changed_surface_or_gate(self):
        for a, b in [("RESHARE_REEL_PROMO_DIALOG", "OTHER"), ("->Be6(", "->changed(")]:
            with self.assertRaises(PATCH["PatchMismatch"]):
                PATCH["suppress_456_reachability_surfaces"](SURFACE.replace(a, b))

    def test_native_eligibility_only_no_permission_or_send_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            x = root / "smali/X"
            x.mkdir(parents=True)
            (x / "05xR.smali").write_text(SURFACE)
            preserved = ".method public final Other()V\n    .locals 0\n    return-void\n.end method\n"
            for name, marker in [
                ("0D77", "V2_REACHABILITY_UPSELL_IMPRESSION_COUNTER"),
                ("0E9G", "V2_REACHABILITY_UPSELL_GLOBAL_SHARED_DISMISS_COOLDOWN"),
                ("0I27", "LX/05xR;->A02(Lcom/instagram/common/session/UserSession;)Z"),
            ]:
                source = ".implements LX/0avn;\n" + marker + "\n"
                for sig in ["B2x()Z", "B2y()Z"]:
                    source += f".method public final {sig}\n    .locals 2\n    invoke-virtual {{v0, v1}}, LX/05xR;->A01(Lcom/instagram/common/session/UserSession;)Z\n    invoke-virtual {{v0, v1}}, LX/03fh;->A01(Landroid/content/Context;)Z\n    return v0\n.end method\n"
                (x / (name + ".smali")).write_text(source + preserved)
            updates = PATCH["additional_456_reachability_updates"](root)
            self.assertEqual(len(updates), 4)
            for path, result in updates.items():
                if path.name != "05xR.smali":
                    self.assertEqual(result.count("const/4 v0, 0x0"), 2)
                    self.assertTrue(result.endswith(preserved))
            self.assertEqual((x / "05xR.smali").read_text(), SURFACE)
            (x / "0I27.smali").write_text("unexpected")
            with self.assertRaises(PATCH["PatchMismatch"]):
                PATCH["additional_456_reachability_updates"](root)

if __name__ == "__main__":
    unittest.main()
