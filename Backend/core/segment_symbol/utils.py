
import numpy as np
import cv2
import easyocr

offset = 3 
iou_threshold = 0.2
width_min = 2
width_max = 200 
hw_ratio = 0.01 
need_atleast_text_pixels = 50 
kernel_size = (3, 3)
min_image_size_again_get_text = 20


def calculate_iou(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    # Calculate intersection coordinates
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1+w1, x2+w2)
    yi2 = min(y1+h1, y2+h2)

    # Calculate area of intersection
    inter_area = max(xi2 - xi1, 0) * max(yi2 - yi1, 0)

    # Calculate area of each bbox and union area
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    # Calculate IoU
    iou = inter_area / union_area if union_area != 0 else 0

    return iou


def recognize_text(image):
    reader = easyocr.Reader(['en'], gpu=True)  # Set to True if GPU is available
    result = reader.readtext(image, detail=1)
    return result


def check_symbol_has_only_text(image): 
    result = recognize_text(image)
    
    if(not result and (image.shape[0] < min_image_size_again_get_text or image.shape[1] < min_image_size_again_get_text)): 
        result = recognize_text(cv2.resize(image,(image.shape[1]*4,image.shape[0]*4))) 
        
        
    # Creating kernel 
    kernel = np.ones(kernel_size, np.uint8) 
    symbol_contains_long_text = False
    if(result): 
        for (bbox, text, prob) in result:
            if(len(text) > 4): 
                symbol_contains_long_text = True 
                # Using cv2.erode() method  
                image = cv2.erode(image, kernel) 
                break 
                
    new_image = image.copy()
    new_image[new_image<125.00001] = 0 
    new_image[new_image>125.00001] = 255
    u, indices = np.unique(new_image,return_counts=True)
    symbol_has_only_text = False 
    if(result): 
        for (bbox, text, prob) in result:
          # Since bbox is a list of tuple points, we need to convert it to a numpy array of shape (1, -1, 2).
            pts = np.array(bbox, dtype=np.int32)
            pts = pts.reshape((-1, 1, 2))
            # Fill the detected text area with zero (black).
            cv2.fillPoly(new_image, [pts], color=(0))
        u, indices = np.unique(new_image,return_counts=True)
        
        if(len(u)==1): 
            symbol_has_only_text =True 
        else:
            if(indices[1] < need_atleast_text_pixels) : 
                symbol_has_only_text =True 
        
    return result , symbol_has_only_text 


def compare_images(image1, image2,image_shape):
    """
    Compare two  images based on the percentage of black pixels (value = 0).
    Returns the image with a higher percentage of black pixels.
    
    Parameters:
    - image1: First  image
    - image2: Second  image
    
    Returns:
    - A tuple containing the binary image with a higher percentage of black pixels and its percentage of black pixels.
    """
    
    gray_image = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY) if len(image1.shape) == 3 else image1
    _, image1 = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
    new_image = np.zeros((image_shape[0],image_shape[1])) + 255
    new_image[0:image1.shape[0],0:image1.shape[1]] = image1
    image1 = new_image
    
    gray_image = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY) if len(image2.shape) == 3 else image2
    _, image2 = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
    new_image = np.zeros((image_shape[0],image_shape[1])) + 255
    new_image[0:image2.shape[0],0:image2.shape[1]] = image2
    image2 = new_image
    
    # Calculate the number of black pixels in each image
    unique1, counts1 = np.unique(image1, return_counts=True)
    black_pixels1 = counts1[0] if 0 in unique1 else 0
    percentage1 = black_pixels1 / image1.size
    
    unique2, counts2 = np.unique(image2, return_counts=True)
    black_pixels2 = counts2[0] if 0 in unique2 else 0
    percentage2 = black_pixels2 / image2.size
    
    if percentage1 >= percentage2:
        return image1, percentage1, 0 
    else:
        return image2, percentage2, 1


def find_closest_above_below(bboxes):
    above_below_dict = {}
    for i, bbox in enumerate(bboxes):
        closest_above = None
        closest_below = None
        min_distance_above = float('inf')
        min_distance_below = float('inf')

        for j, other_bbox in enumerate(bboxes):
            if i != j: # Ensure we're not comparing the bbox with itself
                # Check if other_bbox is directly above or below bbox
                horizontal_overlap = not (other_bbox[0] > bbox[0] + bbox[2] or other_bbox[0] + other_bbox[2] < bbox[0])
                if horizontal_overlap:
                    if other_bbox[1] < bbox[1] and bbox[1] - (other_bbox[1] + other_bbox[3]) < min_distance_above:
                        # other_bbox is above bbox
                        closest_above = j
                        min_distance_above = bbox[1] - (other_bbox[1] + other_bbox[3])
                    elif other_bbox[1] > bbox[1] and other_bbox[1] - (bbox[1] + bbox[3]) < min_distance_below:
                        # other_bbox is below bbox
                        closest_below = j
                        min_distance_below = other_bbox[1] - (bbox[1] + bbox[3])
        
        above_below_dict[i] = {"above": closest_above, "below": closest_below}
    
    return above_below_dict