import pdfplumber
import pandas as pd
from tqdm import tqdm
from io import BytesIO
from openpyxl.styles import Alignment, Font, Border, Side
from typing import List
from collections import defaultdict

# spare parts (2).pdf

def get_vertical_lines(page, min_height=10, tolerance=2):
    x_positions = []

    for line in page.lines:
        x0, x1 = round(line["x0"]), round(line["x1"])
        y0, y1 = line["y0"], line["y1"]
        height = abs(y1 - y0)

        # Only consider vertical lines of sufficient height
        if abs(x0 - x1) < 1 and height >= min_height:
            x_positions.append(x0)

    # Remove near-duplicates by clustering
    x_positions = sorted(set(x_positions))
    clustered = []
    for x in x_positions:
        if not clustered or abs(x - clustered[-1]) > tolerance:
            clustered.append(x)

    return clustered


def get_vertical_lines_based(page, right_edge=560, tolerance=2):
    from difflib import SequenceMatcher

    vertical_lines = []

    text_lines = page.extract_text().splitlines()
    if len(text_lines) < 2:
        return [right_edge]  

    second_line = text_lines[1].strip()

    words = page.extract_words(keep_blank_chars=True, use_text_flow=True)

    for word in words:
        if word['text'].strip() in second_line:
            x0 = round(float(word['x0']))
            vertical_lines.append(x0)

    vertical_lines.append(right_edge)

    vertical_lines = sorted(set(vertical_lines))
    clustered = []
    for x in vertical_lines:
        if not clustered or abs(x - clustered[-1]) > tolerance:
            clustered.append(x)

    return clustered


def flatten_rows(data, add_col=False):
    processed = []
    previous_row = None

    for row in data:
        if "Pos" in str(row[0]).strip():
            continue

        if not add_col and not str(row[0]).strip().isdigit():
            if previous_row:
                for col_index in range(1, len(row)):
                    if previous_row[col_index] is None:
                        previous_row[col_index] = ""
                    if row[col_index]:
                        previous_row[col_index] += f" {row[col_index]}".strip()
            else:
                print(f"Warning: overflow row without a previous one: {row}")
        else:
            if previous_row:
                processed.append(previous_row)
            previous_row = row

    if previous_row:
        processed.append(previous_row)
    return processed


def normalize_headers(df: pd.DataFrame, header_map: dict) -> pd.DataFrame:
    new_columns = {}
    for col in df.columns:
        new_columns[col] = header_map.get(col, col)
    return df.rename(columns=new_columns)


def align_to_standard_schema(df: pd.DataFrame, standard_columns: List[str]) -> pd.DataFrame:
    for col in standard_columns:
        if col not in df.columns:
            df[col] = ""
    return df[standard_columns]


