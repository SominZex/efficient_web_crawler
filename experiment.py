from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd

chrome_driver_path = '/root/.wdm/drivers/chromedriver/linux64/131.0.6778.87/chromedriver-linux64/chromedriver'

service = Service(chrome_driver_path)

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=service, options=options)
driver.get("https://www.starquik.com/category/branded-food")

time.sleep(5)

product_links = []
soup = BeautifulSoup(driver.page_source, "html.parser")
product_cards = soup.find_all("div", class_="product-card-container")
for card in product_cards:
    link_tag = card.find("a", href=True)
    if link_tag:
        product_links.append("https://www.starquik.com" + link_tag["href"])

all_product_details = []

for link in product_links:
    driver.get(link)
    time.sleep(2)
    
    product_soup = BeautifulSoup(driver.page_source, "html.parser")
    
    try:
        name = product_soup.find("h1", class_="product-name").text.strip()
    except:
        name = None
    
    try:
        image = product_soup.find("div", class_="product-card-container-image").find("img")["src"]
    except:
        image = None

    try:
        price = product_soup.find("div", class_="product-detail-price").text.strip()
    except:
        price = None

    try:
        cancelled_price = product_soup.find("span", class_="product-detail-cancelled-price").text.strip()
    except:
        cancelled_price = None

    try:
        variants = [variant.text.strip() for variant in product_soup.find_all("div", class_="variant-box")]
    except:
        variants = None

    try:
        ean = product_soup.find("div", class_="tabs__description").text.strip()
        ean_number = ean.split("EAN:")[1].split(",")[0].strip()
    except:
        ean_number = None

    all_product_details.append({
        "Name": name,
        "Link": link,
        "Image": image,
        "Price": price,
        "Cancelled Price": cancelled_price,
        "Variants": variants,
        "EAN": ean_number,
    })

driver.quit()

df = pd.DataFrame(all_product_details)
df.to_csv("starquik_products_1.csv", index=False)

print("Dump complete! Data saved to starquik_products.csv")
