import pandas as pd
import os
import shutil

source_image_dir = "/home/cicada3301/Documents/blinkit_scrap/product_images/product_images"
destination_image_dir = "/home/cicada3301/Documents/blinkit_scrap/renamed_images"
csv_dir = "/home/cicada3301/Documents/blinkit_scrap/data_cleaning/filtered_data.csv"

os.makedirs(destination_image_dir, exist_ok=True)

master_data = pd.read_csv(csv_dir)
image_files = os.listdir(source_image_dir)

def match_and_copy_images(row):
    product_name = row['Product Name'].lower()
    master_id = row['master_id']
    matched_images = []
    
    print(f"Matching for: {product_name}")
    
    for image_file in image_files:
        if product_name in image_file.lower():
            matched_images.append(image_file)

    if not matched_images:
        print(f"No images found for: {product_name}")
        return "" 
    
    renamed_images = []
    for idx, image_file in enumerate(matched_images, start=1):
        ext = os.path.splitext(image_file)[1] 
        new_name = f"{master_id}_{idx}{ext}"
        source_path = os.path.join(source_image_dir, image_file)
        destination_path = os.path.join(destination_image_dir, new_name)
        
        if os.path.exists(source_path):
            shutil.copy(source_path, destination_path) 
            renamed_images.append(destination_path) 
            print(f"Copied and renamed: {source_path} -> {destination_path}")
        else:
            print(f"File not found: {source_path}")

    return ";".join(renamed_images)

master_data['image_dir'] = master_data.apply(match_and_copy_images, axis=1)

output_csv_path = "updated_products_with_images.csv"
master_data.to_csv(output_csv_path, index=False)

print(f"Image copying, renaming, and CSV update completed. Output saved to {output_csv_path}.")
