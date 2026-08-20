from osdagbridge.core.reports.table_utils import make_longtable

COL_SPEC = r"|L{5.5cm}|p{10.0cm}|"
CAPTION = r"\textbf{Dead Load -- Self Weight}"
HEADER_ROW_LINE = r"\textbf{parameter} & \textbf{value} \\"
BODY = "\n".join([
    r"\textnormal{Steel Self-Weight Applied} & 76.4 kN/m\textsuperscript{3} \\[6pt]",
    r"\hline",
    r"\textnormal{Concrete Deck Weight} & 24.5 kN/m\textsuperscript{3} \\[6pt]",
    r"\hline",
    r"\textnormal{Self-Weight Factor} & 1.0 \\[6pt]",
    r"\hline",
])

LEGACY_FIRST_HEAD = "\n".join([
    r"\begin{longtable}{|L{5.5cm}|p{10.0cm}|}",
    r"\caption{\textbf{Dead Load -- Self Weight}} \\",
    r"\hline",
    r"\textbf{parameter} & \textbf{value} \\",
    r"\hline",
])


def _dead_load_table(body=BODY, **kwargs):
    return make_longtable(COL_SPEC, CAPTION, [r"\textbf{parameter} & \textbf{value}"],
                          body, pre=r"\hline", post=r"\hline", **kwargs)


def _regions(out):
    first_head = out.split(r"\endfirsthead")[0]
    repeat_head = out.split(r"\endfirsthead")[1].split(r"\endhead")[0]
    body_region = out.split(r"\endhead")[1]
    return first_head, repeat_head, body_region


def test_env_structure():
    out = _dead_load_table()
    assert out.startswith(r"\begin{longtable}{" + COL_SPEC + r"}")
    assert out.endswith(r"\end{longtable}")
    assert out.index(r"\endfirsthead") < out.index(r"\endhead")


def test_caption_once():
    out = _dead_load_table()
    first_head, _, _ = _regions(out)
    assert out.count(r"\caption{") == 1
    assert r"\caption{" + CAPTION + r"}" in first_head


def test_header_repeated_in_correct_regions():
    out = _dead_load_table()
    first_head, repeat_head, body_region = _regions(out)
    assert first_head.count(HEADER_ROW_LINE) == 1
    assert repeat_head.count(HEADER_ROW_LINE) == 1
    assert body_region.count(HEADER_ROW_LINE) == 0


def test_body_passthrough():
    out = _dead_load_table()
    _, _, body_region = _regions(out)
    assert BODY in body_region
    assert out.count(BODY) == 1


def test_legacy_first_page_byte_identical():
    out = _dead_load_table()
    first_head, _, _ = _regions(out)
    assert first_head == LEGACY_FIRST_HEAD + "\n"


def test_repeat_header_defaults_and_override():
    out = _dead_load_table()
    _, repeat_head, _ = _regions(out)
    assert repeat_head.strip("\n") == "\n".join([r"\hline", HEADER_ROW_LINE, r"\hline"])

    custom = "\n".join([r"\multicolumn{2}{c}{\textit{Custom (continued)}} \\", r"\hline", HEADER_ROW_LINE, r"\hline"])
    out2 = _dead_load_table(repeat_header=r"\multicolumn{2}{c}{\textit{Custom (continued)}} \\")
    _, repeat_head2, _ = _regions(out2)
    assert repeat_head2.strip("\n") == custom
    assert out2.count(HEADER_ROW_LINE) == 2


def test_multi_row_header():
    headers = [r"\textbf{Girder} & \textbf{Member ID}",
               r"\textbf{Design Mode} & \textbf{Girder Type}"]
    out = make_longtable(COL_SPEC, CAPTION, headers, BODY)
    first_head, repeat_head, _ = _regions(out)
    for h in headers:
        line = h + r" \\"
        assert first_head.count(line) == 1
        assert repeat_head.count(line) == 1


def test_empty_body():
    out = make_longtable(COL_SPEC, CAPTION, [r"\textbf{parameter} & \textbf{value}"], "")
    assert out.endswith(r"\end{longtable}")
    assert r"\endhead" in out
