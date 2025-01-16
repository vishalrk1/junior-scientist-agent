import os
from pathlib import Path
import pandas as pd

def dataframe_validator(df_path: str) -> pd.DataFrame:
    if not df_path.lower().endswith('.csv'):
        raise ValueError("Only CSV files are supported as of now.")
    
    if not os.path.exists(df_path):
        raise FileNotFoundError(f"The file {df_path} does not exist.")
    
    return pd.read_csv(df_path)