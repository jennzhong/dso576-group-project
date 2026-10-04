"""
Build the Gradescope PDF from the evidence created by clean_listenbrainz.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)


SUMMARY_FILE = Path("cleaning_summary.json")
CHECKLIST_FILE = Path("checklist.json")
DECISION_LOG_FILE = Path("cleaning_decision_log.csv")
RECORD_CHECKS_FILE = Path("record_checks.csv")
INFO_FILE = Path("submission_info.json")
OUTPUT_PDF = Path("Shivanee_Kooner_Module6_Cleaning_Report.pdf")


def esc(value) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def p(value, style):
    return Paragraph(esc(value), style)


def main() -> None:
    required = [SUMMARY_FILE, CHECKLIST_FILE, DECISION_LOG_FILE, RECORD_CHECKS_FILE, INFO_FILE]
    missing = [str(x) for x in required if not x.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing report inputs: " + ", ".join(missing) +
            ". Run python clean_listenbrainz.py first."
        )

    summary = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    checklist = json.loads(CHECKLIST_FILE.read_text(encoding="utf-8"))
    info = json.loads(INFO_FILE.read_text(encoding="utf-8"))
    decisions = pd.read_csv(DECISION_LOG_FILE)
    checks = pd.read_csv(RECORD_CHECKS_FILE)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    h1 = ParagraphStyle("H1Custom", parent=styles["Heading1"], fontSize=14, leading=17, spaceBefore=8, spaceAfter=6)
    h2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], fontSize=11, leading=14, spaceBefore=6, spaceAfter=4)
    body = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=5)
    small = ParagraphStyle("Small", parent=body, fontSize=7.3, leading=9)
    status = ParagraphStyle("Status", parent=body, fontSize=9, leading=11, leftIndent=10)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="DSO 576 Module 6 Project Data Cleaning - Shivanee Kooner",
        author="Shivanee Kooner",
    )

    story = []
    story.append(Paragraph("DSO 576 - Module 6 Project Data Cleaning", title_style))
    story.append(Paragraph("Emerging Artist Discovery Through Listening Behavior", styles["Heading2"]))
    story.append(Spacer(1, 4))

    metadata = [
        ["Student", "Shivanee Kooner"],
        ["Branch", info.get("branch_name", "")],
        ["Branch URL", info.get("branch_url", "")],
        ["Submitted cleaning commit", info.get("commit_id", "")],
        ["Data source", "ListenBrainz public API"],
        ["Historical cutoff", "2026-09-22 00:00:00 UTC (includes listens through Sep. 21, 2026)"],
    ]
    meta_table = Table(
        [[p(a, small), p(b, small)] for a, b in metadata],
        colWidths=[1.35 * inch, 5.45 * inch],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Project question", h1))
    story.append(Paragraph(esc(summary["business_question"]), body))
    story.append(Paragraph("One row", h1))
    story.append(Paragraph(esc(summary["one_row"]), body))

    story.append(Paragraph("14-item checklist", h1))
    for item in checklist:
        block = [
            Paragraph(f"{item['number']}. {esc(item['title'])}", h2),
            Paragraph(f"<b>Status:</b> {esc(item['status'])}", status),
            Paragraph(f"<b>Evidence:</b> {esc(item['evidence'])}", body),
        ]
        story.append(KeepTogether(block))

    story.append(PageBreak())
    story.append(Paragraph("Cleaning decision log", h1))
    decision_data = [
        [p("Rule", small), p("Reason", small), p("Check", small)]
    ]
    for _, row in decisions.iterrows():
        decision_data.append(
            [
                p(row["rule"], small),
                p(row["reason"], small),
                p(row["check"], small),
            ]
        )
    decision_table = Table(
        decision_data,
        colWidths=[1.5 * inch, 2.75 * inch, 2.75 * inch],
        repeatRows=1,
    )
    decision_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(decision_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph("Five record checks", h1))
    story.append(
        Paragraph(
            "The expected result was defined from the written cleaning rule before it was compared with the actual cleaned output. "
            "The full original/expected/actual values are also saved in record_checks.csv.",
            body,
        )
    )

    for _, row in checks.iterrows():
        match = "Yes" if bool(row["matches_expected"]) else "No"
        record_data = [
            ["Case", row["case_type"]],
            ["Source row", row["source_row_index"]],
            ["Original artist", row.get("original_artist_name", "")],
            ["Expected artist", row.get("expected_artist_name", "")],
            ["Actual artist", row.get("actual_artist_name", "")],
            ["Original time", row.get("original_listened_at", "")],
            ["Expected time", row.get("expected_listened_at", "")],
            ["Actual time", row.get("actual_listened_at", "")],
            ["Original artist_mbids", row.get("original_artist_mbids", "")],
            ["Expected artist_mbids", row.get("expected_artist_mbids", "")],
            ["Actual artist_mbids", row.get("actual_artist_mbids", "")],
            ["Matches expected?", match],
        ]
        t = Table(
            [[p(a, small), p(b, small)] for a, b in record_data],
            colWidths=[1.45 * inch, 5.55 * inch],
        )
        t.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(KeepTogether([Paragraph(f"Record check {int(row['check'])}", h2), t, Spacer(1, 5)]))

    story.append(Paragraph("How one cleaning decision was checked", h1))
    story.append(Paragraph(esc(info.get("codex_note", "")), body))

    story.append(Paragraph("50-row cleaned sample", h1))
    story.append(Paragraph(esc(summary["sample_selection"]), body))
    story.append(
        Paragraph(
            "The full 50-row sample is included in the GitHub branch as cleaned_sample_50.csv.",
            body,
        )
    )

    story.append(Paragraph("Remaining limitations", h1))
    for limitation in summary["limitations"]:
        story.append(Paragraph(f"- {esc(limitation)}", body))

    doc.build(story)
    print(f"Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
