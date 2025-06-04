import pdfplumber
import pandas as pd
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
                cropped_page_1 = page.within_bbox((0, 2 * height / 5, width, height))
                tables = cropped_page_1.extract_table(table_settings={
                    "horizontal_strategy": "text",
                    "explicit_vertical_lines": [67, 225, 270, 340, 545],
                    "snap_tolerance": 9,
                    "vertical_strategy": "explicit"
                })

                # debug_pic= cropped_page_1.to_image()
                # debug_pic.debug_tablefinder(table_settings={
                #     "horizontal_strategy": "text",
                #     "explicit_vertical_lines": [67, 225, 270, 340, 545],
                #     "vertical_strategy": "explicit",
                #     "snap_tolerance": 8
                # })
                # debug_pic.save(f"output_tables/{i}.png")

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
                            previous_row[0] += f"\n{row[0].strip()}"
                    else:
                        previous_row = row[:]
                        processed_data.append(previous_row)
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

    data = {"shipping_data": shipping_data, "combinded_data": combinded_data, "subtotal": subtotal, "total": total, "currency": currency}

    return data
    # pdf portion

# def pdf_creation(path):
#     data = extract_values(path)
#     buffer = io.BytesIO()
#     c = canvas.Canvas(buffer, pagesize=letter)
#     width, height = letter
#     margin = 72 
#     current_y = height - margin
    
#     # Company info
#     c.setFont("Helvetica", 12)
#     company_info = [
#         "Equipment Reuse International, LLC",
#         "2962 Mechanic Street, Lake City, PA 16423",
#         "Email: scott@equip-reuse.com",
#         "Website: www.equip-reuse.com"
#     ]
    
#     for line in company_info:
#         c.drawString(margin, current_y, line)
#         current_y -= 20
#     current_y -= 20
    
#     # Title
#     c.setFillColor(colors.HexColor('#d1a700'))
#     c.setFont("Helvetica-Bold", 16)
#     title = "Receiving Order"
#     title_width = stringWidth(title, "Helvetica-Bold", 16)
#     c.drawString((width - title_width) / 2, current_y, title)
#     current_y -= 40
#     c.setFillColor(colors.black)
    
#     # Shipping table
#     c.setFont("Helvetica", 12)
#     if data.get("shipping_data"):
#         for row in data["shipping_data"]:
#             c.drawString(margin, current_y, f"{row[0]} {row[1]}")
#             current_y -= 20
#         current_y -= 20
    
#     # Main table
#     if data.get("combined_data"):
#         col_widths = [1.0, 2.0, 1.0, 1.0, 1.0]  # Proportional column widths
#         total_width = width - (2 * margin)
#         widths = [w * total_width / sum(col_widths) for w in col_widths]
#         row_height = 30
        
#         # Headers
#         c.setFont("Helvetica-Bold", 12)
#         x = margin
#         for header, width in zip(data["combined_data"][0], widths):
#             c.drawString(x + 5, current_y, header)
#             x += width
        
#         current_y -= row_height
        
#         # Data rows with form fields
#         for row_idx, row in enumerate(data["combined_data"][1:]):
#             x = margin
#             for col_idx, (cell, width) in enumerate(zip(row, widths)):
#                 if col_idx in [2, 3]:  # Editable columns (Quantity and Price)
#                     c.acroForm.textfield(
#                         name=f"field_{row_idx}_{col_idx}",
#                         tooltip=f"field_{row_idx}_{col_idx}",
#                         x=x + 2,
#                         y=current_y - row_height + 8,
#                         width=width - 4,
#                         height=20,
#                         value=str(cell),
#                         borderWidth=1,
#                         borderColor=colors.black,
#                         fillColor=colors.white,
#                         textColor=colors.black,
#                         fontSize=12
#                     )
#                 else:
#                     c.drawString(x + 5, current_y - row_height + 14, str(cell))
                
#                 # Draw cell borders
#                 c.rect(x, current_y - row_height, width, row_height)
#                 x += width
            
#             current_y -= row_height
#         current_y -= 20
    
#     # Totals
#     c.setFont("Helvetica-Bold", 12)
#     total_width = 200
#     x = width - margin - total_width
    
#     if data.get("subtotal"):
#         c.drawString(x, current_y, f"SUBTOTAL: {data['subtotal']}")
#         current_y -= 20
    
#     c.drawString(x, current_y, f"TOTAL: {data['currency']} {data['total']}")
#     current_y -= 40
    
