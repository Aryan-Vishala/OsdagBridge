from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_WC_LD_LANE_TABLE_COUNT,
)


def _table_block(tex, caption):
    cap = tex.index(r"\caption{" + caption + r"}")
    start = tex.rindex(r"\begin{longtable", 0, cap)
    end = tex.index(r"\end{longtable}", cap)
    return tex[start:end]


class TestLiveLoadsTable:
    def _realistic_inputs(self):
        return {
            KEY_SPAN: 30.0,
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_IRC_70R_WHEELED: True,
            KEY_WC_LD_LANE_TABLE_COUNT: 2,
            KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
        }

    def test_ll_table_renders_vehicle_and_impact_rows(self):
        block = _table_block(ch3_loads(self._realistic_inputs()),
                             r"\textbf{Live Loads (LL)}")
        assert r"\textnormal{Vehicles Considered} & Class A, Class 70R (Wheeled)" in block
        assert r"\textnormal{Impact Factor (IRC 6)} & Class A:\allowbreak{} 1.207" in block

    def test_ll_table_renders_braking_and_footpath_values(self):
        block = _table_block(ch3_loads(self._realistic_inputs()),
                             r"\textbf{Live Loads (LL)}")
        assert r"\textnormal{Braking Load (IRC 6)} & 163.04 kN (16.62 tonnes)" in block
        assert (r"\textnormal{Footpath Live Load (if applicable)} & "
                r"4.905 kN/m\textsuperscript{2} (IRC 6 Cl. 206.1)") in block

    def test_ll_table_uses_continuation_header(self):
        block = _table_block(ch3_loads(self._realistic_inputs()),
                             r"\textbf{Live Loads (LL)}")
        assert r"\endfirsthead" in block
        assert r"\endhead" in block

    def test_ll_table_no_vehicles_shows_none(self):
        block = _table_block(ch3_loads({KEY_SPAN: 30.0}),
                             r"\textbf{Live Loads (LL)}")
        assert r"\textnormal{Vehicles Considered} & None" in block
