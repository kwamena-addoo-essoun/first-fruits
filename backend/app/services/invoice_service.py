from sqlalchemy.orm import Session
from app.models.timelog import TimeLog
from app.models.project import Project
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover
    REPORTLAB_AVAILABLE = False  # pragma: no cover

class TimeTrackingService:
    @staticmethod
    def calculate_hours(start_time: datetime, end_time: datetime) -> float:
        """Calculate hours between two times, handling timezone-naive/aware mix."""
        from datetime import timezone as _tz

        def to_naive(dt: datetime) -> datetime:
            if dt.tzinfo is not None:
                return dt.astimezone(_tz.utc).replace(tzinfo=None)
            return dt

        delta = to_naive(end_time) - to_naive(start_time)
        return delta.total_seconds() / 3600

    @staticmethod
    def get_project_stats(db: Session, project_id: int) -> dict:
        """Get total hours and earnings for a project"""
        timelogs = db.query(TimeLog).filter(TimeLog.project_id == project_id).all()
        project = db.query(Project).filter(Project.id == project_id).first()
        
        total_hours = sum(log.hours for log in timelogs)
        total_earned = total_hours * project.hourly_rate if project else 0
        
        return {"total_hours": total_hours, "total_earned": total_earned}

class InvoiceService:
    @staticmethod
    def generate_invoice_number(user_id: int, invoice_count: int) -> str:
        """Generate unique invoice number"""
        return f"INV-{user_id}-{invoice_count + 1:04d}"

    @staticmethod
    def calculate_invoice_total(total_hours: float, hourly_rate: float) -> float:
        """Calculate invoice total"""
        return round(total_hours * hourly_rate, 2)


class InvoicePDFGenerator:
    @staticmethod
    def generate(invoice, user) -> bytes:
        """Generate a PDF for the given invoice and return raw bytes."""
        if not REPORTLAB_AVAILABLE:  # pragma: no cover
            raise RuntimeError("reportlab is not installed")  # pragma: no cover

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=inch, leftMargin=inch,
            topMargin=inch, bottomMargin=inch
        )
        styles = getSampleStyleSheet()
        story = []

        # ── Title ──────────────────────────────────────────────────────────
        title_style = ParagraphStyle(
            "InvoiceTitle", parent=styles["Heading1"],
            fontSize=28, spaceAfter=4, textColor=colors.HexColor("#2c3e50")
        )
        story.append(Paragraph("INVOICE", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # ── Meta (invoice # / dates) ────────────────────────────────────────
        issue = invoice.issue_date.strftime("%B %d, %Y")
        due = invoice.due_date.strftime("%B %d, %Y")
        paid = invoice.paid_date.strftime("%B %d, %Y") if invoice.paid_date else "—"

        meta_data = [
            ["Invoice #:", invoice.invoice_number, "Status:", invoice.status.upper()],
            ["Issue Date:", issue, "Due Date:", due],
        ]
        if invoice.paid_date:
            meta_data.append(["Paid Date:", paid, "", ""])

        meta_table = Table(meta_data, colWidths=[1.2 * inch, 2.3 * inch, 1.0 * inch, 2.5 * inch])
        meta_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.35 * inch))

        # ── From / To ───────────────────────────────────────────────────────
        from_name = user.company_name or user.username
        to_name = invoice.client_name or "—"
        from_to_data = [
            [Paragraph("<b>FROM</b>", styles["Normal"]), Paragraph("<b>BILL TO</b>", styles["Normal"])],
            [Paragraph(from_name, styles["Normal"]), Paragraph(to_name, styles["Normal"])],
        ]
        from_to = Table(from_to_data, colWidths=[3.5 * inch, 3.5 * inch])
        from_to.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#dee2e6")),
        ]))
        story.append(from_to)
        story.append(Spacer(1, 0.35 * inch))

        # ── Line items ──────────────────────────────────────────────────────
        desc = invoice.project_name or "Freelance Services"
        if invoice.notes:
            desc += f"\n{invoice.notes}"

        item_data = [
            ["DESCRIPTION", "HOURS", "RATE", "AMOUNT"],
            [desc, f"{invoice.total_hours:.2f} hrs",
             f"${invoice.hourly_rate:.2f}/hr", f"${invoice.total_amount:.2f}"],
            ["", "", "TOTAL DUE", f"${invoice.total_amount:.2f}"],
        ]
        item_table = Table(item_data, colWidths=[3.0 * inch, 1.2 * inch, 1.3 * inch, 1.5 * inch])
        item_table.setStyle(TableStyle([
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            # Data row
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8f9fa")),
            # Total row
            ("FONTNAME", (2, 2), (-1, 2), "Helvetica-Bold"),
            ("FONTSIZE", (2, 2), (-1, 2), 12),
            ("LINEABOVE", (2, 2), (-1, 2), 1, colors.HexColor("#2c3e50")),
            # General
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [None]),
            ("GRID", (0, 0), (-1, 1), 0.5, colors.HexColor("#dee2e6")),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(item_table)

        doc.build(story)
        return buffer.getvalue()

