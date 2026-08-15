from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

# Class A train and Class 70R wheeled totals in tonnes (from vehicle data).
CLASS_A_T = 55.4
CLASS_70R_T = 100.0


class TestCl2112BrakingForce:
    def test_single_lane_bridge(self):
        # 20% first train + 10% succeeding train in the same lane
        assert IRC6_2017.cl_211_2_braking_force(1) == round(0.30 * CLASS_A_T, 3)

    def test_two_lane_bridge(self):
        assert IRC6_2017.cl_211_2_braking_force(2) == round(0.30 * CLASS_A_T, 3)

    def test_three_lane_bridge(self):
        expected = round(0.30 * CLASS_A_T + 0.05 * CLASS_70R_T, 3)
        assert IRC6_2017.cl_211_2_braking_force(3) == expected

    def test_four_lane_bridge(self):
        expected = round(0.30 * CLASS_A_T + 0.05 * CLASS_70R_T * 2, 3)
        assert IRC6_2017.cl_211_2_braking_force(4) == expected

    def test_missing_or_zero_lanes(self):
        assert IRC6_2017.cl_211_2_braking_force(0) == 0.0
        assert IRC6_2017.cl_211_2_braking_force(None) == 0.0
        assert IRC6_2017.cl_211_2_braking_force("") == 0.0


class TestCl2061FootwayLoad:
    def test_returns_irc6_footway_pressure(self):
        value = IRC6_2017.cl_206_1_footway_load()
        assert value == 4.905
