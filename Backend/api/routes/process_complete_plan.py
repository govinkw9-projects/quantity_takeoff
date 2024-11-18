from fastapi import APIRouter, UploadFile, File, HTTPException
from models import ProcessPDFTemplateMatchingResponse2, LegendTemplateResponse2
from core.pdf_to_images.processpdf import process_pdf
from core.template_matching.ProcessBoundingBoxYolov8 import getBoundingBoxes_parallel as getbboxes_yolov8
from core.pdf_to_images.getimages import patch_sections_together, adjust_bounding_boxes
from core.template_similarity.dino_vectorbase import filter_bounding_boxes, get_vectorstore, find_matches_for_template
from core.segment_symbol.yolov8.process_symbol import process_symbol as psymbol_yolov8
from core.apikey_auth import APIKeyAuth
from fastapi import Security, HTTPException, Depends
from core.config import global_params, settings
from api.routes.utils import image_to_base64
from typing import Optional, List, Tuple
import glob 
import os
import cv2 
import numpy as np 
import time 
import base64
from io import BytesIO
from PIL import Image
from pathlib import Path
import json 
import logging 

logger = settings.configured_logger

logger_active = logger.isEnabledFor(logging.INFO)

print(f"LOGGER ACTIVE", logger_active)
router = APIRouter()


async def process_symbols_detection(image: np.ndarray, 
                                  sections_in_folder: str ,
                                  sections_list: List[np.ndarray],
                                  locations_sections: List[Tuple[int, int]]) -> Tuple[List[Tuple[Tuple[int, int], Tuple[int, int]]], np.ndarray]:
    """
    Process image sections for symbol detection and reconstruct the processed image.

    Parameters:
    - image (str): Original complete image as nparray.
    - sections_list (str): List of numpy array of image sections.
    - locations_sections (List[Tuple[int, int]]): Locations of the sections in the original image.

    Returns:
    - Tuple[List[Tuple[Tuple[int, int], Tuple[int, int]]], np.ndarray]: Adjusted bounding boxes and the complete processed image.
    
    Raises:
    - FileNotFoundError: If the image file or sections are not found.
    - Exception: For other processing errors.
    """

    original_complete_image = image
    original_shape = original_complete_image.shape 
    logger.info(f"Full image shape {original_shape}")
    logger.info(f"Sucessfully processed the patches of the image, found {len(sections_list)} sections")
    processed_sections = []
    processed_boxes = []
    # Step2: Process each section for template matching 
    processed_sections, processed_boxes = await getbboxes_yolov8(sections_list, 
                                                                global_params.max_workers)
    if(logger_active):
        try:
            json_data = {}
            for i,bboxes_sections in enumerate(processed_boxes):
                json_data.update({f"section_bbox-{i}":bboxes_sections})
            json.dump(json_data,
                    open(sections_in_folder+f"/processed/all-symbol-detected.json","w"),
                    indent=4)
        except:
            logger.info("Could not save Processed Boxes {idx}")
    # Step3: Put together everything wrt to the original image
    # Step3.1: Put together the sections to get back the complete image 
    process_complete_image = patch_sections_together(processed_sections, 
                                                    original_shape, 
                                                    locations_sections)
    if(logger_active): 
        cv2.imwrite(sections_in_folder+f"/processed/all-symbols-detected.png",process_complete_image)
        cv2.imwrite(f"static/images/all_result.png",process_complete_image)
    # Step3.2: Adjust the bounding boxes of the sections to get bounding boxes wrt. to complete image. 
    adjusted_boxes = adjust_bounding_boxes(processed_boxes, locations_sections)
    logger.info("adjusting boxes")

    drawn_original_complete_image = image 
    show_with_color = (255,120,50)
    json_data = {}
    for i in range(len(adjusted_boxes)):
            (x_min, y_min), (x_max, y_max) = adjusted_boxes[i]
            drawn_original_complete_image = cv2.rectangle(drawn_original_complete_image, (x_min, y_min), (x_max, y_max), show_with_color, 3)
            if(logger_active):
                try:
                  json_data.update({f"bbox-{i}":adjusted_boxes[i]})
                  json.dump(json_data,open(sections_in_folder+f"/processed/adjusted_symbols.json","w"),indent=4)
                except:
                    pass
    return adjusted_boxes,drawn_original_complete_image

