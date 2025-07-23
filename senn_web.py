from playwright.sync_api import sync_playwright
import pandas as pd
import subprocess
import os
from io import BytesIO

def ensure_playwright_browser_installed():
    chromium_dir = os.path.expanduser("~/.cache/ms-playwright/chromium-1124")
    if not os.path.exists(chromium_dir):
        try:
            subprocess.run(["playwright", "install", "chromium"], check=True)
        except Exception as e:
            print("Error installing Chromium:", e)

ensure_playwright_browser_installed()

def check_cred(user, pswd):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set to True for deployment
        page = browser.new_page()
        try:
            page.goto("https://eportalsen.eetcld.com/login")
            page.fill('input[name="Username"]', user)
            page.fill('input[name="Password"]', pswd)
            page.click('.login-button')
            page.wait_for_timeout(3000)
            # Check for common error indicators
            error_selectors = [
                'text=Invalid username or password',
                'text=Login failed',
                '.error-message',
                '.alert-danger'
            ]
            for selector in error_selectors:
                if page.is_visible(selector):
                    return False
            # If no errors and not on login page, assume success
            return page.url != "https://eportalsen.eetcld.com/login?returnurl=%2F"
        finally:
            browser.close()
# output a file
def highlight_not_found(row):
    if row['Status'] == 'Not Found':
        return ['background-color: yellow'] * len(row)
    return [''] * len(row)
def add_info(file, username, password):
    df = pd.read_excel(file)
    df['Status'] = ''
    df['SKU'] = ''
    df['Description'] = ''
    df['List Price'] = ''
    df['Qty in Stock'] = ''
    df['Weight'] = ''
    df['Height'] = ''
    df['Width'] = ''
    df['Length'] = ''
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set to True for deployment
        page = browser.new_page()
        try:
            page.goto("https://eportalsen.eetcld.com/login")
            page.fill('input[name="Username"]', username)
            page.fill('input[name="Password"]', password)
            page.click('.login-button')
            page.wait_for_timeout(3000)
            print(df)
            for _, row in df.iterrows():
                item = str(row["No./\nIdent."]).zfill(6)
                try:
                    page.fill('input[name="q"]', item)
                    page.click('button[type="submit"]')
                    page.wait_for_timeout(3000)
                    if page.locator("text=No products were found that matched your criteria.").is_visible():
                        df.loc[row.name, 'Status'] = 'Not Found'
                        continue

                    df.loc[row.name, 'SKU'] = page.locator('[id^="sku-"]').evaluate("el => el.textContent")
                    df.loc[row.name, 'Description'] = page.locator('.uppercase.title > b').evaluate("el => el.textContent")
                    df.loc[row.name, 'Weight'] = page.locator('span[orig-size="16px"]:has-text("kg")').evaluate("el => el.textContent")
                    df.loc[row.name, 'Height'] = page.locator('p:has(span:has-text("Height")) span:nth-of-type(2)').evaluate("el => el.textContent") 
                    df.loc[row.name, 'Width'] = page.locator('p:has(span:has-text("Width")) span:nth-of-type(2)').evaluate("el => el.textContent")
                    df.loc[row.name, 'Length'] = page.locator('p:has(span:has-text("Length")) span:nth-of-type(2)').evaluate("el => el.textContent")
                    df.loc[row.name, 'List Price'] = page.locator('span[orig-size="22px"]:has-text("$")').evaluate("el => el.textContent.replace('$', '')")
                    df.loc[row.name, 'Qty in Stock'] = page.locator('span.value.green').evaluate("el => el.textContent.split(' ')[0]")

                except:
                    pass
        except Exception as e:
            print(e)
        finally:
            browser.close()
    styled_df = df.style.apply(highlight_not_found, axis=1)
    output_stream = BytesIO()
    with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
        styled_df.to_excel(writer, index=False, sheet_name='Combined Output')
    output_stream.seek(0)
    return output_stream
# add things to a shopping cart
def add_to_cart(file, username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set to True for deployment
        page = browser.new_page()
        output = {}
        try:
            df = pd.read_excel(file)
            page.goto("https://eportalsen.eetcld.com/login")
            page.fill('input[name="Username"]', username)
            page.fill('input[name="Password"]', password)
            page.click('.login-button')
            page.wait_for_timeout(3000)

            for _, row in df.iterrows():
                item = str(row["No./\nIdent."]).zfill(6)
                print(item)
                number = row["Qty./\nMenge."]
                try:
                    page.fill('input[name="q"]', item)
                    page.click('button[type="submit"]')
                    page.wait_for_timeout(3000)
                    if page.locator("text=No products were found that matched your criteria.").is_visible():
                        output[item] = "Item was not found"
                        continue
                    if int(page.text_content('[id^="stock-availability-value-"]').split()[0]) >= number:
                        page.click('.add-to-cart-button')
                        number -= 1
                        page.wait_for_timeout(3000)
                        while number > 0:
                            page.click('.increaseQty')
                            page.wait_for_timeout(500)
                            number -= 1
                    else:
                        output[item] = f'''Not enough stock, there is {int(page.text_content('[id^="stock-availability-value-"]').split()[0])} in stock, and {number} is needed.'''
                except Exception as e:
                    output[item] = f"Error processing item: {str(e)}"
        except Exception as e:
            output["general_error"] = f"General error: {str(e)}"
        finally:
            browser.close()
        return output