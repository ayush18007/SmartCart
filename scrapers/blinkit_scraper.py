from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import time

load_dotenv(dotenv_path='../backend/.env')
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def check_cache(product_name, pincode):
    """Check if we have fresh data for this product+pincode"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT ph.price, ph.quantity, ph.scraped_at 
            FROM price_history ph
            JOIN products p ON ph.product_id = p.id
            WHERE p.name ILIKE :name 
            AND ph.pincode = :pincode
            AND ph.platform_id = 1
            AND ph.expires_at > NOW()
            LIMIT 1
        """), {"name": f"%{product_name}%", "pincode": pincode})
        return result.fetchone()

def save_to_database(results, pincode):
    """Save scraped results to database"""
    with engine.connect() as conn:
        for item in results:
            try:
                # Insert or get product
                conn.execute(text("""
                    INSERT INTO products (name, category)
                    VALUES (:name, 'grocery')
                    ON CONFLICT DO NOTHING
                """), {"name": item["name"]})

                product = conn.execute(text("""
                    SELECT id FROM products WHERE name = :name
                """), {"name": item["name"]}).fetchone()

                if product:
                    # Clean price - remove ₹ symbol
                    price_str = item["price"].replace("₹", "").replace(",", "").strip()
                    try:
                        price = float(price_str)
                    except:
                        price = 0.0

                    # Save price with 30 min expiry
                    expires_at = datetime.now() + timedelta(minutes=30)
                    
                    conn.execute(text("""
                        INSERT INTO price_history 
                        (product_id, platform_id, price, quantity, pincode, expires_at)
                        VALUES (:product_id, 1, :price, :quantity, :pincode, :expires_at)
                    """), {
                        "product_id": product[0],
                        "price": price,
                        "quantity": item["quantity"],
                        "pincode": pincode,
                        "expires_at": expires_at
                    })
                    print(f"💾 Saved: {item['name']} | ₹{price}")

            except Exception as e:
                print(f"DB error for {item['name']}: {e}")

        conn.commit()
        print("✅ All results saved to database!")

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

        browser.close()

    # Save to database
    if results:
        save_to_database(results, pincode)

    return results

if __name__ == "__main__":
    pincode = input("Enter your pincode: ")
    results = scrape_blinkit("amul butter", pincode)
    print(f"\n✅ Total results scraped and saved: {len(results)}")