import pdfplumber
import pandas as pd
from tqdm import tqdm


def extract_tables_(pdf_path, output_dir):
    combined_data = []
    header = ["Item no.", "SeboNr", "Description", "Quantity", "Comment"]  # Expected header

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(tqdm(pdf.pages, desc="Processing Pages")):
            try:
                # for debugging the images
                debug_pic = page.to_image()
                debug_pic.debug_tablefinder(
                    table_settings={
                        "join_tolerance": 7,  
                        "intersection_tolerance": 8,  
                        "horizontal_strategy": "lines_strict",
                        "snap_x_tolerance": 5,
                        "explicit_vertical_lines": [30, 100, 235, 365, 440, 570]

                    }
                )
                debug_image_path = f"{output_dir}/debug_page_{page_number+1}.png"
                debug_pic.save(debug_image_path)
                
                tables = page.extract_tables(table_settings={"join_tolerance": 7,  
                                                            "intersection_tolerance": 8,  
                                                            "horizontal_strategy": "lines_strict",
                                                            "snap_x_tolerance": 5,
                                                            "explicit_vertical_lines": [30, 100, 235, 365, 440, 570]})
                if tables:     
                    for i, table in enumerate(tables):
                        print(f"Page {page_number+1}, Table {i+1}:\n{table}")
                        
                        if len(table[0]) > 5:
                            print("Split col")
                            for row in table[1:]:  
                                row[2] = f"{row[2]} {row[3]}"
                                del row[3] 
                            
                            table[0][2] = "Description" 
                            del table[0][3]
                            
                        df = pd.DataFrame(table[1:], columns=table[0])

                        df = df.iloc[:, :5]
                        while len(df.columns) < 5:
                            df[len(df.columns)] = "" 
                        

                        output_file = f"{output_dir}/table_page_{page_number+1}_table_{i+1}.csv"
                        df.to_csv(output_file, index=False)

            except Exception as e:
                print(f"Error on pathge {page_number+1}: {e}")

pdf_path = "825.0.3320.pdf"
output_dir = "output_tables"
extract_tables_(pdf_path, output_dir)

