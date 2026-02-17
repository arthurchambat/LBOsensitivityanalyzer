"""
CSV Financial Data Ingestion Module

Handles uploading, validation, and normalization of historical financial data.
"""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import io


class FinancialDataIngestion:
    """
    Handles CSV ingestion and validation for historical financials.
    """
    
    REQUIRED_COLUMNS = ['year', 'revenue', 'ebitda']
    OPTIONAL_COLUMNS = ['capex', 'netdebt']
    
    def __init__(self):
        """Initialize the ingestion handler."""
        self.warnings: List[str] = []
        self.data: pd.DataFrame = None
    
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names: lowercase, strip spaces, remove special chars.
        
        Args:
            df: Raw DataFrame
        
        Returns:
            DataFrame with normalized column names
        """
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df
    
    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-detect column mappings (case-insensitive, flexible naming).
        
        Args:
            df: DataFrame with normalized columns
        
        Returns:
            Dictionary mapping standard names to actual column names
        """
        column_map = {}
        
        for col in df.columns:
            # Year detection
            if any(term in col for term in ['year', 'yr', 'date', 'period']):
                column_map['year'] = col
            # Revenue detection
            elif any(term in col for term in ['revenue', 'sales', 'turnover']):
                column_map['revenue'] = col
            # EBITDA detection
            elif 'ebitda' in col:
                column_map['ebitda'] = col
            # Capex detection
            elif 'capex' in col or 'capital_expenditure' in col:
                column_map['capex'] = col
            # Net Debt detection
            elif 'netdebt' in col or 'net_debt' in col:
                column_map['netdebt'] = col
        
        return column_map
    
    def validate_data(self, df: pd.DataFrame, column_map: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate the financial data.
        
        Args:
            df: DataFrame to validate
            column_map: Column name mappings
        
        Returns:
            (is_valid, list_of_warnings)
        """
        warnings = []
        is_valid = True
        
        # Check required columns
        for required in self.REQUIRED_COLUMNS:
            if required not in column_map:
                warnings.append(f"❌ CRITICAL: Missing required column '{required}'")
                is_valid = False
        
        if not is_valid:
            return False, warnings
        
        # Check minimum data points
        if len(df) < 3:
            warnings.append("⚠️ Less than 3 years of data. Analysis may be unreliable.")
        
        # Validate year column
        year_col = column_map['year']
        try:
            years = pd.to_numeric(df[year_col], errors='coerce')
            if years.isna().any():
                warnings.append(f"⚠️ Non-numeric values in '{year_col}' column")
                is_valid = False
            else:
                # Check for sequential years
                year_diffs = years.diff().dropna()
                if not all(year_diffs == 1):
                    warnings.append("⚠️ Years are not sequential. Gaps detected.")
        except Exception as e:
            warnings.append(f"❌ Error processing year column: {str(e)}")
            is_valid = False
        
        # Validate numeric columns
        for col in ['revenue', 'ebitda']:
            if col in column_map:
                actual_col = column_map[col]
                try:
                    numeric_values = pd.to_numeric(df[actual_col], errors='coerce')
                    
                    if numeric_values.isna().any():
                        nan_count = numeric_values.isna().sum()
                        warnings.append(f"⚠️ {nan_count} non-numeric values in '{actual_col}'")
                        is_valid = False
                    
                    # Check for negative EBITDA
                    if col == 'ebitda' and (numeric_values < 0).any():
                        warnings.append("⚠️ Negative EBITDA values detected")
                    
                    # Check for zero values
                    if (numeric_values == 0).any():
                        warnings.append(f"⚠️ Zero values detected in '{actual_col}'")
                    
                    # Check for extreme outliers (>5x median)
                    if len(numeric_values) > 0:
                        median_val = numeric_values.median()
                        if median_val > 0:
                            outliers = numeric_values > (5 * median_val)
                            if outliers.any():
                                warnings.append(f"⚠️ Potential outliers detected in '{actual_col}'")
                
                except Exception as e:
                    warnings.append(f"❌ Error validating '{actual_col}': {str(e)}")
                    is_valid = False
        
        return is_valid, warnings
    
    def clean_data(self, df: pd.DataFrame, column_map: Dict[str, str]) -> pd.DataFrame:
        """
        Clean and standardize the data.
        
        Args:
            df: Raw DataFrame
            column_map: Column mappings
        
        Returns:
            Cleaned DataFrame with standard column names
        """
        cleaned = pd.DataFrame()
        
        # Rename columns to standard names
        for standard_name, actual_col in column_map.items():
            if standard_name in self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS:
                cleaned[standard_name] = pd.to_numeric(df[actual_col], errors='coerce')
        
        # Sort by year
        if 'year' in cleaned.columns:
            cleaned = cleaned.sort_values('year').reset_index(drop=True)
        
        # Drop rows with missing required data
        cleaned = cleaned.dropna(subset=['year', 'revenue', 'ebitda'])
        
        return cleaned
    
    def ingest_csv(self, csv_file) -> Tuple[pd.DataFrame, List[str]]:
        """
        Main ingestion pipeline.
        
        Args:
            csv_file: Uploaded CSV file (Streamlit UploadedFile object or file path)
        
        Returns:
            (cleaned_dataframe, list_of_warnings)
        """
        try:
            # Read CSV
            if hasattr(csv_file, 'read'):
                # Streamlit UploadedFile
                df = pd.read_csv(csv_file)
            else:
                # File path
                df = pd.read_csv(csv_file)
            
            # Drop unnamed columns (index columns from exported CSVs)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Normalize column names
            df = self.normalize_column_names(df)
            
            # Detect columns
            column_map = self.detect_columns(df)
            
            # Validate
            is_valid, warnings = self.validate_data(df, column_map)
            
            if not is_valid:
                return None, warnings
            
            # Clean
            cleaned_df = self.clean_data(df, column_map)
            
            self.data = cleaned_df
            self.warnings = warnings
            
            return cleaned_df, warnings
        
        except Exception as e:
            error_msg = f"❌ CRITICAL: Failed to read CSV: {str(e)}"
            return None, [error_msg]
    
    def get_latest_metrics(self) -> Dict[str, float]:
        """
        Get most recent year metrics.
        
        Returns:
            Dictionary with latest year's financials
        """
        if self.data is None or len(self.data) == 0:
            return {}
        
        latest = self.data.iloc[-1]
        
        return {
            'latest_year': latest['year'],
            'latest_revenue': latest['revenue'],
            'latest_ebitda': latest['ebitda'],
            'latest_margin': (latest['ebitda'] / latest['revenue'] * 100) if latest['revenue'] > 0 else 0
        }


def create_sample_csv() -> str:
    """
    Create a sample CSV string for testing/demo.
    
    Returns:
        CSV string
    """
    sample_data = """Year,Revenue,EBITDA,Capex,NetDebt
2019,100.0,15.0,5.0,30.0
2020,108.0,17.0,5.5,28.0
2021,120.0,20.0,6.0,25.0
2022,135.0,24.0,7.0,22.0
2023,145.0,27.0,7.5,20.0"""
    
    return sample_data


def get_sample_dataframe() -> pd.DataFrame:
    """
    Get a sample DataFrame for testing.
    
    Returns:
        Sample DataFrame with normalized columns
    """
    sample_csv = create_sample_csv()
    df = pd.read_csv(io.StringIO(sample_csv))
    
    # Normalize column names to lowercase
    df.columns = df.columns.str.strip().str.lower()
    
    return df
