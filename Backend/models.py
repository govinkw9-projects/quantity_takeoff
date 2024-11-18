from pydantic import BaseModel, Field
from typing import List, Tuple, Dict



class PlanTemplate(BaseModel):
    imagepath: str
    sectionspath: str


class ErrorResponse(BaseModel):
    error: str


class TemplateMatchingResponse(BaseModel):
    templateImage: str  # base64 image of the template 
    bounding_boxes: List[List[Tuple[int, int]]]  # List of bounding boxes
    boxes_drawn_image: str # 

class LegendTemplate(BaseModel):
    symbols_base64: List[str]


class ProcessPDFTemplateMatchingResponse(BaseModel):
    """
    Complete response for processing of a single template/symbol image


    Expected response would have 4 keys as below

    response = {"image_base64": str # Image of the pdf on the page number 
                template_response={
                    "id1":{"bounding_box":[], # Symbol 1 detected bounding boxes 
                       "templateImage":"str", # Symbol 1 image as base64 
                       "drawn_image": "str"}, # Image of the pdf on the page number with boxes drawn 
                    "id2":{"bounding_box":[],  # Symbol 2 data 
                        "templateImages":"str",
                        "drawn_image": "str"},  
                    "id3":{"bounding_box":[], # Symbol 3 data 
                            "templateImages":"str",
                            "drawn_image": "str"},
                },
                "all_symbols_image_base64": str # Image of the pdf on the page number with all symbols
                "processing_time": float  # Total time taken for processing in minutes
 

}

    """
    image_base64: str = Field(..., description="Image of the pdf on the page number ")
    template_response: Dict[str, TemplateMatchingResponse]
    all_symbols_image_base64: str =Field(..., description="Image of the pdf on the page number with all symbols ")
    processing_time: float  # Total time taken for processing in minutes

class ProcessPDFTemplateAreaDetectionResponse(BaseModel):
    """
    Complete response for processing of a single template/symbol image
    """

    image_base64: str  # Base64 encoded string of the image
    areas: List[float]  # List of bounding boxes
    processing_time: float  # Total time taken for processing in minutes
    area_detected_image: str # Base64 encoded string of the symbol images


class LegendTemplateResponse2(BaseModel):
    mask_base64: str
    bbox : List[Tuple[int,int,int,int]]
    score : float
    point_coord: List[Tuple[int, int]]
    uncertain_iou: float 
    area: int 
    color: List[Tuple[int,int,int]]
    symbol_type: int 



class ProcessPDFTemplateMatchingResponse2(BaseModel):
    """
    Complete response for processing of a single template/symbol image


    Expected response would have 4 keys as below

    response = {"image_base64": str # Image of the pdf on the page number 
                template_response={
                    "id1":{"bounding_box":[], # Symbol 1 detected bounding boxes 
                       "templateImage":"str", # Symbol 1 image as base64 
                       "drawn_image": "str"}, # Image of the pdf on the page number with boxes drawn 
                    "id2":{"bounding_box":[],  # Symbol 2 data 
                        "templateImages":"str",
                        "drawn_image": "str"},  
                    "id3":{"bounding_box":[], # Symbol 3 data 
                            "templateImages":"str",
                            "drawn_image": "str"},
                },
                "all_symbols_image_base64": str # Image of the pdf on the page number with all symbols
                "processing_time": float  # Total time taken for processing in minutes
 

}

    """
    template_response: List[LegendTemplateResponse2]
    processing_time: float  # Total time taken for processing in minutes

