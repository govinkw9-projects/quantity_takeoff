import onnxruntime
import numpy as np 
import cv2 
from typing import List, Tuple
from ultralytics import YOLO

model_path = 'core/template_matching/yolov8/best.pt'



def infer_torch(image: np.ndarray = np.zeros((1024, 1024, 3)), 
               conf_threshold: float = 0.05, 
               nms_threshold: float = 0.05) -> np.ndarray:
    """
    Perform inference on an image using an ONNX model and apply post-processing.

    Parameters:
    - image: np.array, input image.
    - conf_threshold: float, confidence threshold for filtering predictions.
    - nms_threshold: float, IoU threshold for Non-Maximum Suppression.

    Returns:
    - boxes_xyxy[indices]: np.array, filtered and processed bounding boxes.
    """

    model = YOLO(model_path)

    result = model.predict(image, 
                        save=False,
                        iou = 0.05,
                        imgsz = 1024, 
                        conf=0.05)


    bboxes = result[0].boxes.data.cpu().numpy()

    formatted_bboxes = []
    for box in bboxes:
        # Extract the top left corner, width, and height
        x, y, x_end, y_end,_,_ = box
        formatted_bboxes.append((x, y, x_end, y_end))

    return formatted_bboxes 