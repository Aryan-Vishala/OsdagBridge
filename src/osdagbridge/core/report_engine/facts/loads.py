# =============================================================================
# Load fact builders — extract/compute engineering data from input_dict.
#
# Rules:
#   - Fact builders may call IRC6 calculation functions.
#   - Document builders may NOT.
#   - None means "data unavailable". 0.0 means "genuinely zero".
#   - Normalize heterogeneous UI payloads here, not in document builders.
# =============================================================================

from typing import Optional

from . import (
    DeadLoadFact,
    FootwayLoadFact,
    LiveLoadFact,
    LoadCombinationFact,
    LoadFacts,
    QuantityValue,
    SeismicLoadFact,
    SurfacingLoadFact,
    TemperatureLoadFact,
    VehicleLiveLoadFact,
    WindLoadFact,
)


def _qv(value, unit: str = "") -> QuantityValue:
    """Create a QuantityValue, treating empty/None as unavailable."""
    if value in (None, ""):
        return QuantityValue(None, unit)
    try:
        return QuantityValue(float(value), unit)
    except (TypeError, ValueError):
        return QuantityValue(None, unit)


def build_dead_load_facts(input_dict: dict) -> DeadLoadFact:
    """Table 3.1 — pure read from input_dict, no calculations."""
    return DeadLoadFact(
        steel_density=_qv(input_dict.get("material.girder.density"), "kN/m³"),
        concrete_density=_qv(input_dict.get("material.deck.density"), "kN/m³"),
        self_weight_factor=_qv(input_dict.get("loading.permanent_load.dead_load.self_weight_factor")),
    )


def build_surfacing_load_facts(input_dict: dict) -> SurfacingLoadFact:
    """Table 3.2 — pure read from input_dict, no calculations."""
    return SurfacingLoadFact(
        wearing_course_material=str(input_dict.get("typical_section.wearing_course.material") or ""),
        wearing_course_thickness=_qv(input_dict.get("typical_section.wearing_course.thickness"), "mm"),
        crash_barrier_load=_qv(input_dict.get("typical_section.crash_barrier.load"), "kN/m"),
        railing_load=_qv(input_dict.get("typical_section.railing.load_value"), "kN/m"),
    )


