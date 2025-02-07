import pdfplumber
import pandas as pd
from borb.pdf import Document, Page, PDF
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.layout.forms.text_field import TextField
from borb.pdf import SingleColumnLayoutWithOverflow
from borb.pdf import TableCell
from borb.pdf import HexColor
from decimal import Decimal
import io
import re

def extract_values(pdf_path):
    combinded_data = []
    subtotal = None
    total = None
    currency = "N/A"

    with pdfplumber.open(pdf_path) as pdf:
        i = 0
        for page in pdf.pages:
            text = page.extract_text()
            subtotal_match = re.search(r"SUBTOTAL\s+([\d,]+\.\d{2})", text)
            if subtotal_match:
                subtotal = subtotal_match.group(1)
            total_match = re.search(r"TOTAL\s+(USD|EUR)\s+([\d,]+\.\d{2})", text)
            if total_match:
                currency = total_match.group(1) 
                total = total_match.group(2)

            if i == 0:
                height = page.height
                width = page.width
                cropped_page_1 = page.within_bbox((0, 2*height/5, width, height))
                tables = cropped_page_1.extract_table(table_settings={
                    "horizontal_strategy": "text",
                    "explicit_vertical_lines": [67, 225, 270, 340, 545],
                    "snap_tolerance": 9,
                    "vertical_strategy": "explicit"
                })

                debug_pic= cropped_page_1.to_image()
                debug_pic.debug_tablefinder(table_settings={
                    "horizontal_strategy": "text",
                    "explicit_vertical_lines": [67, 225, 270, 340, 545],
                    "vertical_strategy": "explicit",
                    "snap_tolerance": 8
                })
                debug_pic.save(f"output_tables/{i}.png")

                cropped_page_2 = page.within_bbox((0, height/5, width, 4*height/9))
                shipping_info = cropped_page_2.extract_table(table_settings={
                    "horizontal_strategy": "text",
                    "explicit_vertical_lines": [60, 210, 400, 520],
                    "vertical_strategy": "explicit",
                    "snap_tolerance": 8

                })
            else:
                tables = page.extract_table(table_settings={
                    "horizontal_strategy": "text",
                    "explicit_vertical_lines": [67, 225, 270, 340, 545],
                    "snap_tolerance": 10,
                    "vertical_strategy": "explicit"
                })
            i += 1
            if tables:
                df = pd.DataFrame(tables[1:], columns=tables[0])
                processed_data = []
                previous_row = None

                for row in df.values.tolist():
                    if "Approved" in row[0].strip() or "Date" in row[0].strip():
                        continue
                    if not row[1].strip():
                        if previous_row:
                            for col_index in range(2, len(row)):  
                                previous_row[0] += f"\n{row[0].strip()}"
                    else:
                        processed_data.append(row)
                        previous_row = row
            combinded_data.extend(processed_data)
            
            shipping_data = []
            if shipping_info:
                df_ship = pd.DataFrame(shipping_info, columns=shipping_info[0])
                for row in df_ship.values.tolist():
                    if "Purchase" in row[0]:
                        continue
                    elif row[0].strip() == "" and row[1].strip() == "":
                        continue
                    elif "ACTIV" in row[0]:
                        continue
                    else:
                        shipping_data.append(row)

    df = pd.DataFrame(combinded_data, columns=["Item", "Qty Order", "Each", "Total"])
    df.insert(2, "Qty Rec", "")
    df.insert(3, "Qty B/O", "")
    combinded_data = df.values.tolist()
    combinded_data.insert(0, ["Item", "Qty Order", "Qty Rec", "Qty B/O", "Each", "Total"])

    # pdf portion

    buffer = io.BytesIO()

    doc = Document()
    page = Page()
    doc.add_page(page)

    layout = SingleColumnLayoutWithOverflow(page)

    layout.add(Paragraph("Equipment Reuse International, LLC", font="Helvetica-Bold", font_size=Decimal(12)))
    layout.add(Paragraph("2962 Mechanic Street", font_size=Decimal(10)))
    layout.add(Paragraph("Lake City, PA 16423", font_size=Decimal(10)))
    layout.add(Paragraph("scott@equip-reuse.com", font_size=Decimal(10)))
    layout.add(Paragraph("www.equip-reuse.com", font_size=Decimal(10)))

    layout.add(Paragraph("Receving Order", font="Helvetica-Bold", font_size=Decimal(20),font_color=HexColor("#d1a700")))
    # print(shipping_data)
    subheader_table = FixedColumnWidthTable(number_of_columns=3, number_of_rows=len(shipping_data))
    for x in shipping_data:
        try:
            if x[0] == "":
                x[0] = " "
            if x[1] == "":
                x[1] = " "
            if x[2] == "":
                x[2] = " "
            subheader_table.add(TableCell(Paragraph(x[0], font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
            subheader_table.add(TableCell(Paragraph(x[1], font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
            subheader_table.add(TableCell(Paragraph(x[2], font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
        except:
            print(x)

    layout.add(subheader_table)

    # table section

    data_table = FixedColumnWidthTable(
            number_of_columns=6,
            number_of_rows=len(combinded_data),
        )
    
    for header in combinded_data[0]:
        data_table.add(Paragraph(header, font="Helvetica-Bold", font_size=Decimal(10)))

# Add Data Rows
    for row_index, row in enumerate(combinded_data[1:]):
        for col_index, cell in enumerate(row):
            if col_index in [2, 3]:  # Editable text fields
                data_table.add(
                    TextField(
                        field_name=f"field_{row_index}_{col_index}",
                        value=cell,
                        font_size=Decimal(8),
                        border_width=Decimal(0.3)
                    )
                )
            else:  # Regular text
                data_table.add(TableCell(Paragraph(cell, font_size=Decimal(10))))
    layout.add(data_table)
    
    layout.add(Paragraph(" "))

    if subtotal:
        amount_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=2)
        amount_table.add(TableCell(Paragraph("SUBTOTAL: ", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
        amount_table.add(TableCell(Paragraph(subtotal, font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
        amount_table.add(TableCell(Paragraph("TOTAL: ", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
        amount_table.add(TableCell(Paragraph(f"{currency} {total}", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
        layout.add(amount_table)
    else:
        amount_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=1)
        amount_table.add(TableCell(Paragraph("TOTAL: ", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
        amount_table.add(TableCell(Paragraph(f"{currency} {total}", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
        layout.add(amount_table)

    layout.add(Paragraph(" "))
    approved_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=2)
    approved_table.add(TableCell(Paragraph("Recieved: ", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
    approved_table.add(TableCell(TextField(field_name="RevievedDate", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
    approved_table.add(TableCell(Paragraph("Checked & Scanned: ", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
    approved_table.add(TableCell(TextField(field_name="CheckedDate", font_size=Decimal(11)), border_right=False, border_bottom=False,border_top=False, border_left=False))
    
    layout.add(approved_table)
    buffer.seek(0)
    PDF.dumps(buffer, doc)
    return buffer.getvalue()
