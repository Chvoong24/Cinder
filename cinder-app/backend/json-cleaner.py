import os
import glob

def clean_data_directory(directory):
    """
    Removes all JSON, macOS metadata files, and leftover GRIB2 files.
    """
    
    json_files = glob.glob(os.path.join(directory, "*.json"))
    
    
    macos_meta_files = [f for f in os.listdir(directory) if f.startswith("._")]

    
    grib_files = glob.glob(os.path.join(directory, "*.grib2"))

    all_files = (
        json_files +
        [os.path.join(directory, f) for f in macos_meta_files] +
        grib_files
    )

    if not all_files:
        print("Nothing to clean.")
        return

    for file_path in all_files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")