#     # Approval section
#     x = margin
#     field_width = 200
    
#     # Received field
#     c.drawString(x, current_y, "Received:")
#     c.acroForm.textfield(
#         name="ReceivedDate",
#         tooltip="ReceivedDate",
#         x=x + 100,
#         y=current_y - 8,
#         width=field_width,
#         height=20,
#         borderWidth=1,
#         borderColor=colors.black,
#         fillColor=colors.white,
#         textColor=colors.black,
#         fontSize=12
#     )
#     current_y -= 30
    
#     # Checked & Scanned field
#     c.drawString(x, current_y, "Checked & Scanned:")
#     c.acroForm.textfield(
#         name="CheckedDate",
#         tooltip="CheckedDate",
#         x=x + 100,
#         y=current_y - 8,
#         width=field_width,
#         height=20,
#         borderWidth=1,
#         borderColor=colors.black,
#         fillColor=colors.white,
#         textColor=colors.black,
#         fontSize=12
#     )
    
#     c.save()
#     buffer.seek(0) 
#     return buffer.getvalue()




# def pdf_creation(path):
#     data = extract_values(path)

#     with open("receiving_report.html", "r") as file:
#         html_template = file.read()
    
#     template = Template(html_template)
#     html_content = template.render(data)
#     html_base64 = base64.b64encode(html_content.encode()).decode()

#     url = "https://api.doppio.sh/v1/render/pdf/sync"
    
#     headers = {
#         "Authorization": f"Bearer {API_KEY}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#     "page": {
#         "setContent": {
#         "html": html_base64
#         },
#         "pdf": {
#         "printBackground": True,
#         "format": "A4"
#         }
#     }
#     }

#     response = requests.post(url, json=payload, headers=headers)

#     # print("Test API Response:", response.text)
#     print(response.status_code)
#     print(response.text)

#     if response.status_code == 200:
#         pdf_url = response.json().get("pdf")
#         if pdf_url:
#             pdf_response = requests.get(pdf_url)
#             if pdf_response.status_code == 200:
#                 buffer = io.BytesIO(pdf_response.content)
#                 return buffer.getvalue()
#     return None
    
# from borb.pdf import Document, Page, PDF
# from borb.pdf.canvas.layout.page_layout.single_column_layout import SingleColumnLayout
# from borb.pdf.canvas.layout.text.paragraph import Paragraph
# from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
# from borb.pdf.canvas.layout.forms.text_field import TextField
# from borb.pdf.canvas.layout.table.table_cell import TableCell
# from borb.pdf.canvas.color.color import HexColor
# from borb.pdf.canvas.layout.layout_element import Alignment
# from decimal import Decimal

# from borb.pdf import Document, Page, PDF
# from borb.pdf.canvas.layout.text.paragraph import Paragraph
# from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
# from borb.pdf.canvas.layout.forms.text_field import TextField
# from borb.pdf import SingleColumnLayoutWithOverflow
# from borb.pdf import SingleColumnLayout
# from borb.pdf import TableCell
# from borb.pdf import HexColor
from decimal import Decimal
# from borb.pdf.canvas.layout.page_layout.multi_column_layout import MultiColumnLayout
# from borb.pdf.canvas.geometry.rectangle import Rectangle
# from borb.pdf.canvas.layout.layout_element import Alignment



# def pdf_creation(path: str) -> bytes:
#     """
#     Creates a fillable PDF based on `extract_values(path)`.  Adjusted for Borb 3.x.
#     Returns PDF bytes.
#     """
#     buffer = io.BytesIO()
#     data = extract_values(path)

#     # 1. Create Document & first Page
#     doc = Document()
#     page = Page()
#     doc.append_page(page)  # <-- in Borb 3.x, use `append_page` instead of `add_page`

#     # 2. Use SingleColumnLayout (handles overflow automatically)
#     layout: SingleColumnLayout = SingleColumnLayout(page)
#     # (optional) adjust margins if desired:
#     layout.top_margin = page.get_page_info().get_height() * Decimal(0.05)
#     layout.bottom_margin = page.get_page_info().get_height() * Decimal(0.05)
#     layout.left_margin = page.get_page_info().get_width() * Decimal(0.10)
#     layout.right_margin = page.get_page_info().get_width() * Decimal(0.10)

