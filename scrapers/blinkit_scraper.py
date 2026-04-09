from playwright.sync_api import sync_playwright
import time

def scrape_blinkit(product_name):
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print(f"Opening Blinkit to search for: {product_name}")
        page.goto("https://blinkit.com")
        
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Take a screenshot to see what loaded
        page.screenshot(path="blinkit_home.png")
        print("Screenshot saved!")
        
        input("Press Enter to close browser...")
        browser.close()
    
    return results

if __name__ == "__main__":
    scrape_blinkit("amul butter")