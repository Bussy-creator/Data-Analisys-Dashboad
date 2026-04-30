import pandas as pd
import numpy as np
from typing import Optional, Union, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_data(
    file_path: str,
    drop_na: bool = True,
    drop_duplicates: bool = True,
    na_threshold: float = 0.5,
    inplace: bool = False,
    encoding: str = 'utf-8',
    file_type: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Clean and preprocess data from a CSV or Excel file.
    
    Parameters:
    -----------
    file_path : str
        Path to the data file
    drop_na : bool, default=True
        Whether to drop rows with missing values
    drop_duplicates : bool, default=True
        Whether to drop duplicate rows
    na_threshold : float, default=0.5
        Drop columns with more than this fraction of missing values (0-1)
    inplace : bool, default=False
        If True, modify the dataframe in place
    encoding : str, default='utf-8'
        File encoding for CSV files
    file_type : str, optional
        Force file type ('csv', 'excel', 'json'). Auto-detected if None
    
    Returns:
    --------
    pd.DataFrame or None
        Cleaned dataframe, or None if an error occurs
    """
    try:
        # Detect file type if not specified
        if file_type is None:
            if file_path.endswith('.csv'):
                file_type = 'csv'
            elif file_path.endswith(('.xlsx', '.xls')):
                file_type = 'excel'
            elif file_path.endswith('.json'):
                file_type = 'json'
            else:
                file_type = 'csv'
        
        # Read the file
        logger.info(f"Reading {file_type} file: {file_path}")
        if file_type == 'csv':
            df = pd.read_csv(file_path, encoding=encoding)
        elif file_type == 'excel':
            df = pd.read_excel(file_path)
        elif file_type == 'json':
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        initial_rows = len(df)
        initial_cols = len(df.columns)
        logger.info(f"Initial shape: {initial_rows} rows, {initial_cols} columns")
        
        # Drop columns with too many missing values
        if na_threshold < 1.0:
            na_ratio = df.isna().sum() / len(df)
            cols_to_drop = na_ratio[na_ratio > na_threshold].index.tolist()
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
                logger.info(f"Dropped {len(cols_to_drop)} columns with >{na_threshold*100}% missing values")
        
        # Drop rows with missing values
        if drop_na:
            rows_before = len(df)
            df = df.dropna()
            rows_dropped = rows_before - len(df)
            logger.info(f"Dropped {rows_dropped} rows with missing values")
        
        # Drop duplicates
        if drop_duplicates:
            rows_before = len(df)
            df = df.drop_duplicates()
            rows_dropped = rows_before - len(df)
            logger.info(f"Dropped {rows_dropped} duplicate rows")
        
        # Convert common numeric columns that might be stored as strings
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]
        
        final_rows = len(df)
        final_cols = len(df.columns)
        
        logger.info(f"Final shape: {final_rows} rows, {final_cols} columns")
        logger.info(f"Total rows removed: {initial_rows - final_rows} ({(1 - final_rows/initial_rows)*100:.1f}%)")
        logger.info(f"Total columns removed: {initial_cols - final_cols}")
        
        return df
        
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"File is empty: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return None


# Backward compatibility alias
_Clean_Data = clean_data