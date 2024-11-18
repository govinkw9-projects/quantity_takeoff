import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for non-interactive plotting

import numpy as np
import cv2 
import onnx
import os 
import matplotlib.pyplot as plt 
import base64
from io import BytesIO
from core.config import global_params, settings
import logging
import openai 
import requests
from concurrent.futures import ThreadPoolExecutor
import time 
import asyncio

logger = settings.configured_logger
logger_active = logger.isEnabledFor(logging.INFO)


async def call_openai_vision(base64_image: bytes):
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.openai_key}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
            "role": "system",
        "content": [
            {
            "type": "text",
            "text": """
You are provided with the an image. You have to carefully analyse the image and provide detailed analysis of the image. Make responsible assumptions about the image. 
"""
            },
        ]            
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": """
There are two symbols shown in the image labelled (a) and (b). You have to carefully analyse the two symbols and provide aetailed anaylysis of the two symbols. They might of different size. The images might be rotated, scaled and consider it while making a decision. Start the analysis by answering are the two symbols same (Yes/No) ? 
"""
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}", 
                "detail": "high"

            },
            }
        ]
        }
    ],
    "max_tokens": 20
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload).json()
    analysis_of_image = response["choices"][0]["message"]["content"]
    return analysis_of_image

async def images_to_base64(img1,img2):
    # Plot the images side by side
    fig, axs = plt.subplots(1, 2, figsize=(2, 1))
    axs[0].imshow(img1, cmap='gray')
    axs[0].axis('off')  # Remove axis
    axs[0].set_title('(a)',fontsize=4)

    axs[1].imshow(img2, cmap='gray')
    axs[1].axis('off')  # Remove axis
    axs[1].set_title('(b)',fontsize=4)

    plt.tight_layout()
    if(logger_active):
        plt.savefig("temp/openai_input.png", bbox_inches="tight")
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Convert PNG byte array to base64 string
    b64_string = base64.b64encode(buf.read()).decode('utf-8')

    plt.close(fig)
    return b64_string



async def filter_bounding_boxes(bbox,full_image,target_template):
    refined_bbox = None
    try:
        (x1,y1), (x2,y2) = bbox
        cropped_template = full_image[int(y1):int(y2), int(x1):int(x2)]  
        b64_string = await images_to_base64(target_template, 
                                        cropped_template)
        
        analysis_of_image = await call_openai_vision(base64_image=b64_string)
        if("Sorry" in analysis_of_image): 
            analysis_of_image = await call_openai_vision(base64_image=b64_string)
        analysis_of_image = analysis_of_image.replace("\n\n","\n")
        logger.info(f"Image Analysis: {analysis_of_image}" )
        if ("yes" in analysis_of_image.lower() ):
                refined_bbox = bbox
    except Exception as e:
        logger.info(f"Could not process bbox , got error {e}")
    return refined_bbox

def process_section_sync(idx,bbox, full_image,template_np_image):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Call the async function from the synchronous function
    refined_bbox = loop.run_until_complete(
        filter_bounding_boxes(
            bbox=bbox, 
            full_image = full_image, 
            target_template=template_np_image
        )
    )
    return refined_bbox


async def filter_bounding_parallel(boxes,full_image,target_template):
    refined_bounding_boxes = []
    max_workers = 20
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                executor, 
                process_section_sync,
                idx,  
                bbox, 
                full_image,
                target_template
            )
            for idx,bbox in enumerate(boxes)
        ]
        results = await asyncio.gather(*tasks)
        for idx, (refined_bbox) in enumerate(results):
            if(refined_bbox):
                refined_bounding_boxes.append(refined_bbox)
    return refined_bounding_boxes