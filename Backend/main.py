from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from fastapi.staticfiles import StaticFiles
import os 

app = FastAPI()

# Directory where processed images will be saved
image_directory = "static/images"
os.makedirs(image_directory, exist_ok=True)

# Mount static files route
app.mount("/static", StaticFiles(directory="static"), name="static")

# Explicit CORS settings
origins = [
    "http://localhost:8001",  # Add other origins as needed
    "http://yourfrontenddomain.com",  # Example for a deployed frontend
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*", "secret"]  # Explicitly list 'secret'
)

app.include_router(api_router)