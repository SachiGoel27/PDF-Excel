import pdfplumber
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
import io

def extract_values(pdf_path):
    combinded_data = []
    with pdfplumber.open(pdf_path) as pdf:
        i = 0
        for page in pdf.pages:
            if i == 0:
                height = page.height
                width = page.width
                page = page.within_bbox((0, 2*height/5, width, height))
                tables = page.extract_table(table_settings={
                    "horizontal_strategy": "text",
                    "explicit_vertical_lines": [67, 225, 270, 340, 549],
                    "snap_tolerance": 9
                })
                # debug_pic= page.to_image()
                # debug_pic.debug_tablefinder(table_settings={
                #     "horizontal_strategy": "text",
                #     "explicit_vertical_lines": [67, 225, 270, 340, 549],
                #     "snap_tolerance": 9
                # })
                # debug_pic.save(f"output_tables/{i}.png")
            else:
                tables = page.extract_table(table_settings={
                    "horizontal_strategy": "text",
                    "explicit_vertical_lines": [67, 225, 270, 340, 549],
                    "snap_tolerance": 9
                })
            
            if tables:
                df = pd.DataFrame(tables[1:], columns=tables[0])
                data = df.values.tolist()
                processed_data = []
                for row in data:
                    if row[1].strip():
                        processed_data.append(row)
            combinded_data.extend(processed_data)
            i += 1
    combinded_df = pd.DataFrame(processed_data, columns=["Item", "Qty Order", "Each", "Total"])
    combinded_df.insert(2, "Qty Rec", "")
    combinded_df.insert(3, "Qty B/O", "")
    combinded_data = combinded_df.values.tolist()
    combinded_data.insert(0, ["Item", "Qty Order", "Qty Rec", "Qty B/O", "Each", "Total"])
    
    # pdf portion

    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(20, 750, "Equipment Reuse International, LLC")

    c.setFont("Helvetica", 12)
    c.drawString(20, 720, "2962 Mechanic Street")

    c.drawString(20, 705, "Lake City, PA 16423")

    c.drawString(20, 690, "scott@equip-reuse.com")

    c.drawString(20, 675, "www.equip-reuse.com")

    c.setFillColorRGB(1, 0.8, 0.2)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20, 640, "Purchase Order")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 15)
    c.drawString(20, 620, "VENDOR")
    c.drawString(220, 620, "SHIP TO")
    c.drawString(420, 620, "P.O. NO.")

    table_x, table_y = 10, 300  
    colWidths = [150, 100, 100, 100, 80, 80]
    row_height = 30 

    table_style = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ("FONTSIZE", (0, 0), (-1, -1), 10),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.beige, colors.white]),
    ])

    table = Table(combinded_data, colWidths=colWidths)
    table.setStyle(table_style)
    table.wrapOn(c, 500, 700)
    table.drawOn(c, table_x, table_y)


    table_bottom = table_y
    table_top = table_y + (len(combinded_data) * row_height)
    form = c.acroForm
    for row_index, row in enumerate(combinded_data[1:], start=1):
        field_y = table_top - (row_index * row_height) 

        form.textfield(
            name=f"qtyrec_{row_index}",
            x=table_x + sum(colWidths[:2]) + 2,  
            y= field_y,
            width=colWidths[2] - 4,  
            height=20,
            textColor=colors.black, borderColor=colors.black, fillColor=colors.white,
            fontSize=10,
        )

        form.textfield(
            name=f"qtybo_{row_index}",
            x=table_x + sum(colWidths[:3]) + 2,  
            y= field_y,
            width=colWidths[3]-4,  
            height=20,
            textColor=colors.black, borderColor=colors.black, fillColor=colors.white,
            fontSize=10,
        )



    string_spacing = 20
    c.drawString(10, table_bottom - string_spacing - 20, "Additional string 1")
    c.drawString(10, table_bottom - string_spacing - 40, "Additional string 2")    

    c.save()

    buffer.seek(0)
    return buffer.getvalue()