#     # 3. Add header paragraphs
#     layout.append_layout_element(Paragraph("Equipment Reuse International, LLC", font="Helvetica-Bold"))
#     layout.append_layout_element(Paragraph("2962 Mechanic Street", font_size=Decimal(10)))
#     layout.append_layout_element(Paragraph("Lake City, PA 16423", font_size=Decimal(10)))
#     layout.append_layout_element(Paragraph("scott@equip-reuse.com", font_size=Decimal(10)))
#     layout.append_layout_element(Paragraph("www.equip-reuse.com", font_size=Decimal(10)))

#     layout.append_layout_element(
#         Paragraph(
#             "Receiving Order",
#             font="Helvetica-Bold",
#             font_size=Decimal(20),
#             font_color=HexColor("#d1a700")
#         )
#     )

#     # 4. Build the “shipping_data” subheader table (3 columns)
#     subheader_table = FixedColumnWidthTable(number_of_columns=3, number_of_rows=len(data["shipping_data"]))
#     for row in data["shipping_data"]:
#         # replace empty cells with space so that Paragraph(...) doesn’t collapse
#         a, b, c = (row[0] or " "), (row[1] or " "), (row[2] or " ")
#         subheader_table.add(
#             TableCell(Paragraph(a, font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False)
#         )
#         subheader_table.add(
#             TableCell(Paragraph(b, font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False)
#         )
#         subheader_table.add(
#             TableCell(Paragraph(c, font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False)
#         )

#     layout.append_layout_element(subheader_table)

#     # 5. Build the “combined_data” main table (6 columns)
#     data_table = FixedColumnWidthTable(
#         number_of_columns=6,
#         number_of_rows=len(data["combined_data"]),
#         column_widths=[Decimal(2), Decimal(0.5), Decimal(1), Decimal(1), Decimal(1), Decimal(1)]
#     )

#     # 5.1. Header row
#     for header in data["combined_data"][0]:
#         data_table.add(Paragraph(header, font="Helvetica-Bold", font_size=Decimal(10)))

#     # 5.2. Data rows
#     for r_idx, row in enumerate(data["combined_data"][1:]):
#         for c_idx, cell in enumerate(row):
#             if c_idx in (2, 3):
#                 data_table.add(
#                     TextBox(
#                         field_name=f"field_{r_idx}_{c_idx}",
#                         value=str(cell),
#                         font_size=Decimal(8),
#                         border_width=Decimal(0.3)
#                     )
#                 )
#             else:
#                 data_table.add(
#                     TableCell(Paragraph(str(cell), font_size=Decimal(10)))
#                 )

#     data_table.set_padding_on_all_cells(Decimal(0.5), Decimal(0.5), Decimal(0.5), Decimal(0.5))
#     layout.append_layout_element(data_table)

#     # 6. Totals / Subtotals
#     layout.append_layout_element(Paragraph(" "))
#     if data["subtotal"]:
#         amount_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=2)
#         amount_table.add(TableCell(Paragraph("SUBTOTAL:", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#         amount_table.add(TableCell(Paragraph(data["subtotal"], font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#         amount_table.add(TableCell(Paragraph("TOTAL:", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#         amount_table.add(TableCell(Paragraph(f"{data['currency']} {data['total']}", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#         layout.append_layout_element(amount_table)
#     else:
#         amount_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=1)
#         amount_table.add(TableCell(Paragraph("TOTAL:", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#         amount_table.add(TableCell(Paragraph(f"{data['currency']} {data['total']}", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#         layout.append_layout_element(amount_table)

#     # 7. Approval form fields (Received / Checked & Scanned)
#     approved_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=2)
#     approved_table.add(TableCell(Paragraph("Received:", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#     approved_table.add(TableCell(TextBox(field_name="ReceivedDate", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#     approved_table.add(TableCell(Paragraph("Checked & Scanned:", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#     approved_table.add(TableCell(TextBox(field_name="CheckedDate", font_size=Decimal(11)), border_right=False, border_bottom=False, border_top=False, border_left=False))
#     layout.append_layout_element(approved_table)

#     # 8. Footer with page numbers
#     #    (SingleColumnLayout now automatically “overflows” onto new pages;
#     #     we only need to manually re‐attach a layout to each page and add the footer.)
#     total_pages = doc.get_document_info().get_number_of_pages()
#     for i in range(total_pages):
#         p = doc.get_page(i)
#         footer_layout: SingleColumnLayout = SingleColumnLayout(p)
#         footer_layout.append_layout_element(
#             Paragraph(
#                 f"Page {i+1} of {total_pages}",
#                 font_size=Decimal(9),
#                 font="Helvetica-Oblique",
#                 horizontal_alignment=Alignment.RIGHT,
#                 vertical_alignment=Alignment.BOTTOM
#             )
#         )