def build_live_load_facts(input_dict: dict) -> LiveLoadFact:
    """Table 3.3 — reads vehicle selection flags, calls IRC6 for computed values.

    Existing functions called:
        IRC6_2017.cl_208_2_impact_factor(span)   → Class A impact (IM)
        IRC6_2017.cl_208_3_impact_factor(span)   → 70R/AA/Bogie impact (IM)
        IRC6_2017.cl_211_2_braking_force(lanes)  → braking force (tonnes)
        IRC6_2017.cl_206_1_footway_load()        → footway pressure (kN/m²)
    """
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    from osdagbridge.core.utils.common import (
        KEY_LL_CUSTOM_VEHICLES,
        KEY_LL_FOOTPATH_PRESSURE_MODE,
        KEY_LL_FOOTPATH_PRESSURE_VALUE,
        KEY_LL_IRC_70R_BOGIE,
        KEY_LL_IRC_70R_TRACKED,
        KEY_LL_IRC_70R_WHEELED,
        KEY_LL_IRC_AA_TRACKED,
        KEY_LL_IRC_AA_WHEELED,
        KEY_LL_IRC_CLASS_A,
        KEY_LL_IRC_CLASS_FATIGUE,
        KEY_LL_IRC_CLASS_SV,
        KEY_SPAN,
        KEY_WC_LD_LANE_TABLE_COUNT,
    )

    # --- Determine selected vehicles ---
    vehicle_flags = [
        (KEY_LL_IRC_CLASS_A, "Class A"),
        (KEY_LL_IRC_70R_WHEELED, "Class 70R (Wheeled)"),
        (KEY_LL_IRC_70R_TRACKED, "Class 70R (Tracked)"),
        (KEY_LL_IRC_AA_WHEELED, "Class AA (Wheeled)"),
        (KEY_LL_IRC_AA_TRACKED, "Class AA (Tracked)"),
        (KEY_LL_IRC_CLASS_SV, "Class SV"),
        (KEY_LL_IRC_70R_BOGIE, "Class 70R (Bogie)"),
        (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue"),
    ]

    selected = []
    for key, name in vehicle_flags:
        if input_dict.get(key):
            selected.append(name)

    # Normalize custom vehicles (heterogeneous UI payload)
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get("name"):
                selected.append(c["name"])
            elif isinstance(c, str):
                selected.append(c)

    # --- Compute impact factors per vehicle group ---
    span = input_dict.get(KEY_SPAN)
    im_class_a = None
    im_heavy = None
    if span not in (None, ""):
        try:
            span_m = float(span)
            if input_dict.get(KEY_LL_IRC_CLASS_A):
                im_class_a = round(1.0 + IRC6_2017.cl_208_2_impact_factor(span_m), 3)
            is_heavy = (
                input_dict.get(KEY_LL_IRC_70R_WHEELED)
                or input_dict.get(KEY_LL_IRC_AA_WHEELED)
                or input_dict.get(KEY_LL_IRC_70R_BOGIE)
                or input_dict.get(KEY_LL_IRC_70R_TRACKED)
                or input_dict.get(KEY_LL_IRC_AA_TRACKED)
            )
            if is_heavy:
                im_heavy = round(1.0 + IRC6_2017.cl_208_3_impact_factor(span_m), 3)
        except Exception:
            pass

    # Map vehicle names to their impact factor group
    _HEAVY_NAMES = {
        "Class 70R (Wheeled)", "Class 70R (Tracked)",
        "Class AA (Wheeled)", "Class AA (Tracked)",
        "Class 70R (Bogie)",
    }

    vehicles = []
    for name in selected:
        if name == "Class A":
            im = QuantityValue(im_class_a, "") if im_class_a is not None else None
        elif name in _HEAVY_NAMES:
            im = QuantityValue(im_heavy, "") if im_heavy is not None else None
        else:
            im = None
        vehicles.append(VehicleLiveLoadFact(vehicle_class=name, impact_factor=im))

    # --- Braking force (shared across all vehicles) ---
    braking_force = None
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_kN = round(braking_t * 9.81, 2)
            braking_force = QuantityValue(braking_kN, "kN")
        except Exception:
            pass

    # --- Footway load ---
    footway_load = None
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_kN = IRC6_2017.cl_206_1_footway_load()
            footway_load = FootwayLoadFact(
                load_type="IRC 6 Cl. 206.1",
                intensity=QuantityValue(fp_kN, "kN/m²"),
            )
        except Exception:
            pass
    elif fp_value not in (None, ""):
        footway_load = FootwayLoadFact(
            load_type="User-defined",
            intensity=_qv(fp_value, "kN/m²"),
        )

    return LiveLoadFact(
        vehicles=tuple(vehicles),
        braking_force=braking_force,
        footway_load=footway_load,
    )


def build_wind_load_facts(input_dict: dict) -> WindLoadFact:
    """Table 3.4 — reads pre-computed keys; falls back to IRC6 Table 12."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    vz_val = input_dict.get("loading.wind_load.computed.hourly_mean_wind")
    pz_val = input_dict.get("loading.wind_load.computed.hourly_wind_pressure")

    if not vz_val or not pz_val:
        try:
            _vb = input_dict.get("loading.wind_load.basic_wind_speed") or input_dict.get("wind_speed")
            _h = input_dict.get("loading.wind_load.avg_exposed_height")
            _ter_map = {"Plain Terrain": "plain", "Terrain with Obstructions": "obstructed"}
            _ter = _ter_map.get(str(input_dict.get("loading.wind_load.terrain_type", "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass

    return WindLoadFact(
        basic_wind_speed=_qv(input_dict.get("loading.wind_load.basic_wind_speed") or input_dict.get("wind_speed"), "m/s"),
        terrain_type=str(input_dict.get("loading.wind_load.terrain_type") or ""),
        avg_exposed_height=_qv(input_dict.get("loading.wind_load.avg_exposed_height"), "m"),
        hourly_mean_wind_speed=_qv(vz_val, "m/s"),
        hourly_wind_pressure=_qv(pz_val, "N/m²"),
        transverse_wind_force=_qv(input_dict.get("loading.wind_load.computed.transverse_wind_force"), "kN"),
        longitudinal_wind_force=_qv(input_dict.get("loading.wind_load.computed.longitudinal_wind_force"), "kN"),
        vertical_wind_force=_qv(input_dict.get("loading.wind_load.computed.vertical_wind_force"), "kN"),
    )


def build_seismic_load_facts(input_dict: dict) -> SeismicLoadFact:
    """Table 3.5 — reads pre-computed keys; falls back to IRC6 Cl. 218.5.1."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    sl_zone_factor = input_dict.get("loading.seismic_load.computed.zone_factor")
    sl_spectral = input_dict.get("loading.seismic_load.computed.spectral_coeff")
    sl_ah = input_dict.get("loading.seismic_load.computed.horizontal_coeff")
    sl_av = input_dict.get("loading.seismic_load.computed.vertical_coeff")

    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get("loading.seismic_load.seismic_zone") or input_dict.get("seismic_zone")
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st = _smap.get(str(input_dict.get("loading.seismic_load.soil_type", "")), 1)
            _tp = input_dict.get("loading.seismic_load.time_period")
            _damp = input_dict.get("loading.seismic_load.damping") or "5"
            _dl_v = input_dict.get("loading.seismic_load.dead_load.value")
            _ll_v = input_dict.get("loading.seismic_load.live_load.value")
            _dead = float(_dl_v) if str(input_dict.get("loading.seismic_load.dead_load.mode", "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get("loading.seismic_load.live_load.mode", "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(
                zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                live_load_kN=_live, period_T=float(_tp) if _tp else None,
                damping_percent=float(_damp),
            )
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah = _res.get("Ah")
            if not sl_av:
                sl_av = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    return SeismicLoadFact(
        seismic_zone=str(input_dict.get("seismic_zone") or ""),
        zone_factor=_qv(sl_zone_factor),
        importance_factor=_qv(input_dict.get("loading.seismic_load.importance_factor")),
        soil_type=str(input_dict.get("loading.seismic_load.soil_type") or ""),
        spectral_coeff=_qv(sl_spectral),
        horizontal_coeff=_qv(sl_ah),
        vertical_coeff=_qv(sl_av),
    )


def build_temperature_load_facts(input_dict: dict) -> TemperatureLoadFact:
    """Table 3.6 — reads pre-computed keys; falls back to IRC6 Cl. 215.2."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    bt_min = input_dict.get("loading.temperature_load.computed.bridge_temp_min")
    bt_max = input_dict.get("loading.temperature_load.computed.bridge_temp_max")
    tl_rise = input_dict.get("loading.temperature_load.computed.temp_rise")
    tl_fall = input_dict.get("loading.temperature_load.computed.temp_fall")

    if bt_min is None or bt_max is None:
        try:
            _tmax = input_dict.get("loading.temperature_load.highest_max_temp") or input_dict.get("shade_temp_max")
            _tmin = input_dict.get("loading.temperature_load.lowest_min_temp") or input_dict.get("shade_temp_min")
            if _tmax and _tmin:
                _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                    float(_tmax), float(_tmin), "metallic", False,
                )
                bt_min = _res.get("T_min", 0)
                bt_max = _res.get("T_max", 0)
                _mean = (bt_max + bt_min) / 2.0
                if tl_rise is None:
                    tl_rise = bt_max - _mean
                if tl_fall is None:
                    tl_fall = _mean - bt_min
        except Exception:
            pass

    return TemperatureLoadFact(
        max_shade_temp=_qv(input_dict.get("shade_temp_max"), "°C"),
        min_shade_temp=_qv(input_dict.get("shade_temp_min"), "°C"),
        bridge_temp_min=_qv(bt_min, "°C"),
        bridge_temp_max=_qv(bt_max, "°C"),
        temp_rise=_qv(tl_rise, "°C"),
        temp_fall=_qv(tl_fall, "°C"),
    )


def build_load_combination_facts() -> tuple[LoadCombinationFact, ...]:
    """Table 3.7 — entirely code-derived from IRC6 Tables B.2 and B.3."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    _LABEL_MAP = {
        "dead_load": "DL",
        "surfacing": "SIDL",
        "live_load": "LL",
        "wind_load": "WL",
        "thermal_load": "TL",
        "vehicle_collision": "VC",
        "barge_impact": "BI",
        "floating_bodies": "FB",
        "seismic": "EQ",
    }

    combos = []
    for i, combo in enumerate(IRC6_2017.uls_load_combinations(), start=1):
        factors = []
        for load, val in combo["factors"].items():
            label = _LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get("adding")
                rel = val.get("relieving")
                factors.append((label, add, rel))
            else:
                factors.append((label, val, None))
        combos.append(LoadCombinationFact(
            combination_id=f"ULS-{i:02d}",
            load_cases=tuple(f[0] for f in factors if f[1] is not None),
            factors=tuple(factors),
        ))

    for i, combo in enumerate(IRC6_2017.sls_load_combinations(), start=1):
        factors = []
        for load, val in combo["factors"].items():
            label = _LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get("adding")
                rel = val.get("relieving")
                factors.append((label, add, rel))
            else:
                factors.append((label, val, None))
        combos.append(LoadCombinationFact(
            combination_id=f"SLS-{i:02d}",
            load_cases=tuple(f[0] for f in factors if f[1] is not None),
            factors=tuple(factors),
        ))

    return tuple(combos)


def build_load_facts(input_dict: dict) -> LoadFacts:
    """Top-level builder — calls all sub-builders."""
    return LoadFacts(
        dead_load=build_dead_load_facts(input_dict),
        surfacing_load=build_surfacing_load_facts(input_dict),
        live_load=build_live_load_facts(input_dict),
        wind_load=build_wind_load_facts(input_dict),
        seismic_load=build_seismic_load_facts(input_dict),
        temperature_load=build_temperature_load_facts(input_dict),
        load_combinations=build_load_combination_facts(),
    )
