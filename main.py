import pdfplumber
import pandas as pd
from tqdm import tqdm

def extract_tables_(pdf_path, output_dir):
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(tqdm(pdf.pages, desc="Processing Pages")):
            try:
                tables = page.extract_tables(table_settings={"vertical_strategy": "text", "horizontal_strategy": "lines_strict"})
                if tables:
                    for i, table in enumerate(tables):
                        print(f"Table {i+1}:")
                        for row in table:
                            print(row)
                        # df = pd.DataFrame(table[1:], columns=table[0])
                        # output_file = f"{output_dir}/table_page_{page_number+1}_table_{i+1}.csv"
                        # df.to_csv(output_file, index=False)
            except Exception as e:
                print(f"Error on page {page_number+1}: {e}")

pdf_path = "825.0.3320_ETK_1.0_en.pdf"
output_dir = "output_tables"
extract_tables_(pdf_path, output_dir)