@router.post("/process_complete_plan", response_model=ProcessPDFTemplateMatchingResponse2)
async def get_templates_from_pdf(
    # api_key: str = Depends(APIKeyAuth),
    pdffile: UploadFile = File(..., description="The PDF file of Plans to be processed."),
    legendImageFile: UploadFile = File(..., description="The image file of the legend which contains all the legends"),
    page_num: Optional[int] = 1
) -> ProcessPDFTemplateMatchingResponse2:
    """
    Processes a PDF plan by extracting symbols from the specified page and matching them against symbols from a provided legend image. 

    This endpoint performs several steps to analyze the plan:
    - **Step 1**: Extracts the plan image from the specified page number of the PDF.
    - **Step 2**: Converts the plan image into multiple sections for analysis by a deep learning model.
    - **Step 3**: Identifies all symbols within the legend image.
    - **Step 4**: Detects all symbols present in the plan image.
    - **Step 5**: Performs template matching between the symbols from the legend and those found in the plan image, effectively indexing the symbols.

    ### Parameters:
    - `api_key` (str): API key for authentication (provided via header).
    - `pdffile` (UploadFile): The PDF file of plans to be processed.
    - `legendImageFile` (UploadFile): The image file of the legend containing all the symbols.
    - `page_num` (Optional[int]): Page number to process from the PDF file. Defaults to the first page.

    ### Returns:
    A `ProcessPDFTemplateMatchingResponse2` object containing the following fields:
    - `image_base64` (str): A Base64-encoded string of the plan image from the specified page. This is the raw image of the plan without any annotations.
    - `template_response` (List[dict]): A list of objects, each representing a detected symbol in the plan. Each object includes:
      - `mask_base64` (str): Base64-encoded image of the symbol's bounding box region from the plan image.
      - `bbox` (List[List[int]]): Coordinates of the bounding box around the detected symbol, specified as `[x, y, width, height]`.
      - `score` (float): Confidence score of the symbol detection, where 1.0 indicates 100% confidence.
      - `point_coord` (List[List[float]]): Center coordinates of the bounding box, specified as `[center_x, center_y]`.
      - `uncertain_iou` (float): Intersection Over Union (IOU) score of the bounding box prediction, indicating the accuracy of the detection. A score of 0 implies no test data was available for comparison.
      - `area` (int): The area of the bounding box in pixels, calculated as `width * height`.
      - `color` (List[List[int]]): RGB values used to draw the bounding box on the complete plan image, specified as `[R, G, B]`.
      - `symbol_Type` (int): A unique identifier for the symbol type. Symbols with the same `symbol_Type` are considered to represent the same object.
    - `all_symbols_image_base64` (str): Base64-encoded image of the plan with all detected symbols highlighted with bounding boxes.
    - `processing_time` (float): Total time taken to process the plan, in minutes, providing insight into the performance of the processing operation.

    Note: The processing logic may raise exceptions for invalid inputs or unforeseen processing errors. These are handled by returning appropriate HTTP error responses to the client.

    

    ### Example Response:
    ```json
    {
      "image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA...",
      "template_response": [
        {
          "mask_base64": "data:image/png;base64,iVBORw0K...",
          "bbox": [
            [100, 200, 50, 75]
          ],
          "score": 1.0,
          "point_coord": [
            [125, 237.5]
          ],
          "uncertain_iou": 0.95,
          "area": 3750,
          "color": [
            [255, 0, 0]
          ],
          "symbol_Type": 1
        }
      ],
      "all_symbols_image_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA...",
      "processing_time": 2.34
    }
    ```


    """


    save_symbols_path = "temp"
    start_time = time.time()
    # Step1: Get the sections of the page of the pdf which can be found in sections_in_folder
    process_pdf_response= await process_pdf(file=pdffile, 
                                            page_num=page_num,
                                            section_size=global_params.section_size)
    selected_page_image, image_path, sections_in_folder,sections_nparray_list,locations_sections= process_pdf_response
    logger.info(f"Obtained {len(locations_sections)} sections from the pdf image")
    
    all_symbols_drawn_image = selected_page_image.copy()
    if(logger_active):
        save_symbols_path = sections_in_folder+"/symbols"
        os.makedirs(sections_in_folder+"/processed", exist_ok=True)

    logger.info(f"Detecting symbols in legend image")
    symbols_nparray_list = await psymbol_yolov8(file=legendImageFile,
                                                save_symbols_path=save_symbols_path)

    logger.info(f"Detected {len(symbols_nparray_list)} symbols in the legend image")         
    original_complete_image_base64 = image_to_base64(selected_page_image) # Output1
    all_adjusted_boxes,drawn_original_complete_image = await process_symbols_detection(selected_page_image, 
                                                        sections_in_folder,
                                                        sections_nparray_list,
                                                        locations_sections)

    template_response = []
    
    json_data = {}

    #vectorstore = await get_vectorstore(all_adjusted_boxes,drawn_original_complete_image)

    # refined_bounding_boxes_list = await filter_bounding_boxes(boxes=all_adjusted_boxes,
    #                                                          full_image=drawn_original_complete_image,target_template_list=symbols_nparray_list)

    for idx,template_np_image in enumerate(symbols_nparray_list):
        # Step2: Process each template image to get the final bounding boxes wrt to the full complete image along with the bounding boxes drawn complete image
        logger.info(f"Processing template matching for symbol {idx+1} out of {len(symbols_nparray_list)}") 
        
        refined_bounding_boxes = await filter_bounding_boxes(boxes=all_adjusted_boxes,
                                                             full_image=drawn_original_complete_image,target_template=template_np_image)
        
        # refined_bounding_boxes = await  find_matches_for_template(boxes=all_adjusted_boxes,
        #                                                           target_template=template_np_image,
        #                                                           vectorstore=vectorstore)

        #refined_bounding_boxes = refined_bounding_boxes_list[idx]

        if(logger_active):
            try:
                json_data.update({f"template-{idx}":refined_bounding_boxes})
                json.dump(json_data,open(sections_in_folder+f"/processed/all-symbol-refined-detected.json","w"),
                            indent=4)
            except:
                logger.info("Could not save Processed Boxes {idx}")

        try:
            show_with_color = global_params.color_lists[idx]
        except:
            show_with_color = (255,120,50)

        for _, bbox in enumerate(refined_bounding_boxes):
            (x, y), (x_end, y_end) = bbox
            area = (x_end - x) * (y_end - y)
            all_symbols_drawn_image = cv2.rectangle(all_symbols_drawn_image, (int(x), int(y)), (int(x_end), int(y_end)), show_with_color, 3)
            # Proceed only if the area is greater than 0
            if area > 10:
                roi = selected_page_image[int(y): int(y_end), int(x): int(x_end)]
                mask_base64 = image_to_base64(roi)
                response_this_template = LegendTemplateResponse2(mask_base64=mask_base64,
                                                                bbox=[(x, y, x_end-x, y_end-y)],
                                                                 score=1.0,
                                                                 point_coord=[(0.0,0.0)],
                                                                 uncertain_iou=1.0,
                                                                 area=area,
                                                                 color=[(255,255,255)], 
                                                                 symbol_type=idx)
                template_response.append(response_this_template)

        all_adjusted_boxes = [box for box in all_adjusted_boxes if box not in refined_bounding_boxes]


        if(logger_active): 
            cv2.imwrite(sections_in_folder+f"/processed/all-symbols-refined-detected.png",all_symbols_drawn_image)
            cv2.imwrite(f"static/images/result.png",all_symbols_drawn_image)
    
        logger.info(f"Found {len(refined_bounding_boxes)} templates out of {len(all_adjusted_boxes)}")
        logger.info(f"Template matching completed for {idx+1} out of {len(symbols_nparray_list)}")

    show_with_color = (125,125,125)
    for _, bbox in enumerate(all_adjusted_boxes):
                (x, y), (x_end, y_end) = bbox
                area = (x_end - x) * (y_end - y)
                if(area > 40 and (x_end - x) > 16 and (y_end - y) > 16):
                  all_symbols_drawn_image = cv2.rectangle(all_symbols_drawn_image, (int(x), int(y)), (int(x_end), int(y_end)), show_with_color, 5)

    total_time_taken = (time.time() - start_time)/60.0
    all_symbols_drawn_image_base64 = image_to_base64(all_symbols_drawn_image)

    if(logger_active): 
        cv2.imwrite(sections_in_folder+f"/processed/all-symbols-refined-detected.png",all_symbols_drawn_image)
        cv2.imwrite(f"static/images/result.png",all_symbols_drawn_image)

    if(len(template_response)==0):
        response_this_template = LegendTemplateResponse2(mask_base64="",
                                                        bbox=[(0,0,0,0)],
                                                        score=1.0,
                                                        point_coord=[(0.0,0.0)],
                                                        uncertain_iou=1.0,
                                                        area=0,
                                                        color=[(255,255,255)], 
                                                        symbol_Type=idx)
        template_response.append(response_this_template)



    return ProcessPDFTemplateMatchingResponse2(template_response=template_response,
                                               processing_time=total_time_taken)

