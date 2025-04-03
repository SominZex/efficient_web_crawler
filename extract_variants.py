import pandas as pd
import time
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

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

def clean_pack_size(pack_size):
    pack_size = pack_size.lower().strip()

    pack_size = re.sub(r"(\d+)\s*g(m)?", r"\1g", pack_size)
    pack_size = re.sub(r"(\d+)\s*kg", r"\1kg", pack_size)
    pack_size = re.sub(r"(\d+)\s*ml", r"\1ml", pack_size)
    pack_size = re.sub(r"(\d+)\s*l", r"\1l", pack_size)
    pack_size = re.sub(r"(\d+)\s*pcs?", r"\1pcs", pack_size)

    return pack_size

def extract_product_base_name(product_url):
    base_name = product_url.split("/")[-1]
    base_name = re.sub(r"[-_](\d+(\.\d+)?(g|gm|kg|ml|ltr?|pcs)?)$", "", base_name, flags=re.IGNORECASE)
    base_name = re.sub(r"[-_]+", "-", base_name).strip("-").lower()
    return base_name

def has_variants(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-varient-boxes"))
        )
        return True
    except Exception:
        return False


def extract_product_name(driver):
    try:
        product_name = driver.find_element(By.CSS_SELECTOR, "h1.product-name span").text.strip()
        return product_name
    except NoSuchElementException:
        print("Error: Could not locate the product name element.")
        return None

def extract_base_name_until_digits(product_url):
    product_slug = product_url.split("/")[-1]
    match = re.search(r"\d", product_slug)
    if match:
        base_name = product_slug[:match.start()] 
    else:
        base_name = product_slug

    base_name = re.sub(r"[-_]+$", "", base_name).lower()
    return base_name



def extract_variant_links(product_url, driver):
    driver.get(product_url)
    time.sleep(5)

    variant_links = []
    try:
        base_product_name = extract_base_name_until_digits(product_url)
        if not base_product_name:
            print(f"Could not extract base product name for {product_url}")
            return []

        variant_boxes = driver.find_elements(By.CSS_SELECTOR, ".product-varient-boxes .variant-box")
        print(f"Found {len(variant_boxes)} variant boxes for {product_url}")

        for box in variant_boxes:
            try:
                pack_size = box.find_element(By.CSS_SELECTOR, "p").text.strip()
                cleaned_pack_size = clean_pack_size(pack_size)

                variant_link = f"https://www.starquik.com/product/{base_product_name}-{cleaned_pack_size}"

                if is_url_reachable(variant_link):
                    variant_links.append(variant_link)
                    print(f"Valid variant link: {variant_link}")
                else:
                    print(f"Invalid link skipped: {variant_link}")
            except Exception as e:
                print(f"Error processing variant box: {e}")
    except Exception as e:
        print(f"Error extracting variants for {product_url}: {e}")

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
    input_csv = "./starquik_links/home_care.csv"
    output_csv = "home_care_variants_links.csv"

    product_df = pd.read_csv(input_csv)
    product_links = product_df["Link"].tolist()

    driver = create_driver()
    all_variant_links = []

    try:
        for product_url in product_links:
            if not is_url_reachable(product_url):
                print(f"URL not reachable: {product_url}")
                continue

            print(f"Processing product: {product_url}")
            variant_links = extract_variant_links_with_retry(product_url, driver)
            for variant_link in variant_links:
                all_variant_links.append({"Product Link": product_url, "Variant Link": variant_link})
    finally:
        driver.quit()

    if all_variant_links:
        variant_df = pd.DataFrame(all_variant_links)
        variant_df.to_csv(output_csv, index=False)
        print(f"Variant links saved to {output_csv}.")
    else:
        print("No valid variant links found.")

if __name__ == "__main__":
    main()