#     # 9. Write out the PDF
#     PDF.dumps(buffer, doc)
#     buffer.seek(0)
#     return buffer.getvalue()


from borb.pdf import Document, Page, TextBox, SingleColumnLayout, Paragraph, PDF, FixedColumnWidthTable, Table, HexColor, LayoutElement
from io import BytesIO
import tempfile
import pathlib
# import borb
# print(borb.__version__)
def pdf_creation(path):
    buffer = io.BytesIO()
    data = extract_values(path)
    doc = Document()
    page = Page()
    doc.append_page(page)

    layout = SingleColumnLayout(page)

    layout.horizontal_margin = page.get_size()[0] * 0.1
    layout.vertical_margin = page.get_size()[1] * 0.05

    layout.append_layout_element(Paragraph("Equipment Reuse International, LLC", font="Helvetica-Bold"))
    layout.append_layout_element(Paragraph("2962 Mechanic Street", font_size=10))
    layout.append_layout_element(Paragraph("Lake City, PA 16423", font_size=10))
    layout.append_layout_element(Paragraph("scott@equip-reuse.com", font_size=10))
    layout.append_layout_element(Paragraph("www.equip-reuse.com", font_size=10))

    layout.append_layout_element(Paragraph("Receiving Order", font="Helvetica-Bold", font_size=20,font_color=HexColor("#d1a700")))
    # print(shipping_data)
    subheader_table = FixedColumnWidthTable(number_of_columns=3, number_of_rows=len(data['shipping_data']))
    for x in data['shipping_data']:
        try:
            if x[0] == "":
                x[0] = " "
            if x[1] == "":
                x[1] = " "
            if x[2] == "":
                x[2] = " "
            subheader_table.append_layout_element(Table.TableCell(Paragraph(x[0], font_size=11)))
            subheader_table.append_layout_element(Table.TableCell(Paragraph(x[1], font_size=11)))
            subheader_table.append_layout_element(Table.TableCell(Paragraph(x[2], font_size=11)))
        except:
            print(x)

    layout.append_layout_element(subheader_table.no_borders())

    # table section

    data_table = FixedColumnWidthTable(
            number_of_columns=6,
            number_of_rows=len(data['combinded_data']),
            column_widths=[Decimal(2), Decimal(.5), Decimal(1), Decimal(1), Decimal(1), Decimal(1)]
        )
    
    for header in data['combinded_data'][0]:
        data_table.append_layout_element(Paragraph(header, font="Helvetica-Bold", font_size=10))

# Add Data Rows
    for row_index, row in enumerate(data['combinded_data'][1:]):
        for col_index, cell in enumerate(row):
            if col_index in [2, 3]:  # Editable text fields
                data_table.append_layout_element(
                    TextBox(
                        field_name=f"field_{row_index}_{col_index}",
                        value=cell,
                        font_size=8,
                    )
                )
            else:  # Regular text
                data_table.append_layout_element(Table.TableCell(Paragraph(cell, font_size=10)))
    data_table.set_padding_on_all_cells(.5, .5, .5, .5)
    layout.append_layout_element(data_table)
    
    layout.append_layout_element(Paragraph(" "))

    if data['subtotal']:
        amount_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=2)
        amount_table.append_layout_element(Table.TableCell(Paragraph("SUBTOTAL: ", font_size=11)))
        amount_table.append_layout_element(Table.TableCell(Paragraph(data['subtotal'], font_size=11)))
        amount_table.append_layout_element(Table.TableCell(Paragraph("TOTAL: ", font_size=11)))
        amount_table.append_layout_element(Table.TableCell(Paragraph(f"{data['currency']} {data['total']}", font_size=11)))
        layout.append_layout_element(amount_table.no_borders())
    else:
        amount_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=1)
        amount_table.append_layout_element(Table.TableCell(Paragraph("TOTAL: ", font_size=11)))
        amount_table.append_layout_element(Table.TableCell(Paragraph(f"{data['currency']} {data['total']}", font_size=11)))
        layout.append_layout_element(amount_table)

    approved_table = FixedColumnWidthTable(number_of_columns=2, number_of_rows=2)
    approved_table.append_layout_element(Table.TableCell(Paragraph("Received: ", font_size=11)))
    approved_table.append_layout_element(Table.TableCell(TextBox(field_name="RevievedDate", font_size=11)))
    approved_table.append_layout_element(Table.TableCell(Paragraph("Checked & Scanned: ", font_size=11)))
    approved_table.append_layout_element(Table.TableCell(TextBox(field_name="CheckedDate", font_size=11)))
    
    layout.append_layout_element(approved_table)

    total_pages = int(doc.get_number_of_pages())
    
    for i in range(total_pages):  
        page = doc.get_page(i)
        layout = SingleColumnLayout(page)
        layout.append_layout_element(Paragraph(f"Page {i+1} of {total_pages}", font_size = 9, font = "Helvetica-Oblique", horizontal_alignment=LayoutElement.HorizontalAlignment.RIGHT,
                      vertical_alignment=LayoutElement.VerticalAlignment.BOTTOM))




    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_path = pathlib.Path(tmp_file.name)

    try:
        # Write PDF content to the file path
        PDF.write(what=doc, where_to=tmp_path)

        # Read back the PDF content as bytes
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()

    finally:
        # Ensure the file is removed even if something goes wrong
        tmp_path.unlink(missing_ok=True)

    return pdf_bytes
    # buffer = BytesIO()
    # PDF.write(what=doc, where_to=buffer)
    # buffer.seek(0)
    # return buffer.getvalue()

