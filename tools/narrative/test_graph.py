#!/usr/bin/env python3
"""Tests of tools/narrative/graph.py: small synthetic graphs that make each rule pass and fail, and the real data.

    python -m unittest discover -s tools/narrative -p "test_*.py"
"""
from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graph as G  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CP = G.CHECKPOINT


def node(gid, cat, **kw):
    d = {"id": gid, "title": gid, "world": kw.pop("world", "w"), "category": cat, "hub": False, "status": "existing"}
    d.update(kw)
    return d


def edge(frm, to, via=None, kind="scene", **kw):
    e = G.new_edge(frm, to, via or f"{frm}>{to}", kind, kw.pop("status", "proposed"), quest=kw.pop("quest", None))
    cond = kw.pop("cond", {})
    e["condition"].update(cond)
    e.update(kw)
    return e


def tiny(extra_edges=(), drop=(), settings=None):
    """Two locations A (hub a0, scenes a1) and B (hub b0), two quests q (scenes q1, q2, q3; q3 is the ending) and r (scene r1).
    Every hub shows both quest entrances and one exit; everything has three choices; every quest scene returns."""
    nodes = {
        "m/a0": node("m/a0", "mainline", location="A", hub=True), "m/a1": node("m/a1", "mainline", location="A", world="z"),
        "m/b0": node("m/b0", "mainline", location="B", hub=True, world="z"),
        "q/q1": node("q/q1", "quest", quest="q"), "q/q2": node("q/q2", "quest", quest="q"), "q/q3": node("q/q3", "quest", quest="q"), "r/r1": node("r/r1", "quest", quest="r"),
    }
    E = []
    for hub in ("m/a0", "m/b0"):
        E += [edge(hub, "q/q1", f"{hub}.q", "quest_entry", quest="q", rhythm_gate=False), edge(hub, "r/r1", f"{hub}.r", "quest_entry", quest="r", rhythm_gate=False)]
    E += [edge("m/a0", "m/a1", "a0.a1"), edge("m/a1", "m/b0", "a1.b0"), edge("m/a1", "m/a0", "a1.to_hub", link="to_hub"), edge("m/b0", "m/a1", "b0.a1")]
    E += [edge("q/q1", "q/q2", "q1.q2"), edge("q/q2", "q/q3", "q2.q3"), edge("q/q3", "q/q1", "q3.q1")]
    for n in ("q/q1", "q/q2", "q/q3", "r/r1"):
        E.append(edge(n, CP, n + ".return", "quest_return", quest=n.split("/")[0]))
    E += list(extra_edges)
    E = [e for e in E if e["via"] not in drop]
    locs = [{"id": "A", "title": "A", "worlds": ["w"], "hub": "m/a0"}, {"id": "B", "title": "B", "worlds": ["w"], "hub": "m/b0"}]
    quests = [{"id": "q", "title": "Q", "entry": "q/q1", "completion": ["q/q3"]}, {"id": "r", "title": "R", "entry": "r/r1", "completion": ["r/r1"]}]
    s = dict(G.DEFAULT_SETTINGS)
    s.update(settings or {})
    g = G.Graph("target", nodes, E, locs, quests, s, "m/a0")
    g.data_problems = []
    g.build_problems = []
    return g


OV6 = {"exceptions": [{"id": "ends", "rule": 6, "kind": "terminal_component", "scope": {"worlds": ["z"]}, "reason": "no ending yet", "tracked_by": "later", "report_as": "exception"}]}


def exc(rule, scope, id="x1", kind="named_exception"):
    return {"id": id, "rule": rule, "kind": kind, "scope": scope, "reason": "because", "tracked_by": "later", "report_as": "exception"}


