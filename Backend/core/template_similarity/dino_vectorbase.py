import numpy as np
from core.config import global_params, logger
import logging
import torch
from torchvision import transforms
from transformers import AutoImageProcessor, AutoModel
from sklearn.decomposition import PCA
import faiss
import numpy as np
import os
from PIL import Image ,ImageOps


def equalize_hist_rgb(img):
    """
    Apply histogram equalization to an RGB image using PIL.
    
    Parameters:
    - img: PIL.Image object in RGB mode.
    
    Returns:
    - PIL.Image object with histogram equalization applied to its luminance.
    """
    # Convert the RGB image to YCbCr
    ycbcr_img = img.convert('YCbCr')
    
    # Split the YCbCr image into Y, Cb, and Cr channels
    y, cb, cr = ycbcr_img.split()
    
    # Apply histogram equalization to the Y channel
    y_eq = ImageOps.equalize(y)
    
    # Merge the equalized Y channel back with Cb and Cr channels
    ycbcr_eq_img = Image.merge('YCbCr', (y_eq, cb, cr))
    
    # Convert the YCbCr image back to RGB
    rgb_eq_img = ycbcr_eq_img.convert('RGB')
    
    return rgb_eq_img

def transform_image(img,img_size=224):
    """
    Load an image and return a tensor that can be used as an input to DINOv2.
    """
    img = Image.fromarray(img)
    #img = equalize_hist_rgb(img)

    # img_gray = img.convert("L")
    # img_thresholded = img_gray.point(lambda p: p > 20 and 255)
    # img = img_thresholded.convert("RGB")

    transform_image = transforms.Compose(
            [
                transforms.Resize(img_size),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    transformed_img = transform_image(img)[:3].unsqueeze(0)

    return transformed_img

class VectorStore():
    def __init__(self,imgs, n_pca_components=10):
        self.imgs = imgs 
        self.index = faiss.IndexFlatL2(1024)
        self.n_pca_components = n_pca_components
        #Load the model and processor
        self.device = torch.device('cuda' if torch.cuda.is_available() else "cpu")
        self.processor = AutoImageProcessor.from_pretrained('facebook/dinov2-large')
        self.model = AutoModel.from_pretrained('facebook/dinov2-large').to(self.device)
        self.pca = PCA(n_components=n_pca_components)

        feature_vectors = []
        for idx,image in enumerate(imgs):
            with torch.no_grad():
                inputs = {'pixel_values': transform_image(image).to(self.device)}
                # inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                outputs = self.model(**inputs)
            features = outputs.last_hidden_state
            feature_vector = features.mean(dim=1).detach().cpu().numpy()
            feature_vectors.append(feature_vector.squeeze(0))

            if(n_pca_components==0):
                self.add_vectors_to_index(feature_vector)

        if(n_pca_components!=0):
            # Fit PCA on extracted feature vectors
            feature_vectors = np.array(feature_vectors)
            self.pca.fit(feature_vectors)

            # Transform feature vectors with PCA and add to FAISS index
            self.index = faiss.IndexFlatL2(n_pca_components)  # Update index dimensionality to PCA components
            transformed_vectors = self.pca.transform(feature_vectors)
            self.add_vectors_to_index(transformed_vectors)


    def add_vectors_to_index(self,feature_vector):
        feature_vector = np.float32(feature_vector)
        faiss.normalize_L2(feature_vector)
        #Add to index
        self.index.add(feature_vector)

    def find_index(self,given_image,threshold=0.34):
        with torch.no_grad():
            inputs = {'pixel_values': transform_image(given_image).to(self.device)}
            # inputs = self.processor(images=given_image, return_tensors="pt").to(self.device)
            outputs = self.model(**inputs)

        #Normalize the features before search
        embeddings = outputs.last_hidden_state
        embeddings = embeddings.mean(dim=1)

        vector = embeddings.detach().cpu().numpy()
        if(self.n_pca_components!=0):
            vector = self.pca.transform(vector)  # Transform with PCA

        vector = np.float32(vector)
        faiss.normalize_L2(vector)

        d,I = self.index.search(vector,min(100,len(self.imgs)))
        matched_indices = [I[0][idx] for idx, distance in enumerate(d[0]) if distance < threshold]

        return d[0],I[0]

        #return matched_indices  # for find_matches_for_template function 

def offset_bboxes(bbox,full_image,offset = 10):
    (x, y), (x_end, y_end) = bbox
    area = (x_end - x) * (y_end - y)

        # Image dimensions
    height, width = full_image.shape[:2]

        # Apply offset
    x_new = max(0, x - offset)
    y_new = max(0, y - offset)
    x_end_new = min(width, x_end + offset)
    y_end_new = min(height, y_end + offset)
    return (x_new,y_new), (x_end_new,y_end_new)



async def get_vectorstore(boxes,full_image):
    imgs = []
    for idx,bbox in enumerate(boxes):
        try:
            new_bbox = offset_bboxes(bbox,full_image,offset = 0)
            (x1,y1), (x2,y2) = new_bbox
            cropped_template = full_image[int(y1):int(y2), int(x1):int(x2)]  
            imgs.append(cropped_template)
        except:
            pass 
        
    vectorstore = VectorStore(imgs=imgs, n_pca_components=20)
    return vectorstore



def rotate_image(image, angle):
    """
    Rotate the given numpy array image by the specified angle (90, 180, 270 degrees).
    Assumes image is in shape (height, width, 3).
    """
    if angle == 90:
        return np.rot90(image, 1)
    elif angle == 180:
        return np.rot90(image, 2)
    elif angle == 270:
        return np.rot90(image, 3)
    else:
        return image

def find_matches_for_template(boxes,target_template, vectorstore):
    """
    Rotate the target_template by 90, 180, 270 degrees, and find matches for each rotation.
    Returns the union of all matches.
    """
    angles = [90, 180, 270]
    all_matches = set()  # Using a set to automatically handle duplicates
    
    # Original
    matches_indices = vectorstore.find_index(given_image=target_template, 
                                             threshold=0.4)
    all_matches.update(matches_indices)
    
    # Rotated versions
    for angle in angles:
        rotated_image = rotate_image(target_template, angle)
        matches_indices = vectorstore.find_index(given_image=rotated_image, 
                                                 threshold=0.4)
        all_matches.update(matches_indices)
    
    refined_bounding_boxes = []
    for idx in list(all_matches):
        refined_bounding_boxes.append(boxes[idx])

    return refined_bounding_boxes


async def filter_bounding_boxes2(boxes,full_image,target_template_list):
    all_matches_indices_distance = []
    aggregated_matches = []
    threshold = 0.39

    
    imgs = []
    for idx,bbox in enumerate(boxes):
        try:
            new_bbox = offset_bboxes(bbox,full_image,offset = 0)
            (x1,y1), (x2,y2) = new_bbox
            cropped_template = full_image[int(y1):int(y2), int(x1):int(x2)]  
            imgs.append(cropped_template)
        except:
            pass 
        
    vectorstore = VectorStore(imgs=imgs, n_pca_components=10)

    # Step 1: Aggregate Matches
    for idx, target_template in enumerate(target_template_list):
        # Assuming `vectorstore.find_index` returns a list of tuples (index, distance)
        matches_indices = vectorstore.find_index(given_image=target_template, 
                                                 threshold=threshold)
        # Append matches with template identifier (idx here)
        aggregated_matches.append((idx,)+matches_indices) # (template_idx, match_idx, distance)

        
        
    # Create a dictionary to hold each index and its minimum distance and label
    index_min_distance_simple = {}

    # Go through each label, distance, and index array in the simplified data
    for label, distances, indices in aggregated_matches:
        for dist, idx in zip(distances, indices):
            if idx not in index_min_distance_simple or dist < index_min_distance_simple[idx][0]:
                if(dist < threshold):
                    index_min_distance_simple[idx] = (dist, label)

    # Rebuild the distance and index arrays for each label based on minimum distances for the simplified example
    cleaned_matches_indices_distance = []
    for label, _, _ in aggregated_matches:
        new_distances = []
        new_indices = []
        for idx, (dist, assigned_label) in index_min_distance_simple.items():
            if assigned_label == label:
                new_distances.append(dist)
                new_indices.append(idx)

        # Sort the new distances and indices to maintain order
        sorted_indices_distances = sorted(zip(new_indices, new_distances), key=lambda x: x[0])
        sorted_indices, sorted_distances = zip(*sorted_indices_distances) if sorted_indices_distances else ([], [])
        
        cleaned_matches_indices_distance.append((label, np.array(sorted_distances), np.array(sorted_indices)))

        refined_bounding_boxes_list = []
        for idx in range(len(cleaned_matches_indices_distance)):
            _, d, I = cleaned_matches_indices_distance[idx]
            matched_indices = [I[i] for i, distance in enumerate(d)]
            refined_bounding_boxes = []
            for i in matched_indices:
                refined_bounding_boxes.append(boxes[i])

            refined_bounding_boxes_list.append(refined_bounding_boxes)


        return refined_bounding_boxes_list



async def filter_bounding_boxes(boxes,full_image,target_template): 
    select_num_indixes = 2
    threshold = global_params.image_similarity_threshold

    refined_bounding_boxes = []
    refined_bbox_indices = []
    imgs = []
    img_indices = []
    for idx,bbox in enumerate(boxes):
        try:
            new_bbox = offset_bboxes(bbox,full_image,offset = 0)
            (x1,y1), (x2,y2) = new_bbox
            area = (x2 - x1) * (y2 - y1)
            cropped_template = full_image[int(y1):int(y2), int(x1):int(x2)]
            if(area>5 and cropped_template.shape[0] > 5 and cropped_template.shape[1] > 5):  
                imgs.append(cropped_template)
                img_indices.append(idx)
        except:
            pass 
        
    vectorstore = VectorStore(imgs=imgs, n_pca_components=0)

    d, I = vectorstore.find_index(given_image=target_template, threshold=threshold)
    for idx, distance in zip(I, d):
        if(distance < threshold):
            refined_bbox_indices.append(img_indices[idx])
            
            
    d_array = np.array(d)  # Convert distances to a NumPy array for easier manipulation

    # Find the indexes of the smallest distances
    sorted_indexes = np.argsort(d_array)
    best_indexes_list = sorted_indexes[:min(select_num_indixes,len(sorted_indexes))]
    best_indexes_in_I = np.array(I)[best_indexes_list]
    best_distances = d_array[best_indexes_list]
    print(np.array(d)[sorted_indexes[0:5]])
    print("Found distances best ", np.array(d)[best_indexes_list])

    # Retrieve and process the best  matches
    for distance, best_matched_index in zip(best_distances,best_indexes_in_I):
        if(distance<threshold):
            (x, y), (x_end, y_end) = boxes[img_indices[best_matched_index]] 
            target_template = full_image[int(y):int(y_end), int(x):int(x_end)]  # Extract the template
            
            d, I = vectorstore.find_index(given_image=target_template, threshold=threshold)
            for idx, distance in zip(I, d):
                if(distance < threshold):
                    refined_bbox_indices.append(img_indices[idx])
                
        
    refined_bbox_indices = list(set(refined_bbox_indices))    

    for idx in refined_bbox_indices:
            refined_bounding_boxes.append(boxes[idx])


    return refined_bounding_boxes

async def filter_bounding_boxes4(boxes,full_image,target_template):
    refined_bounding_boxes = []
    imgs = []
    for idx,bbox in enumerate(boxes):
        try:
            new_bbox = offset_bboxes(bbox,full_image,offset = 0)
            (x1,y1), (x2,y2) = new_bbox
            cropped_template = full_image[int(y1):int(y2), int(x1):int(x2)]  
            imgs.append(cropped_template)
        except:
            pass 
        
    vectorstore = VectorStore(imgs=imgs, n_pca_components=0)
    # matches_indices = vectorstore.find_index(given_image=target_template,
    #                                          threshold=0.40)

    # for idx in matches_indices:
    #     refined_bounding_boxes.append(boxes[idx])

    refined_bounding_boxes = find_matches_for_template(boxes,target_template, vectorstore)



    return refined_bounding_boxes