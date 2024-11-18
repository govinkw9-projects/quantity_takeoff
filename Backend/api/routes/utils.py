import numpy as np 
import time 
import base64
from io import BytesIO
from PIL import Image
from pathlib import Path
import json 
import cv2 

def image_to_base64(image_array: np.ndarray) -> str:
    """
    Convert a numpy array to a base64 encoded string.

    This function takes an image in numpy array format (Height x Width x 3 channels)
    and converts it to a base64 encoded string. The numpy array should represent
    an image in BGR format (which is typical of OpenCV images). The image is first
    converted to RGB, then encoded to PNG format, and finally encoded to a base64
    string.

    Parameters:
    image_array (np.ndarray): The image in numpy array format. This should be a 3-channel
                              image (BGR format) with shape (Height, Width, 3).

    Returns:
    str: The base64 encoded string of the image.

    Example:
    >>> dummy_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    >>> base64_image = image_to_base64(dummy_image)
    >>> print(base64_image)  # This will print the base64 encoded string of the image.
    """

    # Convert the NumPy array to an RGB image using PIL
    image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))

    # Save the image to a buffer in PNG format
    buffered = BytesIO()
    image.save(buffered, format="PNG")

    # Encode the buffer's contents into a base64 string
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return img_str
      
