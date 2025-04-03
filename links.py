import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

csv_directory = "./starquik_links"

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")

def create_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_product_details(driver, product_url):
    try:
        driver.get(product_url)
        print(f"Loaded URL: {product_url}")

        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tabs__item"))
        )

        product_info_tab = driver.find_element(By.XPATH, "//li[@title='Product Information']")
        product_info_tab.click()
        print("Clicked on 'Product Information' tab.")

        WebDriverWait(driver, 45).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "tabs__content"))
        )

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        product_name = soup.find(class_="product-name")
        product_name = product_name.text.strip() if product_name else "N/A"

        current_price = soup.find(class_="product-detail-price")
        current_price = re.search(r"[\d,]+(?:\.\d+)?", current_price.text.strip()) if current_price else None
        current_price = current_price.group(0) if current_price else "N/A"

        cancelled_price = soup.find(class_="product-detail-cancelled-price")
        cancelled_price = re.search(r"[\d,]+(?:\.\d+)?", cancelled_price.text.strip()) if cancelled_price else None
        cancelled_price = cancelled_price.group(0) if cancelled_price else "N/A"

        image_element = soup.find(class_="product-discount-img-text")
        image_url = image_element.find("img")["src"] if image_element and image_element.find("img") else "N/A"

        active_tab = soup.find("div", {"class": "tabs__content tabs__content--active"})
        ean_list = []
        if active_tab:
            description = active_tab.find(class_="tabs__description")
            if description:
                ean_matches = re.findall(r"EAN:\s*([\d,\s]+)", description.text)
                if ean_matches:
                    ean_text = ean_matches[0]
                    ean_list = [ean.strip() for ean in ean_text.split(",") if ean.strip().isdigit()]
            print(f"Extracted EANs: {', '.join(ean_list) if ean_list else 'None'}")
        else:
            print("Product Information content not found.")

        return {
            "Product Name": product_name,
            "Current Price": current_price,
            "Cancelled Price": cancelled_price,
            "Image URL": image_url,
            "EAN": ", ".join(ean_list) if ean_list else "N/A",
        }

    except Exception as e:
        print(f"Error processing URL {product_url}: {e}")
        return {
            "Product Name": "N/A",
            "Current Price": "N/A",
            "Cancelled Price": "N/A",
            "Image URL": "N/A",
            "EAN": "N/A",
        }

def main():
    driver = create_driver()
    output_data = []

    try:
        for csv_file in os.listdir(csv_directory):
            if csv_file.endswith(".csv"):
                print(f"Processing file: {csv_file}")
                df = pd.read_csv(os.path.join(csv_directory, csv_file))

                for index, row in df.iterrows():
                    product_url = row["Link"]
                    print(f"Fetching details for: {product_url}")
                    product_details = extract_product_details(driver, product_url)
                    product_details["Source File"] = csv_file
                    output_data.append(product_details)
    finally:
        driver.quit()

    output_df = pd.DataFrame(output_data)

    if "EAN" in output_df.columns:
        output_df["EAN"] = output_df["EAN"].astype(str)

    output_df.to_csv("frozen_variants_detailss.csv", index=False)
    print("Data extraction completed. File saved.")

if __name__ == "__main__":
    main()
