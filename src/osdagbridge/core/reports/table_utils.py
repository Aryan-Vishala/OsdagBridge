# =============================================================================
# Reusable LaTeX longtable skeleton builder.
# Manages ONLY the longtable skeleton:
#     \begin{longtable} / \caption / \endfirsthead /
#     repeated header / \endhead / body / \end{longtable}
# It does NOT interpret row content, row terminators, or rules.
# =============================================================================


def make_longtable(col_spec, caption=None, header_rows=None, body="", *,
                   num_cols=None, header_row_end=r" \\", repeat_header=None, pre="", post="", **kwargs):
    """Build a longtable whose header repeats on continuation pages.

    Supports:
    - make_longtable(col_spec, caption, header_rows, body, ...)
    - make_longtable(col_spec, num_cols, caption, header_rows, body, ...)
    - make_longtable(col_spec=..., num_cols=..., caption=..., header_rows=..., body=...)
    """
    if isinstance(caption, int):
        num_cols = caption
        caption = header_rows
        header_rows = body
        body = kwargs.get("body", "")

    if caption is None and "caption" in kwargs:
        caption = kwargs["caption"]
    if header_rows is None and "header_rows" in kwargs:
        header_rows = kwargs["header_rows"]
    if not body and "body" in kwargs:
        body = kwargs["body"]
    if num_cols is None and "num_cols" in kwargs:
        num_cols = kwargs["num_cols"]

    if num_cols is None:
        if header_rows and len(header_rows) > 0:
            num_cols = header_rows[0].count("&") + 1
        else:
            num_cols = 2

    header_rows = header_rows or []
    caption = caption or ""

    header_block = "\n".join(h + header_row_end for h in header_rows)
    lines = [
        r"\begin{longtable}{" + col_spec + r"}",
        r"\caption{" + caption + r"} \\",
    ]
    if pre:
        lines.append(pre)
    lines.append(header_block)
    if post:
        lines.append(post)
    lines.append(r"\endfirsthead")
    
    if repeat_header is not False:
        if repeat_header is None or repeat_header is True:
            rh_parts = [p for p in (pre, header_block, post) if p]
            lines.append("\n".join(rh_parts))
        else:
            cont = str(repeat_header).strip()
            if cont:
                if not cont.endswith(r"\\") and r"\multicolumn" in cont:
                    cont += r" \\"
                lines.append(cont)
            if pre:
                lines.append(pre)
            lines.append(header_block)
            if post:
                lines.append(post)
        lines.append(r"\endhead")
        
    lines.append(r"\hline")
    lines.append(r"\endfoot")
    
    lines.append(r"\hline")
    lines.append(r"\endlastfoot")

    if body:
        lines.append(body)
    lines.append(r"\end{longtable}")
    return "\n".join(lines)
