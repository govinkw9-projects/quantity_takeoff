import os 
from core.config import global_params, settings
from PIL import Image
from fastapi import HTTPException, UploadFile
import numpy as np 
from typing import List, Tuple
from io import BytesIO
from .getimages import split_image_into_sections
import fitz
import aiofiles
import shutil 
import logging

logger = settings.configured_logger


def get_images_from_pdf(pdf_file_path: str, 
                        dpi: int = 200) -> List[Image.Image]:
    """
    Extracts images from a PDF file.

    This function uses PyMuPDF to render each page of the PDF as an image. 
    The resolution of the rendered images is controlled by the 'dpi' parameter.

    Parameters:
    pdf_file_path (str): Path to the PDF file to be processed.
    dpi (int, optional): Dots Per Inch (DPI) used for rendering images. 
                         Higher DPI values result in better image quality but larger files.
                         Defaults to 200.

    Returns:
    List[Image.Image]: A list of PIL Image objects, one for each page of the PDF.

    Raises:
    Exception: If the PDF file cannot be opened or processed.

    Example:
    images = get_images_from_pdf("path/to/file.pdf", dpi=300)
    """

    
    try:
        doc = fitz.open(pdf_file_path)
    except Exception as e:
        raise Exception(f"Error opening PDF file: {e}")

    images = []
    for idx in range(len(doc)):
        page = doc.load_page(idx)
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    doc.close()  # Don't forget to close the document
    return images


async def process_pdf(file: UploadFile, page_num: int = 1, section_size=(1700, 1900)) -> Tuple[str, List[str], List[np.ndarray], List[tuple], int, str]:
    """
    Process a PDF file to extract a specific page as an image, handling the file in memory.

    Args:
    - file (UploadFile): An uploaded file object from FastAPI.
    - page_num (int): The page number to extract from the PDF. Defaults to 1.
    - section_size (tuple): The size of each section to split the image into. Defaults to (1700, 1900).

    Returns:
    - selected_page_image: nd.array Numpy image 
    - sections: List of all the sections as numpy array 
    - locations: List of all locations of the sections 
    - 200: Status code 

    Raises:
    - HTTPException: For invalid page numbers or processing errors.
    """
    logger_active = logging.getLogger().isEnabledFor(logging.INFO)
    temp_dir = 'temp'  
    selected_page_image_path = ""
    try:
        # Read PDF into memory
        pdf_bytes = await file.read()
        pdf_stream = BytesIO(pdf_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        if page_num < 1 or page_num > len(doc):
            raise HTTPException(status_code=400, detail="Invalid page number")

        # Extract the specified page
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(dpi= 200)
        img = Image.open(BytesIO(pix.tobytes("png")))

        # Optionally save the extracted page for debugging
        if logger_active:
            os.makedirs(temp_dir, exist_ok=True)
            selected_page_image_path = os.path.join(temp_dir, f'{file.filename}_page_{page_num}.png')
            img.save(selected_page_image_path, 'PNG')

        selected_page_image = np.array(img)

        # Split image into sections
        save_sections_path, sections, locations = split_image_into_sections(
            image=selected_page_image, 
            image_name=file.filename,
            section_size=section_size
        )

        return selected_page_image,selected_page_image_path, save_sections_path, sections, locations
    except Exception as ex:
        logging.exception("An error occurred while processing the PDF: %s", str(ex))
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the PDF: {ex}")
