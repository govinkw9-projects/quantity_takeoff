import copy
import numpy as np
import cv2
from fastapi import HTTPException
from core.detection.inference import infer_onnx
from typing import Tuple, List
from concurrent.futures import ThreadPoolExecutor
import time 
import asyncio
from core.config import global_params, logger


async def getBoundingBoxes(source_image: np.ndarray) -> Tuple[
                                                    np.ndarray, 
                                                    List[Tuple[Tuple[int, int], Tuple[int, int]]], str, 
                                                    int]:
    """
    Performs template matching to find instances of the template image in the source image.
    
    Args:
    - source_image (np.ndarray): The source image in which to find templates.
    - template_image (np.ndarray): The template image to match in the source image.

    Returns:
    - Tuple[np.ndarray, List[Tuple[Tuple[int, int], Tuple[int, int]]], str, int]: A tuple containing the image with drawn bounding boxes, list of bounding boxes, a status message, and a status code.

    TIPS: Use more degrees and use a value of 0.85 for the first processing to get ALL the correct symbols. This will also give some garbage but we can later filter it out. 

    Raises:
    - HTTPException: Specific HTTP errors encountered during processing.
    - IOError: If there is an issue in file operations.
    - RuntimeError: For errors specific to image processing or feature extraction.
    """
    logger.debug("Getting bboxes of a section... ")
    draw_on_image = source_image.copy()
    valid_boxes = []
    symbols_detected_list_numpy = []
    try: 
        bboxes = infer_onnx(image=source_image,model_path=global_params.symbol_yolo_model_path)
        for i , box in enumerate(bboxes):
            x, y, x_end, y_end = box
            area = (x_end - x) * (y_end - y)
            if area > 0:
                roi = source_image[int(y): int(y_end), int(x): int(x_end)]
                valid_boxes.append([(int(x), int(y)), (int(x_end), int(y_end))])
                cv2.rectangle(draw_on_image, (int(x), int(y)), (int(x_end), int(y_end)), (255, 0, 0), 2)
                logger.debug(f"Symbol {i} with shape {roi.shape}")
                symbols_detected_list_numpy.append(roi)

        return draw_on_image, valid_boxes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))      

def process_section_sync(idx,section_nparray):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Call the async function from the synchronous function
    boxes_drawn_image, boxes = loop.run_until_complete(
        getBoundingBoxes(
            source_image=section_nparray        )
    )
    return boxes_drawn_image, boxes

async def detect_symbols(image_sections_nparray_list):
    processed_sections = []
    processed_boxes = []
    with ThreadPoolExecutor(max_workers=global_params.max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                executor, 
                process_section_sync,
                idx,  
                section_nparray
            )
            for idx,section_nparray in enumerate(image_sections_nparray_list)
        ]
        results = await asyncio.gather(*tasks)
        for idx, (boxes_drawn_image, boxes) in enumerate(results):
            processed_sections.append(boxes_drawn_image)
            processed_boxes.append(boxes)
    return processed_sections, processed_boxes