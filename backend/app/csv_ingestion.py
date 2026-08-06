from __future__ import annotations
import pandas as pd

def _format_value(value) -> str:
    if pd.isna(value):
        return "<missing>"
    return str(value)

def row_to_text(row_number: int, row: pd.Series) -> str:
    pairs = [f"{column}: {_format_value(value)}" for column, value in row.items()]
    return f"Row: {row_number}: " + "; ".join(pairs)

def process_csv_into_chunks(file_path: str):
    df = pd.read_csv(file_path)
    chunks = []
    
    overview = f"""
    CSV Dataset Overview
    Rows: {len(df)}
    Columns: {len(df.columns)}
    
    Column Names:
    {",".join(df.columns)}
    """.strip()
    
    chunks.append({
        "section": "overview",
        "text": overview,
        "token_count": len(overview.split())
    })
    
    missing_values = df.isnull().sum()
    missing_text = "Missing Value Report:\n"
    
    for column, count in missing_values.items():
        missing_text += f"{column} has {count} missing values\n"
        
        chunks.append({
            "section": "missing_values",
            "text": missing_text.strip(),
            "token_count": len(missing_text.split())
        })
    
    numeric_columns = df.select_dtypes(include="number").columns
    if len(numeric_columns) > 0:
        numeric_summary = df.describe().to_string()
        numeric_text = f"""
        Numeric Column Summary:
        {numeric_summary}
        """.strip()
    
        chunks.append({
            "section": "numeric_summary",
            "text": numeric_text,
            "token_count": len(numeric_text.split())
        })
    
    categorical_columns = df.select_dtypes(include=["object", "string", "category"]).columns
    for column in categorical_columns:
        value_counts = df[column].value_counts(dropna=False).head(10).to_string()
        text = f"""
        Categorical Column Summary:
        Column: {column}
        
        Top Values: {value_counts}
        """.strip()
    
        chunks.append({
            "section": "categorical_summary",
            "text": text,
            "token_count": len(text.split())
        })
    
    row_batch_size = 25
    for start in range(0, len(df), row_batch_size):
        batch = df.iloc[start:start+row_batch_size]
        row_lines = [row_to_text(index+1, row) for index, row in batch.iterrows()]
        
        text = "CSV Row Records (complete rows; use these to answer questions involving relationships between columns):\n"
        text += "\n".join(row_lines)
        
        chunks.append({
            "section": "row_records",
            "text": text,
            "token_count": len(text.split())
        })
    
    return chunks