# from reportlab.lib import colors 
# from reportlab.lib.pagesizes import letter 
# from reportlab.lib.units import mm, inch 
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Flowable 
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
# from reportlab.pdfgen import canvas
# from reportlab.platypus import KeepTogether

# class FormTextField(Flowable): 
#     def __init__(self, field_name, width, height, value="", fontSize=8): 
#         super().__init__() 
#         self.field_name = field_name 
#         self.width = width 
#         self.height = height 
#         self.value = value 
#         self.fontSize = fontSize

#     def wrap(self, availWidth, availHeight):
#         return self.width, self.height

#     def draw(self):
#         self.canv.acroForm.textfield(
#             name=self.field_name,
#             tooltip=self.field_name,
#             x=0,
#             y=0,
#             width=self.width,
#             height=self.height,
#             value=self.value,
#             fontSize=self.fontSize,
#             borderStyle='solid',
#             borderWidth=1,
#             borderColor=colors.black,
#             forceBorder=True
#         )
# class NumberedCanvas(canvas.Canvas): 
#     def __init__(self, *args, **kwargs): 
#         super(NumberedCanvas, self).__init__(*args, **kwargs) 
#         self._saved_page_states = [] 
    
#     def showPage(self): 
#         if hasattr(self, "_saved_page_states"):  
#             self._saved_page_states.append(dict(self.__dict__))  
#         super().showPage()
   
#     def save(self): 
#         num_pages = len(self._saved_page_states) 
#         for i, state in enumerate(self._saved_page_states): 
#             self.__dict__.update(state) 
#             self._pageNumber = i + 1 
#             self.draw_page_number(num_pages) 
#             super(NumberedCanvas, self).showPage()
#         super(NumberedCanvas, self).save()
   
#     def draw_page_number(self, page_count): 
#         self.setFont("Helvetica-Oblique", 9) 
#         self.drawRightString(self._pagesize[0] - 36, 15, f"Page {self._pageNumber} of {page_count}")

# def pdf_creation(path): 
#     data = extract_values(path)
#     buffer = io.BytesIO() 
#     doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
#     styles = getSampleStyleSheet()
#     header_style = ParagraphStyle("header", parent=styles['Normal'], fontName="Helvetica-Bold", fontSize=12)
#     small_style = ParagraphStyle("small", parent=styles['Normal'], fontSize=10)
#     title_style = ParagraphStyle("title", parent=styles['Normal'], fontName="Helvetica-Bold", fontSize=20,
#                                 textColor=colors.HexColor("#d1a700"))
#     table_header_style = ParagraphStyle("table_header", parent=styles['Normal'], fontName="Helvetica-Bold", fontSize=10)
#     table_cell_style = ParagraphStyle("table_cell", parent=styles['Normal'], fontSize=10)
#     amount_style = ParagraphStyle("amount", parent=styles['Normal'], fontSize=11)
#     approved_style = ParagraphStyle("approved", parent=styles['Normal'], fontSize=11)

#     story = []

#     # Header Section
#     story.append(Paragraph("Equipment Reuse International, LLC", header_style))
#     story.append(Paragraph("2962 Mechanic Street", small_style))
#     story.append(Paragraph("Lake City, PA 16423", small_style))
#     story.append(Paragraph("scott@equip-reuse.com", small_style))
#     story.append(Paragraph("www.equip-reuse.com", small_style))
#     story.append(Spacer(1, 12))
#     story.append(Paragraph("Receving Order", title_style))
#     story.append(Spacer(1, 12))

