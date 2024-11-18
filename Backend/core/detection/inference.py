import onnxruntime
import numpy as np 
import cv2 
from typing import List, Tuple
from core.config import logger

opt_session = onnxruntime.SessionOptions()
opt_session.enable_mem_pattern = False
opt_session.enable_cpu_mem_arena = False
opt_session.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_DISABLE_ALL


#model = YOLO('detect/train2/weights/best.pt')
#model.export(format="onnx",imgsz=[1024])  # export the model to ONNX format
EP_list = ['CUDAExecutionProvider', 'CPUExecutionProvider']
EP_list = ['CPUExecutionProvider']

def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> List[int]:
    """
    Apply Non-Maximum Suppression (NMS) to filter out overlapping bounding boxes based on their IoU.

    Parameters:
    - boxes: np.array, bounding boxes in (x_min, y_min, x_max, y_max) format.
    - scores: np.array, confidence scores for each bounding box.
    - iou_threshold: float, IoU threshold for suppressing boxes.

    Returns:
    - keep_indices: list, indices of boxes to keep.
    """
    # Sort by score
    sorted_indices = np.argsort(scores)[::-1]
    keep_indices = []

    while sorted_indices.size > 0:
        current_index = sorted_indices[0]
        current_box = boxes[current_index]
        keep_indices.append(current_index)
        if sorted_indices.size == 1:
            break
        rest_boxes = boxes[sorted_indices[1:]]
        ious = compute_iou(current_box, rest_boxes)
        sorted_indices = sorted_indices[np.where(ious < iou_threshold)[0] + 1]

    return keep_indices

def compute_iou(box, boxes):
    """
    Compute the Intersection over Union (IoU) between a given box and an array of boxes.

    Parameters:
    - box: np.array, a single bounding box.
    - boxes: np.array, multiple bounding boxes.

    Returns:
    - iou: np.array, IoU values.
    """
    xmin = np.maximum(box[0], boxes[:, 0])
    ymin = np.maximum(box[1], boxes[:, 1])
    xmax = np.minimum(box[2], boxes[:, 2])
    ymax = np.minimum(box[3], boxes[:, 3])

    intersection = np.maximum(0, xmax - xmin) * np.maximum(0, ymax - ymin)
    box_area = (box[2] - box[0]) * (box[3] - box[1])
    boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union = box_area + boxes_area - intersection

    return intersection / np.maximum(union, 1e-9)  # Avoid division by zero

def xywh2xyxy(x):
    """
    Convert bounding box format from (x_center, y_center, width, height) to (x_min, y_min, x_max, y_max).
    
    Parameters:
    - x: np.array, bounding boxes in (x_center, y_center, width, height) format.
    
    Returns:
    - y: np.array, bounding boxes in (x_min, y_min, x_max, y_max) format.
    """
    y = np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2
    y[:, 1] = x[:, 1] - x[:, 3] / 2
    y[:, 2] = x[:, 0] + x[:, 2] / 2
    y[:, 3] = x[:, 1] + x[:, 3] / 2
    return y


def infer_onnx(model_path:str, 
               image: np.ndarray = np.zeros((640, 640, 3)), 
               conf_threshold: float = 0.1, 
               nms_threshold: float = 0.1) -> np.ndarray:
    """
    Perform inference on an image using an ONNX model and apply post-processing.

    Parameters:
    - image: np.array, input image.
    - conf_threshold: float, confidence threshold for filtering predictions.
    - nms_threshold: float, IoU threshold for Non-Maximum Suppression.

    Returns:
    - boxes_xyxy[indices]: np.array, filtered and processed bounding boxes.
    """
    ort_session = onnxruntime.InferenceSession(model_path)
    input_shape = ort_session.get_inputs()[0].shape
    input_name = ort_session.get_inputs()[0].name
    output_name = ort_session.get_outputs()[0].name

    image_height, image_width = image.shape[:2]
    input_height, input_width = input_shape[2:]

    resized = cv2.resize(image, (input_width, input_height))
    input_image = resized / 255.0  # Normalize pixel values to 0-1
    input_image = input_image.transpose(2, 0, 1)  # Rearrange to CHW format
    input_tensor = np.expand_dims(input_image, axis=0).astype(np.float32)

    outputs = ort_session.run([output_name], {input_name: input_tensor})[0]
    predictions = np.squeeze(outputs).T

    scores = np.max(predictions[:, 4:], axis=1)
    valid_indices = scores > conf_threshold
    predictions = predictions[valid_indices]
    scores = scores[valid_indices]

    boxes_xywh = predictions[:, :4]
    #rescale box
    input_shape = np.array([input_width, input_height, input_width, input_height])
    boxes_xywh = np.divide(boxes_xywh, input_shape, dtype=np.float32)
    boxes_xywh *= np.array([image_width, image_height, image_width, image_height])
    boxes_xywh = boxes_xywh.astype(np.int32)

    boxes_xyxy = xywh2xyxy(boxes_xywh)

    indices = nms(boxes_xyxy, scores, iou_threshold=nms_threshold)

    return boxes_xyxy[indices]