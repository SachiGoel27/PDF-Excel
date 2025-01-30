import pdfplumber
import pandas as pd
from tqdm import tqdm
from io import BytesIO
from openpyxl.styles import Alignment, Font, Border, Side

def extract_tables_(pdf_path):
    combined_data = []
    previous_row = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(tqdm(pdf.pages, desc="Processing Pages")):
            try:
                debug_pic1 = page.to_image(resolution=300)
                debug_pic1.debug_tablefinder(
                    table_settings={
                        "join_tolerance": 7,  
                        "intersection_tolerance": 8,  
                        "horizontal_strategy": "text",
                        "snap_x_tolerance": 5,
                        "explicit_horizontal_lines": [500, 800]
                    }
                )
                debug_image_path = f"output_tables/debug_page_{page_number+1}.png"
                debug_pic1.save(debug_image_path)


                # table_settings={
                #             "join_tolerance": 7,  
                #             "intersection_tolerance": 8,  
                #             "horizontal_strategy": "lines_strict",
                #             "snap_x_tolerance": 5,
                #             "explicit_vertical_lines": [40, 70, 110, 220, 340, 380, 510, 550],
                #             "explicit_horizontal_lines": [800]
                #         }


                # if tables:   
                #     for i, table in enumerate(tables): 
                #         print(f"Table {i+1}: Columns: {len(table[0])}, Rows: {len(table) - 1}")
                #         col_count = len(table[0])                       
                #         df = pd.DataFrame(table[1:], columns=table[0])

                #         data = df.values.tolist()
                #         processed_data = []
                        
                #         for row in data:
                #             if not row[0].strip() or not row[0].isdigit():
                #                 if previous_row:
                #                     for col_index in range(1, len(row)):
                #                         previous_row[col_index] += f" {row[col_index]}".strip()
                #                 else:
                #                     print(f"Warning: Overflow row detected without a previous row: {row}")
                #             else:
                #                 processed_data.append(row)
                #                 previous_row = row  

                #         combined_data.extend(processed_data)

            except Exception as e:
                print(f"Error on pathge {page_number+1}: {e}")

extract_tables_("_fpi0037.fpi.pdf")