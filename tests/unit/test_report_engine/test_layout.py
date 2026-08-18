"""Tests for report_engine.layout — LayoutHints."""

import pytest

from osdagbridge.core.report_engine.layout import LayoutHints


class TestLayoutHints:
    def test_defaults(self):
        lh = LayoutHints()
        assert lh.keep_with_next is False
        assert lh.keep_together is False
        assert lh.keep_caption_with_table is True
        assert lh.minimum_bottom_clearance_lines == 3
        assert lh.splittable is True
        assert lh.repeat_header is True
        assert lh.space_after_mm == 4.0

    def test_frozen(self):
        lh = LayoutHints()
        with pytest.raises(AttributeError):
            lh.keep_with_next = True

    def test_custom_values(self):
        lh = LayoutHints(
            keep_with_next=True,
            minimum_bottom_clearance_lines=5,
            space_after_mm=8.0,
        )
        assert lh.keep_with_next is True
        assert lh.minimum_bottom_clearance_lines == 5
        assert lh.space_after_mm == 8.0
