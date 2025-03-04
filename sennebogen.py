import pdfplumber
import pandas as pd
from tqdm import tqdm
from io import BytesIO
from openpyxl.styles import Alignment, Font, Border, Side


def extract_tables_(pdf_path):
    combined_data = []
    previous_row = None
    with pdfplumber.open(pdf_path) as pdf:
        col_count = 0
        odd = False
        add_col = False
        for page_number, page in enumerate(tqdm(pdf.pages, desc="Processing Pages")):
            try:
                case1 = False
                case2 = False
                case3 = False
                case4 = False
                page_text = page.extract_text()                
                if page_text and ("Inhaltsverzeichnis" in page_text or "overview" in page_text):
                    continue
                elif page_text and ("Ident./" not in page_text.splitlines()[1]) and ("Bemerkung" in page_text.splitlines()[1]):
                    # print("a")
                    tables = page.extract_tables(table_settings= {
                            "join_tolerance": 7,  
                            "intersection_tolerance": 8, 
                            "horizontal_strategy": "lines", 
                            "explicit_horizontal_lines": [800],
                            "snap_x_tolerance": 9,
                            "explicit_vertical_lines": [43, 100, 140, 264, 400, 430, 540]
                    })

                elif page_text and ("ME/" in page_text.splitlines()[1] or "Qty. Unit/" in page_text.splitlines()[1]):
                    # print("b")
                    tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                                                            "intersection_tolerance": 8,  
                                                            "horizontal_strategy": "lines_strict",
                                                            "snap_x_tolerance": 5,
                                                            "explicit_vertical_lines": [40, 70, 110, 220, 330, 365, 410, 505, 550],
                                                            "explicit_horizontal_lines": [800]
                                                            })
                elif page_text and ("Pos./" in page_text.splitlines()[1]) and (("MPOS" in page_text.splitlines()[1]) or "Bemerkung" in page_text.splitlines()[1]):
                    print("c")
                    tables = page.extract_tables(table_settings= {
                            "join_tolerance": 7,  
                            "intersection_tolerance": 8,  
                            "horizontal_strategy": "lines_strict",
                            "snap_x_tolerance": 5,
                            "explicit_vertical_lines": [40, 70, 110, 220, 340, 380, 510, 550]
                    })
                
                elif page_text and "Pos./" in page_text.splitlines()[1]:
                    # print("d")
                    tables = page.extract_tables(table_settings= {
                        "join_tolerance": 7,  
                        "intersection_tolerance": 8,  
                        "horizontal_strategy": "lines_strict",
                        "snap_x_tolerance": 5,
                        "explicit_vertical_lines": [40, 70, 110, 220, 330, 370, 410, 510, 550]
                    })
                elif page_text and "Fig./" in page_text.splitlines()[1]:
                    # print("e")
                    tables = page.extract_tables(table_settings= {
                        "join_tolerance": 7,  
                        "intersection_tolerance": 8,  
                        "horizontal_strategy": "lines_strict",
                        "snap_x_tolerance": 5,
                        "explicit_vertical_lines": [40, 70, 110, 220, 340, 380, 510, 550]
                    })
                elif page_text and ("Quanti" in page_text.splitlines()[1] or "Quanti" in page_text.splitlines()[2]):
                    odd = True
                    # print("f")
                    if "Comment" not in page_text:
                        # no mpos (5) --> current
                        # and we need mpos (6)
                        if "Mpos" in page_text:
                            case1 = True
                            # item, senumber, descp, quant, unit, mpos
                            # comment is blank
                            tables = page.extract_tables(table_settings={
                                "join_tolerance": 7,  
                                "intersection_tolerance": 8,  
                                "horizontal_strategy": "lines_strict",
                                "snap_x_tolerance": 5,
                                "explicit_vertical_lines": [43, 90, 200, 320, 370, 440, 560]
                                })
                        else:
                            # item, senumber, descp, quant, unit
                            # mpos and comment is blank
                            case2 = True
                            tables = page.extract_tables(table_settings={
                                "join_tolerance": 7,  
                                "intersection_tolerance": 8,  
                                "horizontal_strategy": "lines_strict",
                                "snap_x_tolerance": 5,
                                "explicit_vertical_lines": [50 ,85, 260, 440, 480, 555]
                                })
                    else:
                        if "Mpos" in page_text:
                            case3 = True
                        # with comment (6) same of the second bullet above
                        # with comment + mpose (7)

                        # item, senumber, descp, quant, unit, mpos, comment
                            tables = page.extract_tables(table_settings={
                                "join_tolerance": 7,  
                                "intersection_tolerance": 8,  
                                "horizontal_strategy": "lines_strict",
                                "snap_x_tolerance": 5,
                                "explicit_vertical_lines": [50 ,85, 180, 260, 310, 380, 470, 555]
                                })
                            # _pic = page.to_image()
                            # debug_pic.debug_tablefinder(
                            #     table_settings={
                            #     "join_tolerance": 7,  
                            #         "intersection_tolerance": 8,  
                            #         "horizontal_strategy": "lines_strict",
                            #         "snap_x_tolerance": 5,
                            #         "explicit_vertical_lines": [50 ,85, 180, 260, 310, 380, 470, 555]
                            #     }
                            # )
                            # debug_image_path = f"output_tables/debug_page_{page_number+1}.png"
                            # debug_pic.save(debug_image_path)
                        else:
                            case4 = True
                            # item, senumber, descp, quant, unit, comment
                            # no mpos
                            tables = page.extract_tables(table_settings={
                                "join_tolerance": 7,  
                                "intersection_tolerance": 8,  
                                "horizontal_strategy": "lines_strict",
                                "snap_x_tolerance": 5,
                                "explicit_vertical_lines": [43, 90, 200, 320, 370, 440, 560]
                                })
                elif page_text and "Comment" in page_text.splitlines()[0]:
                    # print("g")
                    tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                                                            "intersection_tolerance": 8,  
                                                            "horizontal_strategy": "lines_strict",
                                                            "snap_x_tolerance": 5,
                                                            "explicit_vertical_lines": [35, 100, 235, 365, 440, 570],
                                                            "explicit_horizontal_lines": [800]
                                                            })
                elif page_text and "Comment" in page_text.splitlines()[1]:
                    # print("h")
                    tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                                                            "intersection_tolerance": 8,  
                                                            "horizontal_strategy": "lines_strict",
                                                            "snap_x_tolerance": 5,
                                                            "explicit_vertical_lines": [50, 100, 235, 365, 440, 550],
                                                            "explicit_horizontal_lines": [800]
                                                            })
                else:
                    if page_text and "Benennung" in page_text.splitlines()[1]:
                        add_col = True
                        tables = page.extract_tables(table_settings={"intersection_tolerance": 8,  
                                                                "horizontal_strategy": "lines_strict",
                                                                "snap_x_tolerance": 5,
                                                                "explicit_vertical_lines": [40, 125, 295, 465, 550],
                                                                "explicit_horizontal_lines": [800]
                                                                })
                    else:
                        tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                                                                "intersection_tolerance": 8,  
                                                                "horizontal_strategy": "lines_strict",
                                                                "snap_x_tolerance": 5,
                                                                "explicit_vertical_lines": [50, 100, 235, 460, 550],
                                                                "explicit_horizontal_lines": [800]
                                                                })

                if tables:   
                    for i, table in enumerate(tables): 
                        # print(f"Table {i+1}: Columns: {len(table[0])}, Rows: {len(table) - 1}")
                        col_count = len(table[0])                       
                        df = pd.DataFrame(table[1:], columns=table[0])

                        if odd:
                            if case1:
                                df.insert(6, "Comment", "")
                            if case2:
                                df.insert(5, "Mpos", "")
                                df.insert(6, "Comment", "")
                            if case4:
                                df.insert(5, "Mpos", "")
                                    
                        if add_col:
                            df.insert(0, "Pos./", "")
                            df.insert(4, "Qty", "")
                            df.insert(5, "Remark", "")
                        
                        data = df.values.tolist()
                        processed_data = []

                        for row in data:
                            if "Pos" in row[0].strip():
                                continue   
                            if not(add_col):
                                if not row[0].strip().isdigit():
                                    if previous_row:
                                        for col_index in range(1, len(row)):
                                            if previous_row[col_index] is None:
                                                previous_row[col_index] = ""
                                            if row[col_index]:
                                                previous_row[col_index] += f" {row[col_index]}".strip()
                                    else:
                                        print(f"Warning: Overflow row detected without a previous row: {row}")
                                else:
                                    previous_row = row  

                        combined_data.extend(processed_data)

            except Exception as e:
                print(f"Error on pathge {page_number+1}: {e}")
    combined_df = ""
    output_stream = ""
    col_count = len(combined_data[0])
    # print(f"First few rows of combined_data: {combined_data[:5]}"
    print(odd)
    if col_count == 5 or col_count == 4:
        combined_df = pd.DataFrame(combined_data, columns=["Item no.", "SeboNr", "Description", "Quantity", "Comment"])
        output_stream = BytesIO()
    elif col_count == 6:
        combined_df = pd.DataFrame(combined_data, columns=["Pos./\nFig.", "Ident./\nNo.", "Benennung", "Nomenclature", "Menge/\nQty.", "Bemerkung/\nRemark"])
        output_stream = BytesIO()
    elif col_count == 8:
        combined_df = pd.DataFrame(combined_data, columns=["Fig./\nPos.", "No./\nIdent.", "Nomenclature", "Benennung", "Qty./\nMenge.", "Qty. Unit/", "MPOS~Remark/Bemerkung", "see page\n s. Seite"])
        output_stream = BytesIO()
    elif odd:
        combined_df = pd.DataFrame(combined_data, columns=["Item no.", "SeboNr", "Description", "Quantity", "Unit", "Mpos. No.", "Comment"])
        output_stream = BytesIO()
    else:
        combined_df = pd.DataFrame(combined_data, columns=["Pos./\nFig.", "Ident./\nNo.", "Benennung", "Nomenclature", "Menge/\nQty.", "MPOS~Bemerkung/\nRemark", "s. Seite\nsee Page"])
        output_stream = BytesIO()
   
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
