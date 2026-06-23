import pandas as pd

def process_csv_into_chunks(file_path: str):
    df = pd.read_csv(file_path)
    chunks = []
    
    overview = f"""
    CSV Dataset Overview
    Rows: {len(df)}
    Columns: {len(df.columns)}
    
    Column Names:
    {",".join(df.columns)}
    """
    
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
        "text": missing_text,
        "token_count": len(missing_text.split())
    })
    
    numeric_summary = df.describe().to_string()
    numeric_text = f"""
    Numeric Column Summary:
    {numeric_summary}
    """
    
    chunks.append({
        "section": "numeric_summary",
        "text": numeric_text,
        "token_count": len(numeric_text.split())
    })
    
    categorical_columns = df.select_dtypes(include=["object"]).columns
    for column in categorical_columns:
        value_counts = df[column].value_counts().head(10).to_string()
        text = f"""
        Categorical Column Summary:
        Column: {column}
        
        Top Values: {value_counts}
        """
    
    chunks.append({
        "Section": "categorical_summary",
        "text": text,
        "token_count": len(text.split())
    })
    
    return chunks