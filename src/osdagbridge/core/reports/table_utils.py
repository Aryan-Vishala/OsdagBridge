# =============================================================================
# Reusable LaTeX longtable skeleton builder.
# Manages ONLY the longtable skeleton:
#     \begin{longtable} / \caption / \endfirsthead /
#     repeated header / \endhead / body / \end{longtable}
# It does NOT interpret row content, row terminators, or rules.
# =============================================================================


def make_longtable(col_spec, caption, header_rows, body, *,
                   header_row_end=r" \\", repeat_header=None, pre="", post=""):
    """Build a longtable whose header repeats on continuation pages.

    Parameters
    ----------
    col_spec:
        Column specification, e.g. ``r"|L{5.5cm}|p{10.0cm}|"``.
    caption:
        Caption body (inner text), e.g. ``r"\\textbf{Dead Load -- Self Weight}"``.
    header_rows:
        List of header row strings. Each is emitted verbatim followed by
        ``header_row_end`` (without a trailing newline of its own).
    body:
        Fully rendered LaTeX for the table body. Passed through untouched.
    header_row_end:
        Terminator appended to every entry in ``header_rows``.
    repeat_header:
        Opaque string repeated at the top of every continuation page.
        Defaults to ``pre + header_rows + post``.
    pre:
        Opaque string emitted after the caption (before the header rows).
    post:
        Opaque string emitted after the header rows (before ``\\endfirsthead``).
    """
    header_block = "\n".join(h + header_row_end for h in header_rows)
    lines = [
        r"\begin{longtable}{" + col_spec + r"}",
        r"\caption{" + caption + r"}",
    ]
    if pre:
        lines.append(pre)
    lines.append(header_block)
    if post:
        lines.append(post)
    lines.append(r"\endfirsthead")
    
    if repeat_header is not False:
        if repeat_header is None or repeat_header is True:
            rh = "\n".join(part for part in (pre, header_block, post) if part)
        else:
            rh = repeat_header
        lines.append(rh)
        lines.append(r"\endhead")

    if body:
        lines.append(body)
    lines.append(r"\end{longtable}")
    return "\n".join(lines)
