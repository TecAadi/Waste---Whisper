import os
import shutil

source = "RealWaste"
destination = "combined_dataset"

# Source folder -> New category
mapping = {
    "Cardboard": "Paper",
    "Paper": "Paper",

    "Food Organics": "Food Organics",
    "Vegetation": "Food Organics",

    "Textile Trash": "Miscellaneous Trash",
    "Miscellaneous Trash": "Miscellaneous Trash",

    "Glass": "Glass",
    "Metal": "Metal",
    "Plastic": "Plastic"
}

# Create destination folder
os.makedirs(destination, exist_ok=True)

for old_class, new_class in mapping.items():

    source_folder = os.path.join(source, old_class)
    destination_folder = os.path.join(destination, new_class)

    os.makedirs(destination_folder, exist_ok=True)

    if not os.path.exists(source_folder):
        print(f"Not found: {source_folder}")
        continue

    for filename in os.listdir(source_folder):

        source_file = os.path.join(source_folder, filename)

        destination_file = os.path.join(
            destination_folder,
            f"{old_class}_{filename}"
        )

        if os.path.isfile(source_file):
            shutil.copy2(
                source_file,
                destination_file
            )

    print(f"{old_class} -> {new_class}")

print("\nDataset combination completed!")