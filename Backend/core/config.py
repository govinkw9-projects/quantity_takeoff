from pydantic_settings import BaseSettings
import logging
import os 
from dotenv import load_dotenv
load_dotenv()

if(os.environ.get("LOGGER_LEVEL")=="info"):
     log_level = logging.INFO
else:
     log_level = logging.DEBUG

def configured_logger():

        logger = logging.getLogger("uvicorn")
        logger.setLevel(log_level)

        while logger.hasHandlers():
            logger.handlers.clear()

        handler = logging.StreamHandler()
        handler.setLevel(log_level)

            # Create formatter
        formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        return logger


class Settings(BaseSettings):
    api_key: str
    logger_level: str

    class Config:
        env_file = ".env"



class GlobalParams():
    temp_dir = 'temp'


    # Pdf image to section conversion 
    intensity_threshold = 0.0 
    dpi: int =200
    section_size = (1900, 1500)


    # legend symbol detection 
    legend_yolo_model_path:str = 'core/detection/legend//best.onnx'
    if(not os.path.exists(legend_yolo_model_path)): 
        raise FileNotFoundError(f"{legend_yolo_model_path} not found ") 


    # Template matching params 
    threshold = 0.80 
    nms_threshold = 0.5 
    run_in_parallel = True # Always true, just adjust the number of workers. 
    max_workers = 1
    image_similarity_threshold = 0.3
    image_similarity_imgsize = (64,64)
    image_similarity_weight_file = "core/template_similarity/onnx_weights/siamese_network.onnx"
    degrees = [0]
    symbol_yolo_model_path:str = 'core/detection/symbol/best.onnx'
    if(not os.path.exists(symbol_yolo_model_path)): 
        raise FileNotFoundError(f"{symbol_yolo_model_path} not found ") 

    # Visualization 
    color_lists = [
        (255,0,0),
        (0,255,0),
        (0,0,255),
        (255,255,0),
        (0,255,255),
        (255,0,255),
        (128,0,0),
        (0,0,128),
        (0,128,128),
        (160,82,45)
    ]

    
    # Segment anything config for symbol detection 
    sam_file_url_b= "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
    sam_file_url_l = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth"
    sam_file_url_h = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
    sam_model = {"model_type": "vit_b",
                 "file_url":sam_file_url_b}
    sam_weight_path = "core/segment_symbol/sam_"+sam_model["model_type"]+".pth"
    sam_device = "cuda"
    sam_min_width = 25
    sam_max_width = 55

    # Area Detection, need to be fixed later 
    area_detection_models ={"filename": "core/area_detection/area-detection.zip",
                        "file_url":"--header='Host: drive.usercontent.google.com' --header='User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36' --header='Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' --header='Accept-Language: en-US,en;q=0.9' --header='Cookie: SID=fAjydJfwxlEZRIqJf3K1fXM1PyDGyg-5oCKFPj4JuWIybK36s2yjWigLUiFkjoakORwI8Q.; __Secure-1PSID=fAjydJfwxlEZRIqJf3K1fXM1PyDGyg-5oCKFPj4JuWIybK36FF8hHiDublNdBXNKhcKtlQ.; __Secure-3PSID=fAjydJfwxlEZRIqJf3K1fXM1PyDGyg-5oCKFPj4JuWIybK36D27bIEZkAiqLklLJ0FqMrw.; HSID=AppnCvwMAKnF3t01g; SSID=Ajo-S-ggGnxSq7c-R; APISID=NhQjGNfXweLWCftR/AhJ65BSLE64T4pPs9; SAPISID=bBHys7fomb-H-O79/AGF21e-pReSPQWXJZ; __Secure-1PAPISID=bBHys7fomb-H-O79/AGF21e-pReSPQWXJZ; __Secure-3PAPISID=bBHys7fomb-H-O79/AGF21e-pReSPQWXJZ; 1P_JAR=2024-1-8-11; AEC=Ae3NU9OOjP-9cIxkvLXd5QA_RQ601I4lQ97q3HCGFm1CpyW8v5XmfE3NbIc; __Secure-ENID=17.SE=F9AzLwXqI-pa8OA63z8sNv2JcnWsCxHT7SEfaNo36-xoIoETX9c2LarSFklO8u4pxPjO7JNI-v5IEWX0e1qqq7AgHE90u37yu5e05gFdFnUN9MN3n9KiXpvHltcqjm8R4BLn_kwkazLomgHBuzcWCBm8AjvoNPshgzoB-eVRUXwwyx-F8BJo2D4V-Vvw7-se7ViiKK-whef-A4TGjTZEqx95-LDW9zk-Th0zlAjfQMnHRH5WTqsj18BKdcg-rIrvpmaNJD1PLCGqWtg85j_JuX0qfFOaf63qNQ; NID=511=iebfOM9XdAbMRCoISRI_gDaPguLwaM1zto1LeOkcZCJES_zllOpAFOkz4SvCoeF_MAO4qEFfhTIPqh7WET0ZzN-RtVJ0V7bwTjVjjp603khgldgaarYcEFclPrW2tDIVnB2-BGk9sg9wnU6unqLYSwgVnXwTFKt8kH4JG4rqiF8bec4FlgVtEsTKnMzZ3ZvnqTODI1MoR_ghigmAgsbpxM2CSy7lflgk7e_-47DM71MxZQIjdL0r9kLijmKz1KgS-5wpTJnxFJx1APt1ttDE8zWYl-1G; __Secure-1PSIDTS=sidts-CjIBPVxjShOnxPwnbF9xuKIBgIzDmYatoBC4z0BWi5CdatjPhBRqWvygikYF6lFLQ0g94xAA; __Secure-3PSIDTS=sidts-CjIBPVxjShOnxPwnbF9xuKIBgIzDmYatoBC4z0BWi5CdatjPhBRqWvygikYF6lFLQ0g94xAA; SIDCC=ABTWhQGOC4MjRn-BSfW1QO4991A92jzSe5t3nocD4nf36yP2nINrMfg0KYUmaUfVgT7GkwbO4yY; __Secure-1PSIDCC=ABTWhQGW2fJp2t8jgdiJ2bKrAHMIdPz4avKSxSO8X8cwbJlVOavUJ1kdnLYxb1na7ioPED6s5R0; __Secure-3PSIDCC=ABTWhQEJvorV0VyYzER8wmT9csM7LZ_uvd54Ma6Eyo-_wYzMIiuEoFeu47Rtux8CXCtCu4xO3g' --header='Connection: keep-alive' 'https://drive.usercontent.google.com/download?id=1mE8nUPyJlZddZeXJI3sMPHKmPs4Ez9Q1&export=download&authuser=0&confirm=t&uuid=2918d451-0607-4d77-be74-67e092f4ae1d&at=APZUnTUea3F-_M6zua4ZCqB7VDpj%3A1705602400692' -c "}


settings = Settings()
global_params = GlobalParams()
logger = configured_logger()