def extract_tables_(pdf_path):
    combined_data = []
    STANDARD_COLUMNS = ["Fig./\nPos.", "No./\nIdent.", "Nomenclature", "Benennung", "Qty./\nMenge.", "Qty. Unit/", "MPOS~Remark/Bemerkung", "see page\n s. Seite"]
    HEADER_MAP = {
        "Pos./\nFig.": "Fig./\nPos.",
        "Ident./\nNo.": "No./\nIdent.",
        "Menge\nQty.": "Qty./\nMenge.",
        "MPOS~Bemerkung/Remark" : "MPOS~Remark/Bemerkung",
        "s Seite\nsee page":"see page\n s. Seite",
        "Item no." : "Fig./\nPos",
        "SeboNr": "No./\nIdent.",
        "Description" : "Nomenclature",
        "Quantity" : "Qty./\nMenge.",
        "Comment" : "MPOS~Remark/Bemerkung",
        "Ident.\nNo.": "No./\nIdent.",
        "Bemerkung\nRemark" : "MPOS~Remark/Bemerkung",
        "Remark/\nBemerkung" : "MPOS~Remark/Bemerkung",
        "Menge/\nQty.": "Qty./\nMenge.",
        "Item\nno." : "Fig./\nPos",
        "Quanti\nty" : "Qty./\nMenge.",
        "Unit" : "Qty. Unit/",
        "ME/\nQty. Unit" : "Qty. Unit/",
        "siehe S.\nsee page" : "see page\n s. Seite",
        "Qty. Unit/ \nQty. Unit" : "Qty. Unit/"
    }
    # HEADER_MAP = {
    #     # Fig./Pos. equivalents
    #     "pos./ fig.": "Fig./\nPos.",
    #     "item no.": "Fig./\nPos.",
    #     "item\nno.": "Fig./\nPos.",
    #     "posición": "Fig./\nPos.",  # Spanish

    #     # No./Ident. equivalents
    #     "ident./ no.": "No./\nIdent.",
    #     "ident. no.": "No./\nIdent.",
    #     "no./ident.": "No./\nIdent.",
    #     "sebonr": "No./\nIdent.",
    #     "part no.": "No./\nIdent.",
    #     "ident-no.": "No./\nIdent.",
    #     "no. identificación": "No./\nIdent.",  # Spanish

    #     # Nomenclature / Description
    #     "description": "Nomenclature",
    #     "benennung": "Nomenclature",
    #     "descripción": "Nomenclature",  # Spanish

    #     # Qty./Menge.
    #     "menge qty.": "Qty./\nMenge.",
    #     "menge/ qty.": "Qty./\nMenge.",
    #     "quanti ty": "Qty./\nMenge.",
    #     "quantity": "Qty./\nMenge.",
    #     "qty.": "Qty./\nMenge.",
    #     "menge": "Qty./\nMenge.",
    #     "cantidad": "Qty./\nMenge.",  # Spanish

    #     # Unit
    #     "unit": "Qty. Unit/",
    #     "qty. unit/ qty. unit": "Qty. Unit/",
    #     "qty unit": "Qty. Unit/",
    #     "me": "Qty. Unit/",
    #     "me/ qty. unit": "Qty. Unit/",
    #     "unidad": "Qty. Unit/",  # Spanish

    #     # MPOS~Remark/Bemerkung
    #     "comment": "MPOS~Remark/Bemerkung",
    #     "bemerkung/remark": "MPOS~Remark/Bemerkung",
    #     "bemerkung\nremark": "MPOS~Remark/Bemerkung",
    #     "remark/\nbemerkung": "MPOS~Remark/Bemerkung",
    #     "bemerkung": "MPOS~Remark/Bemerkung",
    #     "remark": "MPOS~Remark/Bemerkung",
    #     "mpos~bemerkung/remark": "MPOS~Remark/Bemerkung",
    #     "comentario": "MPOS~Remark/Bemerkung",  # Spanish

    #     # Page reference
    #     "s. seite see page": "see page\n s. Seite",
    #     "siehe s.\nsee page": "see page\n s. Seite",
    #     "see page": "see page\n s. Seite",
    #     "ver página": "see page\n s. Seite"  # Spanish
    # }
    with pdfplumber.open(pdf_path) as pdf:
        # col_count = 0
        # odd = False
        # add_col = False
        for page_number, page in enumerate(tqdm(pdf.pages, desc="Processing Pages")):
            try:
                # case1 = False
                # case2 = False
                # case3 = False
                # case4 = False
                page_text = page.extract_text()                
                if page_text and ("Inhaltsverzeichnis" in page_text or "overview" in page_text):
                    continue

                if page_text and ("SeboNr" in page_text.splitlines()[1]):
                    column_lines = get_vertical_lines_based(page)
                    # print(vertical_line)
                    tables = page.extract_table(table_settings= {
                        "horizontal_strategy": "lines_strict",
                        "intersection_tolerance": 8,
                        "join_tolerance": 7,
                        "snap_x_tolerance": 5,
                        "explicit_vertical_lines": column_lines
                    })
                    debug_pic = page.to_image()
                    debug_pic.debug_tablefinder(
                        table_settings={
                        "horizontal_strategy": "lines_strict",
                        "intersection_tolerance": 8,
                        "join_tolerance": 7,
                        "snap_x_tolerance": 8,
                        "explicit_vertical_lines" : column_lines
                        }
                    )
                    debug_image_path = f"output_tables/debug_page_{page_number+1}.png"
                    debug_pic.save(debug_image_path)
                else:
                    vertical_line = get_vertical_lines(page)
                    # print(vertical_line)
                    tables = page.extract_table(table_settings= {
                        "horizontal_strategy": "lines_strict",
                        "intersection_tolerance": 8,
                        "join_tolerance": 7,
                        "snap_x_tolerance": 5,
                        "explicit_vertical_lines": vertical_line
                    })
                    debug_pic = page.to_image()
                    debug_pic.debug_tablefinder(
                        table_settings={
                        "horizontal_strategy": "lines_strict",
                        "intersection_tolerance": 8,
                        "join_tolerance": 7,
                        "snap_x_tolerance": 5,
                        "explicit_vertical_lines": vertical_line
                        }
                    )
                    debug_image_path = f"output_tables/debug_page_{page_number+1}.png"
                    debug_pic.save(debug_image_path)
                # elif page_text and ("Ident./" not in page_text.splitlines()[1]) and ("Bemerkung" in page_text.splitlines()[1]):
                #     # print("a")
                #     tables = page.extract_tables(table_settings= {
                #             "join_tolerance": 7,  
                #             "intersection_tolerance": 8, 
                #             "horizontal_strategy": "lines", 
                #             "explicit_horizontal_lines": [800],
                #             "snap_x_tolerance": 9,
                #             "explicit_vertical_lines": [43, 100, 140, 264, 400, 430, 540]
                #     })

                # elif page_text and ("ME/" in page_text.splitlines()[1] or "Qty. Unit/" in page_text.splitlines()[1]):
                #     # print("b")
                #     tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                #                                             "intersection_tolerance": 8,  
                #                                             "horizontal_strategy": "lines_strict",
                #                                             "snap_x_tolerance": 5,
                #                                             "explicit_vertical_lines": [40, 70, 110, 220, 330, 365, 410, 505, 550],
                #                                             "explicit_horizontal_lines": [800]
                #                                             })
                # elif page_text and ("Pos./" in page_text.splitlines()[1]) and (("MPOS" in page_text.splitlines()[1]) or "Bemerkung" in page_text.splitlines()[1]):
                #     print("c")
                #     tables = page.extract_tables(table_settings= {
                #             "join_tolerance": 7,  
                #             "intersection_tolerance": 8,  
                #             "horizontal_strategy": "lines_strict",
                #             "snap_x_tolerance": 5,
                #             "explicit_vertical_lines": [40, 70, 110, 220, 340, 380, 510, 550]
                #     })
                #     # debug_pic = page.to_image()
                #     # debug_pic.debug_tablefinder(
                #     #     table_settings={
                #     #     "join_tolerance": 7,  
                #     #         "intersection_tolerance": 8,  
                #     #         "horizontal_strategy": "lines_strict",
                #     #         "snap_x_tolerance": 5,
                #     #         "explicit_vertical_lines": [40, 70, 110, 220, 340, 380, 510, 550]
                #     #     }
                #     # )
                #     # debug_image_path = f"output_tables/debug_page_{page_number+1}.png"
                #     # debug_pic.save(debug_image_path)
                
                # elif page_text and "Pos./" in page_text.splitlines()[1]:
                #     # print("d")
                #     tables = page.extract_tables(table_settings= {
                #         "join_tolerance": 7,  
                #         "intersection_tolerance": 8,  
                #         "horizontal_strategy": "lines_strict",
                #         "snap_x_tolerance": 5,
                #         "explicit_vertical_lines": [40, 70, 110, 220, 330, 370, 410, 510, 550]
                #     })
                # elif page_text and "Fig./" in page_text.splitlines()[1]:
                #     # print("e")
                #     tables = page.extract_tables(table_settings= {
                #         "join_tolerance": 7,  
                #         "intersection_tolerance": 8,  
                #         "horizontal_strategy": "lines_strict",
                #         "snap_x_tolerance": 5,
                #         "explicit_vertical_lines": [40, 70, 110, 220, 340, 380, 510, 550]
                #     })
                # elif page_text and ("Quanti" in page_text.splitlines()[1] or "Quanti" in page_text.splitlines()[2]):
                #     odd = True
                #     # print("f")
                #     if "Comment" not in page_text:
                #         # no mpos (5) --> current
                #         # and we need mpos (6)
                #         if "Mpos" in page_text:
                #             case1 = True
                #             # item, senumber, descp, quant, unit, mpos
                #             # comment is blank
                #             tables = page.extract_tables(table_settings={
                #                 "join_tolerance": 7,  
                #                 "intersection_tolerance": 8,  
                #                 "horizontal_strategy": "lines_strict",
                #                 "snap_x_tolerance": 5,
                #                 "explicit_vertical_lines": [43, 90, 200, 320, 370, 440, 560]
                #                 })
                #         else:
                #             # item, senumber, descp, quant, unit
                #             # mpos and comment is blank
                #             case2 = True
                #             tables = page.extract_tables(table_settings={
                #                 "join_tolerance": 7,  
                #                 "intersection_tolerance": 8,  
                #                 "horizontal_strategy": "lines_strict",
                #                 "snap_x_tolerance": 5,
                #                 "explicit_vertical_lines": [50 ,85, 260, 440, 480, 555]
                #                 })
                #     else:
                #         if "Mpos" in page_text:
                #             case3 = True
                #         # with comment (6) same of the second bullet above
                #         # with comment + mpose (7)

                #         # item, senumber, descp, quant, unit, mpos, comment
                #             tables = page.extract_tables(table_settings={
                #                 "join_tolerance": 7,  
                #                 "intersection_tolerance": 8,  
                #                 "horizontal_strategy": "lines_strict",
                #                 "snap_x_tolerance": 5,
                #                 "explicit_vertical_lines": [50 ,85, 180, 260, 310, 380, 470, 555]
                #                 })
                #             # _pic = page.to_image()
                #             # debug_pic.debug_tablefinder(
                #             #     table_settings={
                #             #     "join_tolerance": 7,  
                #             #         "intersection_tolerance": 8,  
                #             #         "horizontal_strategy": "lines_strict",
                #             #         "snap_x_tolerance": 5,
                #             #         "explicit_vertical_lines": [50 ,85, 180, 260, 310, 380, 470, 555]
                #             #     }
                #             # )
                #             # debug_image_path = f"output_tables/debug_page_{page_number+1}.png"
                #             # debug_pic.save(debug_image_path)
                #         else:
                #             case4 = True
                #             # item, senumber, descp, quant, unit, comment
                #             # no mpos
                #             tables = page.extract_tables(table_settings={
                #                 "join_tolerance": 7,  
                #                 "intersection_tolerance": 8,  
                #                 "horizontal_strategy": "lines_strict",
                #                 "snap_x_tolerance": 5,
                #                 "explicit_vertical_lines": [43, 90, 200, 320, 370, 440, 560]
                #                 })
                # elif page_text and "Comment" in page_text.splitlines()[0]:
                #     # print("g")
                #     tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                #                                             "intersection_tolerance": 8,  
                #                                             "horizontal_strategy": "lines_strict",
                #                                             "snap_x_tolerance": 5,
                #                                             "explicit_vertical_lines": [35, 100, 235, 365, 440, 570],
                #                                             "explicit_horizontal_lines": [800]
                #                                             })
                # elif page_text and "Comment" in page_text.splitlines()[1]:
                #     # print("h")
                #     tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                #                                             "intersection_tolerance": 8,  
                #                                             "horizontal_strategy": "lines_strict",
                #                                             "snap_x_tolerance": 5,
                #                                             "explicit_vertical_lines": [50, 100, 235, 365, 440, 550],
                #                                             "explicit_horizontal_lines": [800]
                #                                             })
                # else:
                #     if page_text and "Benennung" in page_text.splitlines()[1]:
                #         add_col = True
                #         tables = page.extract_tables(table_settings={"intersection_tolerance": 8,  
                #                                                 "horizontal_strategy": "lines_strict",
                #                                                 "snap_x_tolerance": 5,
                #                                                 "explicit_vertical_lines": [40, 125, 295, 465, 550],
                #                                                 "explicit_horizontal_lines": [800]
                #                                                 })
                #     else:
                #         tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                #                                                 "intersection_tolerance": 8,  
                #                                                 "horizontal_strategy": "lines_strict",
                #                                                 "snap_x_tolerance": 5,
                #                                                 "explicit_vertical_lines": [50, 100, 235, 460, 550],
                #                                                 "explicit_horizontal_lines": [800]
                # 
                #                                                })
                i = 0
                if tables:   
                    if len(tables) < 2 or not isinstance(tables[0], list):
                        print(f"⚠️ Skipping malformed table on page {page_number + 1}: {tables[0] if tables else 'empty'}")
                        continue  
                    header = tables[0]
                    raw_rows = tables[1:]
                    df = pd.DataFrame(raw_rows, columns=header)
                    df = normalize_headers(df, HEADER_MAP)
                    flattened_data = flatten_rows(df.values.tolist())
                    df = pd.DataFrame(flattened_data, columns=df.columns)
                    df = align_to_standard_schema(df, STANDARD_COLUMNS)
                    combined_data.append(df)

                    # if odd:
                    #     if case1:
                    #         df.insert(6, "Comment", "")
                    #     if case2:
                    #         df.insert(5, "Mpos", "")
                    #         df.insert(6, "Comment", "")
                    #     if case4:
                    #         df.insert(5, "Mpos", "")
                                
                    # if add_col:
                    #     df.insert(0, "Pos./", "")
                    #     df.insert(4, "Qty", "")
                    #     df.insert(5, "Remark", "")
                    
                    # data = df.values.tolist()
                    # processed_data = []
                    # for row in data:
                    #     # print(f"Processing row: {row}")
                    #     if "Pos" in row[0].strip():
                    #         continue   
                    #     if not(add_col):
                    #         if not row[0].strip().isdigit():
                    #             # print(f"Row is not a number: {row[0]}")
                    #             if previous_row:
                    #                 for col_index in range(1, len(row)):
                    #                     if previous_row[col_index] is None:
                    #                         previous_row[col_index] = ""
                    #                     if row[col_index]:
                    #                         previous_row[col_index] += f" {row[col_index]}".strip()
                    #             else:
                    #                 print(f"Warning: Overflow row detected without a previous row: {row}")
                    #         else:
                    #             if previous_row:
                    #                 processed_data.append(previous_row)  # Save previous before replacing it
                    #             previous_row = row   

                    # final_df = pd.concat(combined_data, ignore_index=True)

            except Exception as e:
                print(f"Error on pathge {page_number+1}: {e}")
    if combined_data:
        combined_df = pd.concat(combined_data, ignore_index=True)
        output_stream = BytesIO()
    else:
        combined_df = pd.DataFrame()
        output_stream = BytesIO()
    # combined_df = ""
    # output_stream = ""
    # col_count = len(combined_data[0])
    # if col_count == 5 or col_count == 4:
    #     combined_df = pd.DataFrame(combined_data, columns=["Item no.", "SeboNr", "Description", "Quantity", "Comment"])
    #     output_stream = BytesIO()
    # elif col_count == 6:
    #     combined_df = pd.DataFrame(combined_data, columns=["Pos./\nFig.", "Ident./\nNo.", "Benennung", "Nomenclature", "Menge/\nQty.", "Bemerkung/\nRemark"])
    #     output_stream = BytesIO()
    # elif col_count == 8:
    #     combined_df = pd.DataFrame(combined_data, columns=["Fig./\nPos.", "No./\nIdent.", "Nomenclature", "Benennung", "Qty./\nMenge.", "Qty. Unit/", "MPOS~Remark/Bemerkung", "see page\n s. Seite"])
    #     output_stream = BytesIO()
    # elif odd:
    #     combined_df = pd.DataFrame(combined_data, columns=["Item no.", "SeboNr", "Description", "Quantity", "Unit", "Mpos. No.", "Comment"])
    #     output_stream = BytesIO()
    # else:
    #     combined_df = pd.DataFrame(combined_data, columns=["Pos./\nFig.", "Ident./\nNo.", "Benennung", "Nomenclature", "Menge/\nQty.", "MPOS~Bemerkung/\nRemark", "s. Seite\nsee Page"])
    #     output_stream = BytesIO()
   
    # make excel pretty
    with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
        combined_df.to_excel(writer, index=False, sheet_name='Combined Output')
    
    output_stream.seek(0)
    from openpyxl import load_workbook
    wb = load_workbook(output_stream)
    sheet = wb.active

    for column in sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter 
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        adjusted_width = max_length + 2  
        sheet.column_dimensions[column_letter].width = adjusted_width

    for cell in sheet[1]: 
        cell.font = Font(bold=True)

    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(horizontal='center', vertical='center')

    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    for row in sheet.iter_rows():
        for cell in row:
            cell.border = thin_border

    output_stream = BytesIO()
    wb.save(output_stream)
    output_stream.seek(0)
    return output_stream
