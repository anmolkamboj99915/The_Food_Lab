from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PDFService:
    @staticmethod
    def generate_bill_pdf(bill):
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f'Food Lab Bill {bill.bill_number}',
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='FoodLabTitle', parent=styles['Title'], textColor=colors.HexColor('#8b1e3f')))
        styles.add(ParagraphStyle(name='FoodLabSmall', parent=styles['Normal'], fontSize=9, leading=12))

        story = []
        logo_path = PDFService._resolve_optional_file(settings.RESTAURANT_LOGO_PATH)
        if logo_path:
            story.append(Image(str(logo_path), width=34 * mm, height=34 * mm, kind='proportional'))
            story.append(Spacer(1, 4 * mm))

        story.append(Paragraph(settings.RESTAURANT_NAME, styles['FoodLabTitle']))
        story.append(Paragraph(settings.RESTAURANT_ADDRESS, styles['FoodLabSmall']))
        story.append(Paragraph(f'GST Number: {settings.RESTAURANT_GST_NUMBER}', styles['FoodLabSmall']))
        story.append(Spacer(1, 8 * mm))

        meta_data = [
            ['Bill Number', bill.bill_number, 'Customer', bill.customer.name],
            ['Date', bill.bill_date.strftime('%d %b %Y'), 'Time', bill.bill_time.strftime('%I:%M %p')],
            ['Phone', bill.customer.phone, 'Table', bill.table_number or '-'],
            ['Payment Mode', bill.get_payment_mode_display(), 'Email', bill.customer.email or '-'],
        ]
        meta_table = Table(meta_data, colWidths=[30 * mm, 55 * mm, 32 * mm, 55 * mm])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f3ef')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#eadbd4')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8 * mm))

        item_rows = [['Ordered Items', 'Quantity', 'Price', 'Total']]
        for item in bill.items.all():
            item_rows.append([
                item.name,
                PDFService._moneyless(item.quantity),
                PDFService._money(item.price),
                PDFService._money(item.total),
            ])
        item_table = Table(item_rows, colWidths=[82 * mm, 26 * mm, 34 * mm, 34 * mm])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b1e3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#eadbd4')),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 7 * mm))

        totals_data = [
            ['Subtotal', PDFService._money(bill.subtotal)],
            [f'GST ({bill.gst_percent}%)', PDFService._money(bill.gst_amount)],
            ['Discount', f'- {PDFService._money(bill.discount_amount)}'],
            ['Grand Total', PDFService._money(bill.grand_total)],
        ]
        totals_table = Table(totals_data, colWidths=[118 * mm, 58 * mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f4b400')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#eadbd4')),
            ('PADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(totals_table)

        payment_qr_path = PDFService._resolve_optional_file(settings.RESTAURANT_PAYMENT_QR_PATH)
        if payment_qr_path:
            story.append(Spacer(1, 8 * mm))
            story.append(Paragraph('QR Payment', styles['Heading3']))
            story.append(Image(str(payment_qr_path), width=35 * mm, height=35 * mm, kind='proportional'))

        story.append(Spacer(1, 10 * mm))
        story.append(Paragraph('Thank you for visiting Food Lab \\u2764\\ufe0f', styles['Heading3']))
        story.append(Paragraph('Google Review: https://share.google/i2NiYn4viT9yXNChc', styles['FoodLabSmall']))
        story.append(Paragraph('Instagram: https://instagram.com/the_food_lab', styles['FoodLabSmall']))

        document.build(story)
        filename = f'food-lab-bill-{bill.bill_number}.pdf'
        bill.pdf_file.save(filename, ContentFile(buffer.getvalue()), save=True)
        return bill.pdf_file

    @staticmethod
    def _resolve_optional_file(path_value):
        if not path_value:
            return None
        path = Path(path_value)
        if not path.is_absolute():
            path = settings.BASE_DIR / path
        return path if path.exists() else None

    @staticmethod
    def _money(value):
        return f'Rs. {value:,.2f}'

    @staticmethod
    def _moneyless(value):
        normalized = value.normalize()
        return str(normalized).rstrip('0').rstrip('.') if '.' in str(normalized) else str(normalized)
