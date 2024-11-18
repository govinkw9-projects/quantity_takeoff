# Quantity Takeoff Api
This application is built using FastAPI and is designed to process images.
## How to use the application

1. Create an .env file similar to .env_template provided.
3. Create a python environment using python 3.9 version. 
2. Install the python packages `pip install -r requirements.txt` 
```bash

cd core/template_matching/cython_files
python setup.py build_ext -i -f
```
4. Now run the fastapi application using  `uvicorn main:app --reload --port 8080 --host 0.0.0.0 --workers 4`
