import pytest
from pathlib import Path

def test_no_raw_latex_fragments_in_semantic_cells():
    ch5_path = Path("src/osdagbridge/core/report_engine/chapters/ch5_document.py")
    if not ch5_path.exists():
        return
        
    text = ch5_path.read_text(encoding="utf-8")
    assert "textsubscript" not in text, "Found legacy textsubscript"
    assert "textsuperscript" not in text, "Found legacy textsuperscript"
    assert "makecell{" not in text, "Found makecell in normal strings"
    assert r"w_{DL}" not in text, "Found raw w_{DL} without Math()"
    assert "cm^2/m" not in text, "Found raw cm^2/m without Math()"
    assert "mm^2/m" not in text, "Found raw mm^2/m without Math()"
