# Use an official Python runtime as a parent image
#----------ONLY CPU-----------
# FROM tensorflow/tensorflow:2.15.0.post1 
#----------ONLY GPU-----------
#FROM tensorflow/tensorflow:2.15.0.post1-gpu 

FROM python:3.9-slim-buster

# Set environment variables to reduce Python bytecode generation and buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    gcc \
    wget \
    build-essential \
    gfortran \
    libglib2.0-0 \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    libopenblas-dev \
    cmake \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub

RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64/7fa2af80.pub

# Add the repository
RUN echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64 /" > /etc/apt/sources.list.d/cuda.list


RUN export DEBIAN_FRONTEND=noninteractive \
 && echo "LC_ALL=en_US.UTF-8" >> /etc/environment \
 && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
 && echo "LANG=en_US.UTF-8" > /etc/locale.conf \
 && apt update && apt install -y locales \
 && locale-gen en_US.UTF-8 \
 && rm -rf /var/lib/apt/lists/*

# Install OpenCV dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    gcc \
    wget \
    build-essential \
    gfortran \
    libglib2.0-0 \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    libopenblas-dev \
    cmake \ 
    && rm -rf /var/lib/apt/lists/*

#RUN pip install torch==2.0.1+cu117 torchvision==0.15.2+cu117 --index-url https://download.pytorch.org/whl/cu117 \
#    && rm -rf /root/.cache/pip

#Installing this tensorfor just to make sure 
# RUN pip install tensorflow[and-cuda]==2.15.0.post1 \
#   && rm -rf /root/.cache/pip

ENV LANG=en_US.UTF-8 \
  LANGUAGE=en_US:en \
  LC_ALL=en_US.UTF-8

WORKDIR /build_vision

COPY requirements.txt /build_vision/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt


#Installing this tensorfor just to make sure 
#RUN pip install tensorflow[and-cuda]==2.15.0.post1 && rm -rf /root/.cache/pip

# Copy the rest of your application's code
COPY . /build_vision/

# Build cython package 
WORKDIR /build_vision/core/template_matching/cython_files
RUN python setup.py build_ext -i -f

# Your application might listen on a certain port, so expose it
EXPOSE 8080
WORKDIR /build_vision

# Use Gunicorn as the WSGI server instead of the Flask development server
CMD ["gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--timeout", "600", "-w", "1", "main:app"]