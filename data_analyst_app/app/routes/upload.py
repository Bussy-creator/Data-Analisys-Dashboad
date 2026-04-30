from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging
import os

from app.services.cleaner import DataCleaner
from app.services.inference import InferenceEngine
from app.utils.file_handler import FileHandler

logger = logging.getLogger(__name__)

router = APIRouter()
file_handler = FileHandler(upload_dir="uploads")


@router.post("/upload")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Upload a data file (CSV, Excel, JSON), clean it, and analyze it.
    
    Returns:
        JSON response with analysis results
    """
    temp_file_path = None
    
    try:
        # Save uploaded file
        temp_file_path = await file_handler.save_file(file)
        logger.info(f"File uploaded: {file.filename} -> {temp_file_path}")
        
        # Clean the data
        cleaner = DataCleaner()
        df = cleaner.clean_data(temp_file_path)
        
        if df is None:
            raise HTTPException(status_code=400, detail="Failed to clean data")
        
        logger.info(f"Data cleaned. Shape: {df.shape}")
        
        # Run inference analysis
        engine = InferenceEngine(df)
        results = engine.run()
        
        logger.info(f"Analysis complete. Found {results['insight_count']} insights")
        
        # Clean up temporary file
        file_handler.delete_file(temp_file_path)
        
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "results": results
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        
        # Clean up temporary file if it exists
        if temp_file_path:
            file_handler.delete_file(temp_file_path)
        
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "data-analyst-api"}
