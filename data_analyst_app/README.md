# Data Analyst API

A FastAPI-based service for automated data analysis and insights generation.

## Features

- **Data Cleaning**: Automatic cleaning of CSV, Excel, and JSON files
- **Statistical Analysis**: Automated profiling of columns (numeric, categorical, datetime)
- **Insight Generation**: Detects outliers, distribution patterns, correlations, and more
- **Type Inference**: Smart detection of column types beyond basic pandas dtypes

## Project Structure

```
data_analyst_app/
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration (not in git)
├── app/
│   ├── routes/
│   │   └── upload.py        # Upload and analysis endpoint
│   ├── services/
│   │   ├── cleaner.py       # Data cleaning logic
│   │   └── inference.py     # Statistical analysis engine
│   └── utils/
│       └── file_handler.py  # File validation and storage
└── uploads/                 # Temporary file storage
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Usage

### Start the server:
```bash
python main.py
# Or with uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Upload and analyze data:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_data.csv"
```

### API Endpoints

- `POST /api/upload` - Upload a file and get analysis results
- `GET /` - API information
- `GET /health` - Health check

## Supported File Formats

- CSV (.csv)
- Excel (.xlsx, .xls)
- JSON (.json)

## Analysis Features

### Column Profiling
- Automatic type detection (numeric, categorical, datetime)
- Smart categorization of numeric columns with few unique values
- Date parsing from string columns

### Numeric Analysis
- Descriptive statistics (mean, median, std, min, max)
- Distribution shape analysis (skewness)
- Outlier detection using IQR method
- Normality testing (Shapiro-Wilk, D'Agostino-Pearson)

### Categorical Analysis
- Dominant category detection
- Cardinality ratio calculation
- Imbalance detection

### Datetime Analysis
- Temporal range analysis
- Missing date detection

### Relationship Analysis
- Pearson correlation between numeric columns
- Statistical significance testing
- Strength classification (weak, moderate, strong)

## Configuration

Edit `.env` to configure:
- `MAX_FILE_SIZE` - Maximum upload size (default: 10MB)
- `ALLOWED_EXTENSIONS` - Accepted file types
- `UPLOAD_DIR` - Temporary storage directory
- `LOG_LEVEL` - Logging verbosity

## Development

The codebase follows a clean architecture:
- **Routes**: Handle HTTP requests and responses
- **Services**: Business logic (cleaning, analysis)
- **Utils**: Helper functions (file handling)

## License

MIT