class SyntheticRules(unittest.TestCase):
    def test_tiny_graph_baseline(self):
        g = tiny()
        for fn in (G.rule_01, G.rule_02, G.rule_03, G.rule_04):
            r = fn(g)
            self.assertEqual(r.status, "PASS", (fn.__name__, r.fail))

    # rule 1
    def test_rule1_pass_counts_choices(self):
        r = G.rule_01(tiny())
        self.assertEqual(r.data["all"], {"q": 1, "r": 1})

    def test_rule1_fail_too_far(self):
        g = tiny(drop=("m/a0.q", "m/b0.q"), extra_edges=[edge("m/a1", "q/q1", "a1.q", "quest_entry", quest="q", rhythm_gate=False)])
        self.assertEqual(G.rule_01(g).data["all"]["q"], 2)
        g2 = tiny(drop=("m/a0.q", "m/b0.q"), settings={"max_choices_to_quest": 1}, extra_edges=[edge("m/a1", "q/q1", "a1.q", "quest_entry", quest="q", rhythm_gate=False)])
        self.assertEqual(G.rule_01(g2).status, "FAIL")

    def test_rule1_fail_gated_entrance_and_exception(self):
        gated = edge("m/a0", "q/q1", "gate.q", "quest_entry", quest="q", rhythm_gate=True, cond={"outcome": "on_pass"})
        g = tiny(extra_edges=[gated])
        r = G.rule_01(g)
        self.assertEqual(r.status, "FAIL")
        self.assertTrue(any("gate.q" in f for f in r.fail))
        ov = {"exceptions": [exc(1, {"objects": ["gate.q"]})], "quests": [], "entrances": []}
        r = G.rule_01(g, ov)
        self.assertEqual(r.status, "EXCEPTION")
        self.assertEqual(r.exceptions[0]["count"], 1)

    def test_rule1_stale_exception_fails(self):
        ov = {"exceptions": [exc(1, {"objects": ["m/a0.q"]})], "quests": [], "entrances": []}
        self.assertEqual(G.rule_01(tiny(), ov).status, "FAIL")

    def test_rule1_gated_only_reachable_fails_ungated_run(self):
        g = tiny(drop=("m/a0.q", "m/b0.q"), extra_edges=[edge("m/a0", "q/q1", "gate.q", "quest_entry", quest="q", rhythm_gate=True, cond={"outcome": "on_pass"})])
        r = G.rule_01(g, {"exceptions": [exc(1, {"objects": ["gate.q"]})], "quests": [], "entrances": []})
        self.assertEqual(r.status, "FAIL")  # reachable only through the gated entrance
        self.assertIsNone(r.data["ungated"]["q"])

    def test_choice_count_ignores_hidden_miss_and_flag_locked(self):
        extra = [edge("m/a1", "m/b0", "h", hidden=True), edge("m/a1", "q/q2", "miss", cond={"outcome": "on_miss"}), edge("m/a1", "r/r1", "locked", cond={"flags_all": ["f"]})]
        g = tiny(extra_edges=extra)
        self.assertEqual(G.distinct_choices(g, "m/a1")[0], 2)  # the hub (to_hub) and b0; the hidden, miss and flag-locked options add nothing
        self.assertNotIn("q/q2", G.distinct_choices(g, "m/a1")[1])
        self.assertNotIn("r/r1", G.distinct_choices(g, "m/a1")[1])

    def test_automatic_scene_costs_nothing(self):
        g = tiny(drop=("m/a0.q",), extra_edges=[edge("m/a0", "m/a1", "auto", cond={"auto": True})])
        # the auto edge is not a choice, and a path over it costs 0
        self.assertNotIn("m/a1", [e["to"] for e in g.out["m/a0"] if g.is_choice(e) and e["via"] == "auto"])
        d = G.search(g, "m/a0")
        self.assertEqual(d["m/a1"], 0)

    def test_flag_aware_search(self):
        g = tiny(drop=("m/a0.q", "m/b0.q"), extra_edges=[
            edge("m/a0", "m/a1", "get", cond={"flags_set": ["f"]}), edge("m/a1", "q/q1", "use", "quest_entry", quest="q", rhythm_gate=False, cond={"flags_all": ["f"]})])
        self.assertEqual(G.fewest_to_quests(g, "m/a0")["q"], 2)
        self.assertIsNone(G.fewest_to_quests(g, "m/a0", flags=False)["q"])

    # rule 2
    def test_rule2_fail_cell_missing(self):
        r = G.rule_02(tiny(drop=("m/b0.r",)))
        self.assertEqual(r.status, "FAIL")
        self.assertTrue(any("B.r" in f for f in r.fail))

    def test_rule2_fail_no_mainline_exit(self):
        r = G.rule_02(tiny(drop=("b0.a1",)))
        self.assertTrue(any("no mainline exit" in f for f in r.fail))

    def test_rule2_fail_scene_too_far(self):
        self.assertEqual(G.rule_02(tiny(drop=("a1.to_hub",))).status, "PASS")  # a1 -> b0 -> quest is 2 choices
        r = G.rule_02(tiny(drop=("a1.to_hub",), settings={"max_choices_to_quest_in_location": 1}))
        self.assertEqual(r.status, "FAIL")

    # rule 3
    def test_rule3_fail_missing_return_and_fixed_landing(self):
        r = G.rule_03(tiny(drop=("q/q2.return",)))
        self.assertTrue(any("q/q2: no visible return" in f for f in r.fail))
        g = tiny(drop=("q/q2.return",), extra_edges=[edge("q/q2", "m/a0", "fixed", "quest_return", quest="q")])
        self.assertTrue(any("fixed scene" in f for f in G.rule_03(g).fail))

    def test_rule3_hidden_leave_does_not_count(self):
        g = tiny(drop=("q/q2.return",), extra_edges=[edge("q/q2", CP, "back key", "quest_return", quest="q", hidden=True)])
        self.assertEqual(G.rule_03(g).status, "FAIL")

    # rule 4
    def test_rule4_fail_unreachable_mainline(self):
        g = tiny()
        g.nodes["m/c0"] = node("m/c0", "mainline", location="B")
        self.assertEqual(G.rule_04(g).status, "FAIL")

    # rule 5
    def test_rule5_pass_fail_and_exception(self):
        self.assertEqual(G.rule_05(tiny(settings={"min_choices": 1})).status, "PASS")
        g = tiny(settings={"min_choices": 3})
        under = sorted(n for n in g.nodes if G.distinct_choices(g, n)[0] < 3)
        self.assertEqual(G.rule_05(g).status, "FAIL")
        ov = {"exceptions": [exc(5, {"quest": "q", "scenes": [n for n in under if n.startswith("q/")]})]}
        r = G.rule_05(g, ov)
        self.assertEqual(r.status, "FAIL")  # r/r1 and the mainline scenes are not excused
        self.assertTrue(all(not f.startswith("q/") for f in r.fail))
        self.assertEqual(r.exceptions[0]["count"], len([n for n in under if n.startswith("q/")]))

    def test_rule5_exception_stale_and_too_wide(self):
        g = tiny(settings={"min_choices": 3})
        counts = {n: G.distinct_choices(g, n)[0] for n in g.nodes}
        under_q = [n for n, k in counts.items() if k < 3 and n.startswith("q/")]
        wide = [n for n, k in counts.items() if k >= 3 and n.startswith("q/")]
        ov = {"exceptions": [exc(5, {"quest": "q", "scenes": under_q + ["m/a0"]})]}
        self.assertTrue(any("not a scene of quest" in f for f in G.rule_05(g, ov).fail))
        ov = {"exceptions": [exc(5, {"quest": "q", "scenes": under_q + ["q/nope"]})]}
        self.assertTrue(any("not a scene" in f for f in G.rule_05(g, ov).fail))
        if wide:
            ov = {"exceptions": [exc(5, {"quest": "q", "scenes": under_q + wide})]}
            self.assertTrue(any("too wide" in f for f in G.rule_05(g, ov).fail))

    def test_rule5_back_option_worst_case(self):
        g = tiny(settings={"min_choices": 3}, extra_edges=[edge("q/q1", "q/q2", "dup"), edge("q/q1", "m/a0", "b1", cond={"previous_scene": True}),
                                                           edge("q/q1", "q/q2", "b2", cond={"previous_scene": True})])
        n, dests = G.distinct_choices(g, "q/q1")
        self.assertEqual(n, 2)  # q2 and the checkpoint; the worst case of the back option is a predecessor that is q2 again
        g = tiny(extra_edges=[edge("q/q1", "m/a0", "b1", cond={"previous_scene": True})])
        self.assertEqual(G.distinct_choices(g, "q/q1")[0], 3)

    # rule 6
    def test_rule6_declared_terminal_and_dead_end(self):
        g = tiny()
        r = G.rule_06(g, OV6)
        self.assertEqual(r.status, "EXCEPTION", r.fail)
        g.nodes["m/dead"] = node("m/dead", "mainline", location="B", world="z")
        g.edges.append(edge("m/a1", "m/dead", "to_dead"))
        g.out["m/a1"].append(g.edges[-1])
        r = G.rule_06(g, OV6)
        self.assertTrue(any("m/dead: no visible way out" in f for f in r.fail))

    def test_rule6_unreachable_and_trapped(self):
        g = tiny()
        g.nodes["q/island"] = node("q/island", "quest", quest="q")
        r = G.rule_06(g, OV6)
        self.assertTrue(any("q/island: not reachable" in f for f in r.fail))
        g2 = tiny(drop=("q/q1.return", "q/q2.return", "q/q3.return"))
        self.assertTrue(any("cannot reach the mainline" in f for f in G.rule_06(g2, OV6).fail))

    def test_rule6_terminal_component_needs_a_declaration(self):
        r = G.rule_06(tiny())  # a1 and b0 lead only to each other and have no ending
        self.assertTrue(any("terminal component" in f for f in r.fail))
        g = tiny()
        g.nodes["m/a2"] = node("m/a2", "mainline", location="A", world="z")
        for e in (edge("m/a0", "m/a2", "a0.a2"), edge("m/a2", "m/a1", "a2.a1")):
            g.edges.append(e)
            g.out[e["from"]].append(e)
        self.assertTrue(any("too wide" in f for f in G.rule_06(g, OV6).fail))
        stale = {"exceptions": [exc(6, {"worlds": ["z", "nowhere"]}, kind="terminal_component")]}
        self.assertTrue(any("stale" in f for f in G.rule_06(tiny(), stale).fail))

    # rule 9 and 10 on the model
    def test_model_rules_pass_on_tiny(self):
        g = tiny()
        self.assertEqual(G.rule_09(g, None, None, walks=20).data["cases"], 4)
        self.assertEqual(G.rule_10(g, None, None, walks=20).status, "PASS", G.rule_10(g, None, None, walks=20).fail)

    def test_rule9_fail_without_return(self):
        g = tiny(drop=("q/q2.return",))
        self.assertEqual(G.rule_09(g, None, None, walks=5).status, "FAIL")

    def test_rule9_closed_quest_cycle(self):
        g = tiny(drop=("q/q1.return", "q/q2.return", "q/q3.return"))
        r = G.rule_09(g, None, None, walks=1)
        self.assertTrue(any("cycle that cannot be left" in f for f in r.fail))

    def test_rule10_fail_without_checkpoint(self):
        g = tiny()
        for e in g.edges:
            if e["to"] == CP:
                e["to"] = "m/a0"
        self.assertEqual(G.rule_10(g).status, "FAIL")

    def test_model_resume_and_restart(self):
        g = tiny()
        self.assertEqual(G.scripted_case(g, "q", "A"), [])
        self.assertEqual(G.scripted_case(g, "r", "B"), [])

    def test_model_closed_request_leaves_state(self):
        g = tiny()
        m = G.RouteModel(g)
        before = m.snapshot()
        rid = m.request(m.options()[0])
        m.close(rid)
        self.assertEqual(m.snapshot(), before)

    # rule 7 and 8 need the data
    def test_exception_without_tracker_fails(self):
        x = exc(5, {"quest": "q", "scenes": []})
        x["tracked_by"] = ""
        self.assertTrue(G.exception_form_errors(x))


