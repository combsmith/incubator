"""
Static checks on dashboard.tmpl.html's filter/sort tooltips (issue #185).

Every filter option, the MobileAction toggle and each sort option must point at an
explanation the tooltip shows on hover/focus/long-press and screen readers announce via
aria-describedby. The copy lives once, in the hidden #tips block; these tests make sure no
control is left unexplained and no reference dangles.

    cd pocs/demand-radar && python -m pytest tests/ -q
"""

import os
from html.parser import HTMLParser

import pytest

TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard.tmpl.html")


class _Scan(HTMLParser):
    """Collect the filter controls (with the group they sit in) and the #tips spans' text."""

    def __init__(self):
        super().__init__()
        self.stack = []  # (tag, attrs) of open non-void elements
        self.controls = []  # (group id, tag, attrs, label)
        self.tips = {}  # tip id -> text
        self.tip_ids = []
        self._tip = None
        self._ctrl = None

    def _group(self):
        for _tag, a in reversed(self.stack):
            if "seg" in (a.get("class") or "").split():
                return a.get("id")
        return None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        inside_tips = any(x.get("id") == "tips" for _t, x in self.stack)
        if inside_tips and tag == "span" and a.get("id"):
            self._tip = a["id"]
            self.tip_ids.append(a["id"])
            self.tips[a["id"]] = ""
        group = self._group()
        if (tag == "button" and group) or (tag == "button" and a.get("id") == "tMA"):
            self._ctrl = [group or "tMA", tag, a, ""]
        elif tag == "select" and a.get("id") == "sort":
            self.controls.append(["sort", tag, a, ""])
        elif tag == "option" and any(x.get("id") == "sort" for _t, x in self.stack):
            self._ctrl = ["sort-option", tag, a, ""]
        self.stack.append((tag, a))

    def handle_endtag(self, tag):
        if tag == "span" and self._tip:
            self._tip = None
        if tag in ("button", "option") and self._ctrl:
            self.controls.append(self._ctrl)
            self._ctrl = None
        while self.stack:
            t, _a = self.stack.pop()
            if t == tag:
                break

    def handle_data(self, data):
        if self._tip:
            self.tips[self._tip] += data
        if self._ctrl:
            self._ctrl[3] += data


@pytest.fixture(scope="module")
def scan():
    p = _Scan()
    with open(TEMPLATE, encoding="utf-8") as f:
        p.feed(f.read())
    return p


def _tip_ref(ctrl):
    group, _tag, a, _label = ctrl
    return a.get("data-tip") if group == "sort-option" else a.get("aria-describedby")


class TestFilterTooltips:
    def test_every_control_group_is_present(self, scan):
        groups = {c[0] for c in scan.controls}
        assert {"ch", "gap", "lens", "rate", "tMA", "sort", "sort-option"} <= groups

    def test_tips_are_unique_and_non_empty(self, scan):
        assert scan.tip_ids, "no #tips block found"
        assert len(scan.tip_ids) == len(set(scan.tip_ids))
        for tid, text in scan.tips.items():
            assert text.strip(), f"tip {tid} is empty"

    def test_every_filter_and_sort_option_references_a_tip(self, scan):
        for ctrl in scan.controls:
            if ctrl[0] == "sort":
                continue  # the <select> itself follows the selected option at runtime
            ref = _tip_ref(ctrl)
            assert ref, f"{ctrl[0]} control {ctrl[3]!r} has no tooltip"
            assert ref in scan.tips, f"{ctrl[0]} control {ctrl[3]!r} points at missing tip {ref!r}"

    def test_sort_select_is_described_by_the_default_option(self, scan):
        select = next(c for c in scan.controls if c[0] == "sort")
        first = next(c for c in scan.controls if c[0] == "sort-option")
        assert select[2].get("aria-describedby") == first[2].get("data-tip")

    @pytest.mark.parametrize(
        "group,label,needle",
        [
            ("ch", "App Store", "App Store search volume"),
            ("ch", "Community", "keyword volume is near zero"),
            ("gap", "Any gap", "low-quality"),
            ("gap", "Emerging", "nascent"),
            ("gap", "Aging", "stale"),
            ("gap", "Weak", "thin"),
            ("gap", "Unmatched", "absent-in-store"),
            ("tMA", "Needs MobileAction", "MobileAction search-volume label"),
            ("lens", "🎯 Disrupt", "1–3★ reviews"),
            ("rate", "Unrated", "stored in this browser"),
            ("sort-option", "Sort: Signal score", "MobileAction volume"),
            ("sort-option", "Sort: Community", "directional"),
        ],
    )
    def test_copy_explains_the_control(self, scan, group, label, needle):
        ctrl = next(c for c in scan.controls if c[0] == group and c[3].replace("\xa0", " ").strip() == label)
        assert needle in scan.tips[_tip_ref(ctrl)]
