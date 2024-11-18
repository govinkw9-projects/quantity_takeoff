from fastapi import APIRouter, UploadFile, File, HTTPException
from models import LegendTemplate
from core.detection.legend.process_legend import detection_legend
from api.routes.utils import image_to_base64
from fastapi import Security, HTTPException, Depends
from core.apikey_auth import APIKeyAuth
from typing import Optional, List, Tuple
import os

router = APIRouter()


@router.post("/segment_legend", response_model=LegendTemplate)
async def get_images_from_legend(
    api_key: str = Depends(APIKeyAuth),
    file: UploadFile = File(
        ..., description="The Legend Template of Plans to be processed."
    ),
    method: str = None
) -> LegendTemplate:
    """
    Extracts symbols from a legend table image and processes it.

    This endpoint accepts an image file, and then processes the specified file
    to return a response based on the 'LegendTemplate' model.

    Args:
    - api_key (str): The API key for authentication, provided via header.
    - file (UploadFile): The Image file to be processed. The file is uploaded as multipart/form-data.


    Returns:
    - A JSON response with the status and processed data according to the 'LegendTemplate' model.

    Raises:
    - HTTPException: If processing fails or an invalid page number is provided.
    """

    symbols_generated = await detection_legend(file=file,
                                                    save_symbols_path="temp")
    all_symbols_base64 = [image_to_base64(symbol) for symbol in symbols_generated]

    return {"symbols_base64": all_symbols_base64}
