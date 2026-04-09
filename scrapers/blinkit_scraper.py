from playwright.sync_api import sync_playwright
import time

def scrape_blinkit(product_name, pincode):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"🔍 Searching Blinkit for: {product_name} in pincode: {pincode}")
        page.goto("https://blinkit.com")
        time.sleep(4)

        # Handle location popup
        try:
            location_input = page.locator('input[placeholder="search delivery location"]').first
            location_input.click()
            location_input.fill(pincode)
            print(f"✅ Entered pincode: {pincode}")
            time.sleep(4)

            suggestion = page.get_by_text(pincode).first
            if suggestion.is_visible():
                suggestion.click()
                print("✅ Location selected!")
            time.sleep(4)

        except Exception as e:
            print(f"Location error: {e}")

        # Navigate directly to search URL
        try:
            search_query = product_name.replace(" ", "%20")
            page.goto(f"https://blinkit.com/s/?q={search_query}")
            print(f"✅ Navigated to search page!")
            time.sleep(5)
        except Exception as e:
            print(f"Search error: {e}")

        # Extract using exact class names from HTML
        try:
            name_elements = page.locator('.tw-text-300.tw-font-semibold.tw-line-clamp-2').all()
            price_elements = page.locator('.tw-text-200.tw-font-semibold').all()
            quantity_elements = page.locator('.tw-text-200.tw-font-medium.tw-line-clamp-1').all()

            print(f"Found {len(name_elements)} products")

            for i in range(min(5, len(name_elements))):
                try:
                    name = name_elements[i].inner_text().strip()
                    price = price_elements[i].inner_text().strip() if i < len(price_elements) else "N/A"
                    quantity = quantity_elements[i].inner_text().strip() if i < len(quantity_elements) else "N/A"

                    # Skip if name is empty or it's a header
                    if not name or "Showing" in name:
                        continue

                    result = {
                        "name": name,
                        "price": price,
                        "quantity": quantity,
                        "platform": "Blinkit",
                        "pincode": pincode
                    }
                    results.append(result)
                    print(f"📦 {name} | {quantity} | {price}")

                except Exception as e:
                    print(f"Error extracting item {i}: {e}")

        except Exception as e:
            print(f"Extraction error: {e}")

        page.screenshot(path="blinkit_results.png")
        print("📸 Screenshot saved!")
        input("Press Enter to close browser...")
        browser.close()

    return results

if __name__ == "__main__":
    pincode = input("Enter your pincode: ")
    results = scrape_blinkit("amul butter", pincode)
    print(f"\n✅ Total results: {len(results)}")
    for r in results:
        print(r)