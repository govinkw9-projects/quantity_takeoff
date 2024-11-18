from fastapi import APIRouter, UploadFile, File, HTTPException
from models import PlanTemplate
from core.pdf_to_images.processpdf import process_pdf
from fastapi import Security, HTTPException, Depends
from core.apikey_auth import APIKeyAuth
from typing import Optional, List, Tuple


router = APIRouter()


@router.post("/process_plan", response_model=PlanTemplate)
async def get_images_from_pdf(
    api_key: str = Depends(APIKeyAuth),
    file: UploadFile = File(..., description="The PDF file of Plans to be processed."),
    page_num: Optional[int] = 1,
) -> PlanTemplate:
    """
    Extracts and processes a specific page from a provided PDF file of plans.

    This endpoint accepts a PDF file and a page number. It processes the specified page
    and returns a response based on the 'PlanTemplate' model. This function is designed
    to be used with an API that handles file uploads and can process PDF files.

    Args:
    - file (UploadFile): The PDF file to be processed, uploaded as multipart/form-data.
    - page_num (int, optional): The page number to extract from the PDF. Defaults to 1.

    Returns:
    - PlanTemplate: A model representing the processed data, including paths to the 
      extracted images and sections.

    Raises:
    - HTTPException: If processing fails or an invalid page number is provided. The exception
      includes the status code, error details, and relevant headers.

    Note:
    - The 'PlanTemplate' model should define the structure of the returned data, including
      fields like 'imagepath' and 'sectionspath'.
    """

    section_size = (1700, 1900)

    try:
        image_path, sections_in_folder,status_code = await process_pdf(file, 
                                                           page_num=page_num,
                                                           section_size=section_size)
        if(status_code==200):
            return PlanTemplate(imagepath=image_path, 
                            sectionspath=sections_in_folder)
    except Exception as e:
        error_message = str(e)
        raise HTTPException(
            status_code=500,  
            detail=error_message,
            headers={"X-Error": error_message},
        )