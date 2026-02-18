# utils/excel_handler.py
"""
Excel export utilities
"""
import pandas as pd
from io import BytesIO
from typing import List, Dict, Optional

def convert_to_excel(data: List[Dict], sheet_name: str = "Data") -> Optional[BytesIO]:
    """Convert list of dictionaries to Excel file"""
    try:
        if not data:
            return None
        
        output = BytesIO()
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error creating Excel file: {e}")
        return None

def convert_multiple_sheets_to_excel(data_dict: Dict[str, List[Dict]]) -> Optional[BytesIO]:
    """Convert multiple data sets to Excel with multiple sheets"""
    try:
        if not data_dict:
            return None
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, data in data_dict.items():
                if data:
                    df = pd.DataFrame(data)
                    df.to_excel(writer, index=False, sheet_name=sheet_name[:31])  # Excel sheet name limit
        
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error creating Excel file: {e}")
        return None