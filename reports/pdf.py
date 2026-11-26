"""PDF export using ReportLab (free, open source)."""
from io import BytesIO
from xml.sax.saxutils import escape

from core.utils import format_money


def _safe(text):
    """The built-in PDF fonts only cover Latin-1; replace anything else."""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def build_monthly_pdf(summary, farm_name, currency, insight_lines):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    s = summary
    cur = _safe(currency)
    fm = lambda v: _safe(format_money(cur, v))  # noqa: E731

    dark, light = colors.HexColor("#1b5e20"), colors.HexColor("#c8e6c9")
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Monthly report {s['label']}", author=_safe(farm_name),
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=dark, fontSize=20, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=dark, spaceBefore=12, spaceAfter=4)
    body = styles["BodyText"]

    def table(rows, widths, header=True, align_right_from=1):
        t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
        style = [
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
            ("ALIGN", (align_right_from, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        if header:
            style += [
                ("BACKGROUND", (0, 0), (-1, 0), light),
                ("TEXTCOLOR", (0, 0), (-1, 0), dark),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        t.setStyle(TableStyle(style))
        return t

    story = [
        Paragraph(escape(_safe(farm_name)), h1),
        Paragraph(f"Monthly profit &amp; loss report - {escape(s['label'])}", body),
        Spacer(1, 8),
    ]

    verdict = {"profit": "PROFIT", "loss": "LOSS", "even": "BREAK-EVEN", "empty": "NO DATA"}[s["status"]]
    verdict_color = {"profit": "#2e7d32", "loss": "#c62828"}.get(s["status"], "#555555")
    story.append(
        Paragraph(
            f'<font color="{verdict_color}" size="15"><b>{verdict}: {escape(fm(s["net_abs"]))}</b></font>',
            body,
        )
    )

    story.append(Paragraph("Summary", h2))
    summary_rows = [
        ["Milk produced", f"{s['milk_liters']:,.2f} L"],
        ["Milk sales", fm(s["milk_revenue"])],
        ["Other income", fm(s["other_income"])],
        ["Total income", fm(s["total_income"])],
        ["Total expenses", fm(s["total_expense"])],
        ["Net profit / loss", fm(s["net"])],
    ]
    if s["cost_per_liter"] is not None:
        summary_rows.append(["Cost per liter", fm(s["cost_per_liter"])])
    if s["revenue_per_liter"] is not None:
        summary_rows.append(["Average milk price per liter", fm(s["revenue_per_liter"])])
    story.append(table(summary_rows, [90 * mm, 80 * mm], header=False))

    story.append(Paragraph("Income breakdown", h2))
    rows = [["Source", "Amount", "Share"]] + [
        [_safe(r["label"]), fm(r["total"]), f"{r['pct']}%"] for r in s["income_rows"]
    ]
    story.append(table(rows if len(rows) > 1 else rows + [["-", "-", "-"]], [90 * mm, 50 * mm, 30 * mm]))

    story.append(Paragraph("Expense breakdown", h2))
    rows = [["Category", "Amount", "Share"]] + [
        [_safe(r["label"]), fm(r["total"]), f"{r['pct']}%"] for r in s["expense_rows"]
    ]
    story.append(table(rows if len(rows) > 1 else rows + [["-", "-", "-"]], [90 * mm, 50 * mm, 30 * mm]))

    if s["top_animals"]:
        story.append(Paragraph("Top milk producers", h2))
        rows = [["Animal", "Liters", "Milk value"]] + [
            [_safe(f"{a['tag']} {a['name']}".strip()), f"{a['liters']:,.2f}", fm(a["revenue"])]
            for a in s["top_animals"]
        ]
        story.append(table(rows, [90 * mm, 40 * mm, 40 * mm]))

    story.append(Paragraph("Observations", h2))
    for line in insight_lines:
        story.append(Paragraph("&bull; " + escape(_safe(line)), body))

    doc.build(story)
    return buffer.getvalue()