class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = G.prepare(str(ROOT / "content"), str(ROOT / "content/narrative/graph.json"))
        cls.d = d
        cls.today, cls.target = d["today"], d["target"]
        cls.game, cls.ov = d["game"], d["overlay"]
        cls.rt = {r.rule: r for r in G.validate(cls.today, None, cls.game)}
        cls.rg = {r.rule: r for r in G.validate(cls.target, cls.ov, cls.game)}

    # today
    def test_today_counts(self):
        # sanity literals: the five locations and four quests; the rest follows the data (new entrances add edges)
        self.assertEqual((len(self.today.locations), len(self.today.quests)), (5, 4))
        ids = {n for n in self.today.nodes}
        self.assertTrue(all(e["from"] in ids and e["to"] in ids for e in self.today.edges), "every edge joins two nodes")
        self.assertGreater(len(self.today.edges), len(self.today.nodes))
        entries = [e for e in self.today.edges if e["kind"] == "quest_entry"]
        self.assertEqual(len({(e["from"], e["via"]) for e in entries}), len(entries), "one quest_entry edge per entrance object")

    def test_today_rule1_choices(self):
        d = self.rt[1].data
        self.assertEqual(set(d["all"]), {"bassment", "gospel", "squadron", "ember"})
        self.assertTrue(all(v is not None and v >= 1 for v in d["all"].values()), d["all"])
        self.assertTrue(all(d["with_hidden"][q] <= d["all"][q] for q in d["all"]))
        # today only the shortest way to each quest counts; the verdict follows the numbers (FAIL while some quest is not reachable by ungated entrances only within the limit)
        reachable = all(v is not None and v <= d["limit"] for v in d["ungated"].values())
        self.assertEqual(self.rt[1].status, "PASS" if reachable else "FAIL")

    def test_today_rule2_four_of_twenty(self):
        d = self.rt[2].data
        self.assertEqual(len(d["cells"]), len(self.today.locations) * len(self.today.quests))
        self.assertEqual(d["cells_any_scene"], sum(1 for c in d["cells"] if c[2]))
        self.assertEqual(self.rt[2].status, "PASS" if d["cells_hub_ungated"] == len(d["cells"]) else "FAIL")

    def test_today_rule3_returns_land_on_the_floor(self):
        d = self.rt[3].data
        self.assertEqual(d["fixed_landings"].keys(), {"main/warehouse"})
        self.assertEqual((d["fixed_landing_scenes"], d["without_visible_return"]), (13, 97))
        self.assertEqual(self.rt[3].status, "FAIL")

    def test_today_other_rules(self):
        self.assertEqual(self.rt[4].status, "PASS")
        self.assertEqual(self.rt[5].status, "FAIL")
        self.assertEqual(self.rt[6].status, "FAIL")  # the late loops are closed and nothing declares them
        self.assertEqual(self.rt[7].status, "PASS")
        self.assertEqual(self.rt[9].status, "FAIL")
        self.assertEqual(self.rt[10].status, "FAIL")

    def test_today_lost_fights_reach_passage_0(self):
        lost = [e for e in self.today.edges if e["condition"].get("outcome") == "fight_lost"]
        self.assertEqual(len(lost), 10)
        self.assertTrue(all(e["to"] == "bassment/0" for e in lost))

    def test_today_main_choice_histogram(self):
        h = self.rt[5].data["mainline_hist"]
        # the flag-locked ember and star do not count; every mainline scene is counted once and offers at least one choice (new entrances move scenes between buckets)
        self.assertTrue(all(k >= 1 for k in h))
        self.assertGreater(sum(h.values()), 0)
        self.assertLessEqual(max(h), 10, "the hub cap")

    # target
    def test_target_no_failures(self):
        for k, r in self.rg.items():
            self.assertNotEqual(r.status, "FAIL", (k, r.fail[:5]))

    def test_target_statuses_and_exceptions(self):
        st = {k: r.status for k, r in self.rg.items() if k}
        self.assertEqual([k for k, v in st.items() if v == "EXCEPTION"], [1, 5, 6])
        ids = sorted(x["id"] for r in self.rg.values() for x in r.exceptions)
        self.assertEqual(ids, ["bassment_passages_under_three", "late_loops_have_no_ending", "legacy_wizard_entrance"])

    def test_target_every_quest_one_ungated_choice(self):
        d = self.rg[1].data
        self.assertEqual(d["all"], {"bassment": 1, "gospel": 1, "squadron": 1, "ember": 1})
        self.assertEqual(d["ungated"], {"bassment": 1, "gospel": 1, "squadron": 1, "ember": 1})

    def test_target_twenty_cells_and_return(self):
        self.assertEqual(self.rg[2].data["cells_hub_ungated"], 20)
        self.assertEqual(self.rg[3].data["on_checkpoint"], 110)

    def test_target_twenty_new_entrances(self):
        hub_entries = [e for e in self.target.edges if e["kind"] == "quest_entry" and e.get("entrance")]
        self.assertEqual(len(hub_entries), 20)
        self.assertFalse(any(e["rhythm_gate"] for e in hub_entries))

    def test_target_seven_routes_flagged(self):
        flagged = [e for e in self.target.edges if e.get("owner_to_confirm")]
        self.assertEqual(len(flagged), 7)
        self.assertEqual(sum(1 for e in flagged if e["link"] == "restart"), 5)

    def test_target_hub_links(self):
        links = {(e["from"], e["to"]) for e in self.target.edges if e.get("link") == "hub_to_hub"}
        self.assertEqual(links, {("main/mothership", "main/underworld"), ("main/underworld", "main/mothership"), ("main/hospital", "main/ward"), ("main/ward", "main/hospital")})

    def test_target_caps(self):
        self.assertEqual(self.rg[0].status, "PASS")

    def test_not_checkable_notes(self):
        for k in (5, 8, 9, 10):
            self.assertTrue(any("not checkable from data" in n for n in self.rg[k].not_checkable), k)

    # mutations of the overlay
    def build(self, ov):
        g, problems = G.build_target(self.game, ov)
        g.build_problems = problems
        g.data_problems = []
        return g, {r.rule: r for r in G.validate(g, ov, self.game)}

    def test_dropping_the_wizard_exception_fails_rule1(self):
        ov = copy.deepcopy(self.ov)
        ov["exceptions"] = [x for x in ov["exceptions"] if x["id"] != "legacy_wizard_entrance"]
        _, r = self.build(ov)
        self.assertEqual(r[1].status, "FAIL")

    def test_stale_bassment_exception_fails(self):
        ov = copy.deepcopy(self.ov)
        x = next(x for x in ov["exceptions"] if x["id"] == "bassment_passages_under_three")
        x["scope"]["scenes"].remove("bassment/0")
        _, r = self.build(ov)
        self.assertEqual(r[5].status, "FAIL")
        x["scope"]["scenes"] += ["bassment/0", "bassment/1"]  # bassment/1 has two choices without a return... check too wide is reported when it has enough
        ov2 = copy.deepcopy(self.ov)
        x2 = next(x for x in ov2["exceptions"] if x["id"] == "bassment_passages_under_three")
        hub_like = next(n for n, k in self.rg[5].data["counts"].items() if k >= 3 and n.startswith("bassment/"))
        x2["scope"]["scenes"].append(hub_like)
        _, r2 = self.build(ov2)
        self.assertTrue(any("too wide" in f for f in r2[5].fail))

    def test_unresolved_reference_fails_rule7(self):
        ov = copy.deepcopy(self.ov)
        ov["entrances"][5]["scene"] = "main/nowhere"
        _, r = self.build(ov)
        self.assertEqual(r[7].status, "FAIL")
        ov = copy.deepcopy(self.ov)
        ov["extra_routes"][0]["scene"] = "main/nowhere"
        _, r = self.build(ov)
        self.assertEqual(r[7].status, "FAIL")

    def test_proposed_object_colliding_with_hotspot_fails_rule7(self):
        ov = copy.deepcopy(self.ov)
        ov["entrances"][4]["object"]["id"] = "warehouse.bar.ember"
        _, r = self.build(ov)
        self.assertTrue(any("collides" in f for f in r[7].fail))

    def test_gated_entrance_in_overlay_fails_rule1(self):
        ov = copy.deepcopy(self.ov)
        ov["entrances"][5]["rhythm_gate"] = True
        _, r = self.build(ov)
        self.assertEqual(r[7].status, "FAIL")

    def test_missing_entrance_cell_fails(self):
        ov = copy.deepcopy(self.ov)
        del ov["entrances"][7]
        _, r = self.build(ov)
        self.assertEqual(r[2].status, "FAIL")
        self.assertEqual(r[7].status, "FAIL")

    def test_unmarked_extra_route_fails_rule7(self):
        ov = copy.deepcopy(self.ov)
        x = next(x for x in ov["extra_routes"] if x["kind"] == "restart")
        del x["owner_to_confirm"]
        _, r = self.build(ov)
        self.assertEqual(r[7].status, "FAIL")

    def test_late_loop_exception_stale_when_no_terminal(self):
        ov = copy.deepcopy(self.ov)
        x = next(x for x in ov["exceptions"] if x["id"] == "late_loops_have_no_ending")
        x["scope"]["worlds"] = ["hospital_late", "ward_late", "hospital"]
        _, r = self.build(ov)
        self.assertEqual(r[6].status, "FAIL")

    def test_strict_turns_exceptions_into_failures(self):
        res = G.validate(self.target, self.ov, self.game, strict=True)
        self.assertTrue(any(r.status == "FAIL" for r in res))

    # exports and command line
    def test_export_is_deterministic_and_sorted(self):
        a = G.dumps(G.export_graph(self.target, "x"))
        b = G.dumps(G.export_graph(G.prepare(str(ROOT / "content"), str(ROOT / "content/narrative/graph.json"))["target"], "x"))
        self.assertEqual(a, b)
        self.assertNotIn("\r", a)
        data = json.loads(a)
        ids = [n["id"] for n in data["nodes"]]
        self.assertEqual(ids, sorted(ids))

    def test_mermaid_mentions_every_location_and_quest(self):
        m = G.mermaid(self.target)
        for l in self.target.locations:
            self.assertIn(l["title"], m)
        self.assertIn("The Bassment", m)

    def test_cli_exit_codes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(G.main(["--content", str(ROOT / "content"), "--overlay", str(ROOT / "content/narrative/graph.json")]), 0)
            self.assertEqual(G.main(["--content", str(ROOT / "content"), "--graph", "today"]), 1)
            self.assertEqual(G.main(["--content", str(ROOT / "content"), "--overlay", str(ROOT / "content/narrative/graph.json"), "--strict"]), 1)
        self.assertIn("EXCEPTION", out.getvalue())
        self.assertIn("SUMMARY", out.getvalue())

    def test_cli_unknown_format_is_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "o.json"
            p.write_text(json.dumps({"format": "other"}), encoding="utf-8")
            err = io.StringIO()
            from contextlib import redirect_stderr
            with redirect_stderr(err):
                self.assertEqual(G.main(["--content", str(ROOT / "content"), "--overlay", str(p)]), 2)

    def test_committed_exports_match_the_tool(self):
        out = ROOT / "docs/parallel-development/graph"
        if not (out / "narrative_graph.json").exists():
            self.skipTest("exports not written yet")
        want = G.dumps(G.export_graph(self.target, "content/narrative/graph.json"))
        self.assertEqual((out / "narrative_graph.json").read_bytes().decode("utf-8"), want)
        self.assertEqual((out / "narrative_graph.mmd").read_bytes().decode("utf-8"), G.mermaid(self.target))
        self.assertEqual((out / "graph_today.json").read_bytes().decode("utf-8"), G.dumps(G.export_graph(self.today)))


