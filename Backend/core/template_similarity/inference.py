import onnxruntime as ort
import numpy as np
import cv2 
import onnx
import os 
from core.config import global_params, logger
import logging
from fastapi import HTTPException

logger_active = logger.isEnabledFor(logging.DEBUG)

def pairwise_distance_numpy(vector1, vector2):
    """
    Compute pairwise distance between two vectors using NumPy.

    Parameters:
    vector1 (np.ndarray): First vector.
    vector2 (np.ndarray): Second vector.

    Returns:
    np.ndarray: Pairwise distances.
    """
    return np.sqrt(np.sum((vector1 - vector2) ** 2, axis=1))

def preprocess_image(image):
    image = cv2.resize(image,global_params.image_similarity_imgsize)
    image = np.transpose(image,[2,0,1])
    image = np.expand_dims(image,axis=0)/255.0 
    return image


def predict_similarity(input_data1, input_data2):
    # Load the ONNX model
    weights_path = global_params.image_similarity_weight_file
    ort_session = ort.InferenceSession(weights_path)
    outputs = ort_session.run(None, {'onnx::Pad_0': input_data1, 
                                     'onnx::Pad_1': input_data2})
    euclidean_distance = pairwise_distance_numpy(outputs[0], outputs[1])
    if(euclidean_distance < global_params.image_similarity_threshold):
        category = "Similar"
    else:
        category = "Different"
    return category

async def filter_bounding_boxes(boxes,full_image,target_template):
    refined_bounding_boxes = []
    input_data2 = preprocess_image(target_template) # Target template image 
    for idx,bbox in enumerate(boxes):
        try:
            (x1,y1), (x2,y2) = bbox
            cropped_template = full_image[int(y1):int(y2), int(x1):int(x2)]  
            input_data1 = preprocess_image(cropped_template)
            predicted_category = predict_similarity(input_data2.astype(np.float32), 
                                                    input_data1.astype(np.float32))
            if(predicted_category=="Similar"):
                refined_bounding_boxes.append(bbox)
        except Exception as ex:
            logging.exception("An error occurred while filtering the bboxes: %s", str(ex))
            raise HTTPException(status_code=500, detail=f"An error occurred while filtering the bboxes: {ex}")
    return refined_bounding_boxes