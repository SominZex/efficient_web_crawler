import pandas as pd
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

def create_driver(retries=3, delay=5):
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1}/{retries} to create WebDriver...")
            
            service = Service(
                ChromeDriverManager().install(),
                service_args=["--verbose"],
                log_path="./chromedriver_debug.log" 
            )
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--remote-debugging-port=9222")
            
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(120)
            print("WebDriver created successfully.")
            return driver
        except Exception as e:
            print(f"Error creating WebDriver (Attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    
    raise Exception("Failed to create WebDriver after multiple attempts.")

def is_url_reachable(url, timeout=10):
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"URL check failed for {url}: {e}")
        return False

def extract_variant_links(product_url, driver):
    driver.get(product_url)
    time.sleep(5)

    variant_links = []
    try:
        print(f"Fetching page for: {product_url}")
        
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-varient-boxes"))
            )
        except TimeoutException:
            print(f"Timed out waiting for product variants on {product_url}")
            print(driver.page_source) 

        variant_boxes = driver.find_elements(By.CSS_SELECTOR, ".product-varient-boxes .variant-box")
        print(f"Found {len(variant_boxes)} variant boxes for {product_url}")

        for box in variant_boxes:
            variant_name = box.get_attribute("data-product")
            print(f"Extracted variant name: {variant_name}")
            if variant_name:
                variant_link = f"{product_url}?variant={variant_name}"
                variant_links.append(variant_link)
            else:
                print(f"Variant name not found for box: {box.text}")
                
    except Exception as e:
        print(f"Error extracting variant links from {product_url}: {e}")
    return variant_links

def extract_variant_links_with_retry(product_url, driver, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return extract_variant_links(product_url, driver)
        except Exception as e:
            print(f"Attempt {attempt + 1}/{retries} failed for {product_url}: {e}")
            time.sleep(delay * (attempt + 1))
    print(f"Failed to extract variant links for {product_url} after {retries} attempts.")
    return []

def main():
    input_csv = "./starquik_links/frozen.csv"
    output_csv = "frozen_variant_links_vt.csv"

    product_df = pd.read_csv(input_csv)
    product_links = product_df["Link"].tolist()

    driver = create_driver()
    all_variant_links = []

    try:
        for product_url in product_links:
            if not is_url_reachable(product_url):
                print(f"URL not reachable: {product_url}")
                continue
            print(f"Extracting variants for: {product_url}")
            variant_links = extract_variant_links_with_retry(product_url, driver)
            for variant_link in variant_links:
                all_variant_links.append({"Product Link": product_url, "Variant Link": variant_link})
    finally:
        driver.quit()

    print("Saving variant links to CSV.")
    variant_df = pd.DataFrame(all_variant_links)
    variant_df.to_csv(output_csv, index=False)
    print(f"Variant links saved to {output_csv}.")

if __name__ == "__main__":
    main()
    