import numpy as np
import cv2
from core.config import global_params, settings
from fastapi import HTTPException
from core.segment_symbol.yolov8.inference import infer_onnx
import os
from typing import Tuple, List
import io
import os
import subprocess
import shutil 
import logging


logger = settings.configured_logger

    
async def process_symbol(file, save_symbols_path) -> Tuple[str, int, List[np.ndarray]]:
    """
    Process an uploaded image file.

    This function reads the uploaded file, processes it, and returns a message and status code.

    Args:
    - file: An uploaded file object from FastAPI.

    Returns:
    - Tuple[str, int]: A message and HTTP status code.
    """
    logger_active = logger.isEnabledFor(logging.INFO)

    symbols_generated = []
    try:
        # Read the image file
        image_data = await file.read()
        image_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        logger.info(f"Legend image shape: {image.shape}")

        image_to_show_legend = image.copy()
        file_paths = []
        if(logger_active):
            try: 
                shutil.rmtree(save_symbols_path)
            except:
                pass 
            os.makedirs(save_symbols_path, exist_ok=True)

        bboxes = infer_onnx(image=image)

        for i , box in enumerate(bboxes):
            # Extract the top left corner, width, and height
            x, y, x_end, y_end = box
            area = (x_end - x) * (y_end - y)
            # Proceed only if the area is greater than 0
            if area > 0:
                roi = image[int(y): int(y_end), int(x): int(x_end)]
                logger.info(f" idx: {i} cropped detected symbol shape: {roi.shape}")
                if logger_active:
                    cv2.rectangle(image_to_show_legend, (int(x), int(y)), (int(x_end), int(y_end)), (255, 0, 0), 2)
                    file_path = f"{save_symbols_path}/symbol{i}.jpg"
                    cv2.imwrite(file_path, cv2.cvtColor(roi, cv2.COLOR_RGB2BGR))
                    logger.info(f"Symbol {i} with shape {roi.shape}")
                symbols_generated.append(roi)
        if logger_active:
            cv2.imwrite(f"{save_symbols_path}/all_symbol.jpg", image_to_show_legend)
        return symbols_generated
    except Exception as ex:
        logging.exception("An error occurred while processing symbol using yolov8 method: %s", str(ex))
        raise HTTPException(status_code=500, detail=f"An error occurred in processing symbol : {ex}")