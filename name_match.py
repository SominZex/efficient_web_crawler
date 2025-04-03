import pandas as pd
from fuzzywuzzy import fuzz, process
import re

def clean_product_name(name):
    if isinstance(name, str):
        name = re.sub(r'[^a-zA-Z\s]', '', name).lower()
        return name.strip()
    return ""

blinkit = pd.read_csv('/home/cicada3301/Documents/blinkit_scrap/data_cleaning/merged_data.csv')
master = pd.read_csv('/home/cicada3301/Documents/blinkit_scrap/data_cleaning/filtered_data.csv')

blinkit['clean_product_name'] = blinkit['product_name'].apply(clean_product_name)
master['clean_product_name'] = master['Product Name'].apply(clean_product_name)

master_dict = {row['clean_product_name']: row['master_id'] for _, row in master.iterrows()}

def match_product_name(blinkit_name):
    blinkit_name_clean = clean_product_name(blinkit_name)
    
    match = process.extractOne(blinkit_name_clean, master_dict.keys(), scorer=fuzz.token_sort_ratio)
    
    if match:
        match_score = match[1]
        match_name = match[0]
        
        if match_score >= 85:
            return master_dict[match_name] 
    
    return None 

blinkit['master_id'] = blinkit['product_name'].apply(match_product_name)

blinkit = blinkit.drop(columns=['clean_product_name'])

blinkit.to_csv('matched_products.csv', index=False)

print("Matching complete. Check 'matched_products.csv' for the result.")
