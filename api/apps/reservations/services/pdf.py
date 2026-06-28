from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from common.exceptions import NotFoundError

FONT_NAME = "SeznamovakFont"
HEADER = ["Name", "Nickname", "Email", "Year", "Faculty", "Disability", "Roommate", "Phone", "Paid"]
SEPARATOR = "------------------------------------"
# Points, together they fill the landscape A4 page
COLUMN_WIDTHS = [95, 65, 130, 30, 45, 120, 100, 80, 35]


class ReservationPdfService:
    """Exports the reservations of a batch to a PDF table."""

    def __init__(self, *, reservation_repository, batch_repository):
        self.reservation_repository = reservation_repository
        self.batch_repository = batch_repository

    def render_batch(self, *, batch_number):
        """Return the PDF bytes of all reservations of the batch, substitutes included."""
        batch = self.batch_repository.get_by_number(batch_number)
        if batch is None:
            raise NotFoundError("Batch not found.")
        reservations = self.reservation_repository.list_for_batch_with_details(batch)

        if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(FONT_NAME, settings.PDF_FONT_PATH))
        style = ParagraphStyle("cell", fontName=FONT_NAME, fontSize=8, leading=10)

        # Every reservation takes three rows: the data, the address and a separator line
        rows = [self._cells(HEADER, style)]
        separator_rows = []
        for reservation in reservations:
            billing = reservation.billing_information
            if reservation.is_paid:
                paid = "Yes"
            else:
                paid = "No"
            data_row = [
                f"{reservation.name} {reservation.surname}",
                reservation.nickname,
                reservation.email,
                str(reservation.year),
                reservation.faculty.faculty_abbrev,
                reservation.disability,
                reservation.roommate,
                billing.phone,
                paid,
            ]
            address_row = [billing.street, billing.city, billing.country, "", "", "", "", "", ""]
            separator_row = [SEPARATOR, "", "", "", "", "", "", "", ""]
            rows.append(self._cells(data_row, style))
            rows.append(self._cells(address_row, style))
            rows.append(self._cells(separator_row, style))
            separator_rows.append(len(rows) - 1)

        table = Table(rows, colWidths=COLUMN_WIDTHS, repeatRows=1)
        table_style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
        for row_index in separator_rows:
            table_style.add("SPAN", (0, row_index), (-1, row_index))
        table.setStyle(table_style)

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=20,
            rightMargin=20,
            topMargin=20,
            bottomMargin=20,
            title=f"turnus{batch_number}",
        )
        document.build([table])
        return buffer.getvalue()

    def _cells(self, values, style):
        cells = []
        for value in values:
            # Paragraph reads markup, so the text is escaped
            cells.append(Paragraph(escape(value), style))
        return cells