#     # Shipping Data Table
#     shipping_data = []
#     for row in data.get("shipping_data", []):
#         clean_row = [cell if cell != "" else " " for cell in row]
#         shipping_data.append(clean_row)
#     if shipping_data:
#         num_cols = len(shipping_data[0])
#         shipping_table = Table(shipping_data, colWidths=[doc.width/num_cols]*num_cols)
#         shipping_table.setStyle(TableStyle([
#             ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
#             ('BOX', (0,0), (-1,-1), 0.5, colors.black),
#             ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
#         ]))
#         story.append(shipping_table)
#         story.append(Spacer(1, 12))

#     # Main Data Table with fillable fields
#     combinded_data = data.get("combinded_data", [])
#     if combinded_data:
#         table_data = []
#         # Header row
#         header_row = [Paragraph(cell, table_header_style) for cell in combinded_data[0]]
#         table_data.append(header_row)

#         col_width_fractions = [2, 0.5, 1, 1, 1, 1]
#         total_fraction = sum(col_width_fractions)
#         col_widths = [doc.width * (frac/total_fraction) for frac in col_width_fractions]

#         # Data rows: for columns 2 and 3 (indexes 2,3), we add fillable fields.
#         for row_index, row in enumerate(combinded_data[1:]):
#             row_cells = []
#             for col_index, cell in enumerate(row):
#                 if col_index in [2, 3]:
#                     field_width = col_widths[col_index] - 4  # slight padding adjustment
#                     field = FormTextField(field_name=f"field_{row_index}_{col_index}", width=field_width, height=15, value=cell, fontSize=8)
#                     row_cells.append(KeepTogether([Spacer(1, 2), field]))
#                 else:
#                     row_cells.append(Paragraph(cell, table_cell_style))
#             table_data.append(row_cells)

#         main_table = Table(table_data, colWidths=col_widths)
#         main_table.setStyle(TableStyle([
#             ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
#             ('BOX', (0,0), (-1,-1), 0.5, colors.black),
#             ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
#             ('LEFTPADDING', (0,0), (-1,-1), 2),
#             ('RIGHTPADDING', (0,0), (-1,-1), 2),
#             ('TOPPADDING', (0,0), (-1,-1), 2),
#             ('BOTTOMPADDING', (0,0), (-1,-1), 2),
#         ]))
#         story.append(main_table)
#         story.append(Spacer(1, 12))

#     # Amount Table (Subtotal and Total)
#     if data.get("subtotal"):
#         amount_data = [
#             [Paragraph("SUBTOTAL: ", amount_style),
#             Paragraph(data["subtotal"], amount_style)],
#             [Paragraph("TOTAL: ", amount_style),
#             Paragraph(f"{data.get('currency', '')} {data.get('total', '')}", amount_style)]
#         ]
#         amount_table = Table(amount_data, colWidths=[doc.width/2.0]*2)
#     else:
#         amount_data = [
#             [Paragraph("TOTAL: ", amount_style),
#             Paragraph(f"{data.get('currency', '')} {data.get('total', '')}", amount_style)]
#         ]
#         amount_table = Table(amount_data, colWidths=[doc.width/2.0]*2)
#     amount_table.setStyle(TableStyle([
#         ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
#     ]))
#     story.append(amount_table)
#     story.append(Spacer(1, 12))

#     # Approved Table with form fields for Received and Checked dates.
#     approved_data = [
#         [Paragraph("Recieved: ", approved_style),
#         FormTextField(field_name="RevievedDate", width=doc.width/2.0 - 4, height=15, value="", fontSize=11)],
#         [Paragraph("Checked & Scanned: ", approved_style),
#         FormTextField(field_name="CheckedDate", width=doc.width/2.0 - 4, height=15, value="", fontSize=11)]
#     ]
#     approved_table = Table(approved_data, colWidths=[doc.width/2.0]*2)
#     approved_table.setStyle(TableStyle([
#         ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
#         ('BOX', (0,0), (-1,-1), 0.5, colors.black),
#         ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
#     ]))
#     story.append(approved_table)
#     story.append(Spacer(1, 12))

#     # Build the PDF using our custom NumberedCanvas to include footers.
#     doc.build(story, canvasmaker=NumberedCanvas)
#     pdf_value = buffer.getvalue()
#     return pdf_value