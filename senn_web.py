from playwright.sync_api import sync_playwright
import pandas as pd
import subprocess
import os

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
            for _, row in df:
                item = row["No./\nIdent."]
                try:
                    page.fill('input[name="q"]', item)
                    page.click('button[type="submit"]')
                    if page.is_visible("No products were found that matched your criteria."):
                        df.loc[row.name, 'Status'] = 'Not Found'
                        continue
                    row['SKU'] = page.text_content('[id^="sku-"]')
                    row['Description'] = page.text_content('.uppercase title').title()
                    row['Weight'] = page.text_content('span[orig-size="16px"]:has-text("kg")')
                    row['Height'] = page.text_content('span[orig-size="16px"]:has-text("feet"):nth-of-type(1)')
                    row['Width'] = page.text_content('span[orig-size="16px"]:has-text("feet"):nth-of-type(2)')
                    row['Length'] = page.text_content('span[orig-size="16px"]:has-text("feet"):nth-of-type(3)')
                except:
                    pass
        except:
            print("somthing")
        finally:
            browser.close()
    styled_df = df.style.apply(highlight_not_found, axis=1)

# add things to a shopping cart
def add_to_cart(file, username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for deployment
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