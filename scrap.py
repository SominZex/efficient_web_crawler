import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from selenium.common.exceptions import TimeoutException

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-gpu")
options.add_argument("start-maximized")
options.add_argument("--disable-software-rasterizer")

prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2,
    "profile.managed_default_content_settings.javascript": 2,
}
options.add_experimental_option("prefs", prefs)

def create_driver(retries=3):
    for _ in range(retries):
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(120)
            return driver
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")
            time.sleep(5)
    raise Exception("Failed to start WebDriver after multiple attempts.")



def get_unique_filename(base_filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{base_filename}_{timestamp}.csv"
    
    counter = 1
    while os.path.exists(new_filename):
        new_filename = f"{base_filename}_{timestamp}_{counter}.csv"
        counter += 1
    
    return new_filename

driver = create_driver()

timeout = 120

driver.get("https://www.starquik.com/category/branded-food")

try:

    print("Starting WebDriverWait for product details.")

    WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.CLASS_NAME, ""))
    )
    print("Element 'product-details-inner-container' is visible!")

    while True:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        product_cards = soup.find_all("div", class_="product-card-container")
        for card in product_cards:
            link_tag = card.find("a", href=True)
            if link_tag:
                product_links.append("https://www.starquik.com" + link_tag["href"])

        driver.execute_script("window.scrollBy(0, 2000);")
        time.sleep(4)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

    all_product_details = []

    for link in product_links:
        try:
            driver.get(link)
            
            WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "product-detail-price"))
            )

            product_tabs = driver.find_elements(By.CSS_SELECTOR, "li.tabs__item")
            for tab in product_tabs:
                if tab.get_attribute("title") == "Product Information":
                    tab.click()
                    break
            time.sleep(2) 

            product_soup = BeautifulSoup(driver.page_source, "html.parser")

            name = product_soup.find("h1", class_="product-name").text.strip() if product_soup.find("h1", class_="product-name") else None
            image = product_soup.find("div", class_="product-card-container-image").find("img")["src"] if product_soup.find("div", class_="product-card-container-image") else None
            price = product_soup.find("div", class_="product-detail-price").text.strip() if product_soup.find("div", class_="product-detail-price") else None
            cancelled_price = product_soup.find("span", class_="product-detail-cancelled-price").text.strip() if product_soup.find("span", class_="product-detail-cancelled-price") else None

            ean_number = None
            ean_section = product_soup.find("div", id_="tab6")
            if ean_section:
                ean_text = ean_section.find("div", class_="tabs__description").text.strip()
                if "EAN:" in ean_text:
                    ean_text_split = ean_text.split("EAN:")[1]
                    ean_numbers = ean_text_split.split(",")
                    ean_number = [ean.strip() for ean in ean_numbers]

            all_product_details.append({
                "Name": name,
                "Link": link,
                "Image": image,
                "Price": price,
                "Cancelled Price": cancelled_price,
                "Variants": variants,
                "EAN": ean_number,
            })

        except TimeoutException as e:
            print(f"Timeout occurred for link: {link} - {e}")
            continue

finally:
    driver.quit()

filename = get_unique_filename("starquik_products")

df = pd.DataFrame(all_product_details)
df.to_csv(filename, index=False)

print(f"Dump complete! Data saved to {filename}")