if __name__ == "__main__":
    unittest.main()


class N22Tools(unittest.TestCase):
    """Work package N2.2: the cap of 8 choices (hubs up to 10, ruling 16) and the hub's Bassment route "bassment" (ruling 15)."""

    def _hub_graph(self, k):
        nodes = {"main/h": node("main/h", "mainline", location="A", hub=True), "main/x": node("main/x", "mainline", location="A")}
        E = [edge("main/h", "main/x", f"h.o{i}") for i in range(k)]
        g = G.Graph("target", nodes, E, [{"id": "A", "title": "A", "worlds": ["w"], "hub": "main/h"}], [], dict(G.DEFAULT_SETTINGS), "main/h")
        g.data_problems, g.build_problems = [], []
        return g

    def test_the_cap_is_eight_and_a_hub_needs_an_override_only_above_it(self):
        class FakeGame:
            main = {"h": {}, "x": {}}
        r8 = G.check_cap(self._hub_graph(8), None, FakeGame)
        self.assertEqual(r8.data["cap"], 8)
        self.assertEqual(r8.data["need_override"], [], "eight choices fit the default cap of a node without max_hotspots")
        r9 = G.check_cap(self._hub_graph(9), None, FakeGame)
        self.assertEqual(r9.data["need_override"], [("main/h", 9, 8)])
        self.assertEqual(r9.fail, [], "a hub may hold up to 10")
        r11 = G.check_cap(self._hub_graph(11), None, FakeGame)
        self.assertTrue(r11.fail)

    def test_the_bassment_route_is_an_ungated_hub_entrance_not_the_wizard(self):
        game = G.Game(str(ROOT / "content"))
        t = G._resolve_route(game, "bassment", None)
        self.assertEqual(t, (game.entry_of("bassment"), "quest_entry", "bassment"))
        self.assertIsNone(G._resolve_route(game, "trial:1", None))
        # a hotspot row with the route on the Floor (a trial_gate scene) is not marked legacy; the wizard's passage number still is
        h = {"id": "warehouse.enter_bassment", "scene": "warehouse", "kind": "secret", "on_success": {"route": "bassment"}, "on_failure": {"energy": -4}}
        game.hotspots["main/warehouse"].append(h)
        edges = G._scene_edges(game, "main/warehouse", None, game.main, "main/")
        hatch = [e for e in edges if e["via"] == "warehouse.enter_bassment" and e["kind"] == "quest_entry"]
        wiz = [e for e in edges if e["via"] == "warehouse.wizard" and e["kind"] == "quest_entry"]
        self.assertTrue(hatch and not any(e.get("legacy") for e in hatch))
        self.assertTrue(wiz and all(e.get("legacy") for e in wiz))
