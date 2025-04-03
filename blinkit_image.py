import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

csv_file = '/home/cicada3301/Documents/blinkit_scrap/trial_blinkit.csv'
df = pd.read_csv(csv_file)

image_dir = 'scraped_images'
os.makedirs(image_dir, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

def download_image(url, img_name):
    try:
        img_data = requests.get(url, headers=headers).content
        img_path = os.path.join(image_dir, img_name)
        
        with open(img_path, 'wb') as file:
            file.write(img_data)
        print(f"Downloaded: {img_name}")
    except Exception as e:
        print(f"Error downloading {img_name}: {e}")

def extract_images_from_url(product_url):
    try:
        response = requests.get(product_url, headers=headers)
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        carousel_section = soup.find('section', {'id': 'carousel-items'})
        if not carousel_section:
            print("No carousel section found.")
            return
        
        img_tags = carousel_section.find_all('img')
        
        product_id = product_url.split('/prn/')[1].split('/prid/')[1]
        
        for i, img_tag in enumerate(img_tags):
            img_url = img_tag.get('src')
            if img_url:
                img_url = urljoin(product_url, img_url)
                
                img_name = f"{product_id}_{i + 1}.jpg"
                
                download_image(img_url, img_name)
    
    except Exception as e:
        print(f"Error processing {product_url}: {e}")

for _, row in df.iterrows():
    product_url = row['product_url']
    print(f"Processing {product_url}...")
    extract_images_from_url(product_url)

print("Scraping complete!")
