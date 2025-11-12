import pandas as pd
import requests
import os
from io import BytesIO

def extract_datatourisme_places(
    dataset_url: str = "https://static.data.gouv.fr/resources/datatourisme-la-base-nationale-des-donnees-publiques-dinformation-touristique-en-open-data/20251112-034711/datatourisme-place.csv",
    output_filename: str = "datatourisme_places.csv"
):
    """ 
    Extract DataTourisme 'places' dataset and store it under data/raw/. 
    
    Args: 
        dataset_url (str): Direct link to the CSV file (from data.gouv.fr) 
        output_filename (str): Name for the local CSV file  
    Returns: 
        str: path to the saved file 
    """

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(root_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    output_path = os.path.join(raw_dir, output_filename)

    print(f"Downloading DataTourisme dataset from: {dataset_url}")
    response = requests.get(dataset_url, stream=True)
    response.raise_for_status()

    # Detect content type
    content_type = response.headers.get("Content-Type", "")
    print(f"Content-Type: {content_type}")

    # Quick check if this looks like HTML (error)
    if b"<html" in response.content[:500].lower():
        raise ValueError("The URL returned an HTML page, not a CSV. It may have expired or changed.")

    # Detect gzip by magic number
    df = pd.read_csv(BytesIO(response.content), sep=",", encoding="utf-8", dtype=str)

    # Keep relevant columns
    cols_to_keep = [
        "Nom_du_POI", "Categories_de_POI", "Latitude", "Longitude", "Adresse_postale",
        "Code_postal_et_commune", "Date_de_mise_a_jour", "Classements_du_POI", "Description"
    ]
    df = df[[c for c in cols_to_keep if c in df.columns]]

    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Saved {len(df)} records to {output_path}")
    return output_path


if __name__ == "__main__":
    extract_datatourisme_places()
