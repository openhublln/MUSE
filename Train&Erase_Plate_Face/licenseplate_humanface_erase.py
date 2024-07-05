import os
import platform
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from ultralytics import YOLO

def text(img, text, xy=(0, 0), color=(0, 0, 0), size=20):
    pil = Image.fromarray(img)
    s = platform.system()
    if s == "Linux":
        font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', size)
    elif s == "Darwin":
        font = ImageFont.truetype('....', size)
    else:
        font = ImageFont.truetype('simsun.ttc', size)
    ImageDraw.Draw(pil).text(xy, text, font=font, fill=color)
    return np.asarray(pil)

# Load YOLO models
car_plate_model = YOLO('./runs/detect/train/weights/best_plate.pt')
face_model = YOLO('./runs/detect/train/weights/best_face.pt')

# Set input and output folder paths
origin_folder = 'Process/original'
plate_processed_folder = 'Process/plate_processed'
final_processed_folder = 'Process/final_processed'

# Check if Process folders exist, create them if not
if not os.path.exists(plate_processed_folder):
    os.makedirs(plate_processed_folder)
if not os.path.exists(final_processed_folder):
    os.makedirs(final_processed_folder)

# Read all images in the Origin folder
image_files = [f for f in os.listdir(origin_folder) if f.endswith('.jpg') or f.endswith('.png')]

# Step 1: Car plate detection and obscuring
for i, file in enumerate(image_files):
    full = os.path.join(origin_folder, file)
    print(f"Processing car plate detection for: {full}")
    img = cv2.imdecode(np.fromfile(full, dtype=np.uint8), cv2.IMREAD_COLOR)
    img = img[:, :, ::-1].copy()

    # Make the image writable
    img.setflags(write=1)

    # Car plate detection
    plate_results = car_plate_model.predict(img, save=False)
    plate_boxes = plate_results[0].boxes.xyxy

    for box in plate_boxes:
        x1 = int(box[0])
        y1 = int(box[1])
        x2 = int(box[2])
        y2 = int(box[3])
        # Blur the region of the car plate
        roi = img[y1:y2, x1:x2]
        roi = cv2.GaussianBlur(roi, (51, 51), 0)
        img[y1:y2, x1:x2] = roi

    # Save the processed image to plate_processed_folder
    plate_processed_img_path = os.path.join(plate_processed_folder, os.path.basename(full))
    cv2.imwrite(plate_processed_img_path, img[:, :, ::-1])

# Step 2: Face detection and obscuring
plate_processed_images = [f for f in os.listdir(plate_processed_folder) if f.endswith('.jpg') or f.endswith('.png')]

for i, file in enumerate(plate_processed_images):
    full = os.path.join(plate_processed_folder, file)
    print(f"Processing face detection for: {full}")
    img = cv2.imdecode(np.fromfile(full, dtype=np.uint8), cv2.IMREAD_COLOR)
    img = img[:, :, ::-1].copy()

    # Make the image writable
    img.setflags(write=1)

    # Face detection
    face_results = face_model.predict(img, save=False)
    face_boxes = face_results[0].boxes.xyxy

    for box in face_boxes:
        x1 = int(box[0])
        y1 = int(box[1])
        x2 = int(box[2])
        y2 = int(box[3])
        # Blur the region of the face
        roi = img[y1:y2, x1:x2]
        roi = cv2.GaussianBlur(roi, (51, 51), 0)
        img[y1:y2, x1:x2] = roi

    # Save the processed image to final_processed_folder
    final_processed_img_path = os.path.join(final_processed_folder, os.path.basename(full))
    cv2.imwrite(final_processed_img_path, img[:, :, ::-1])

print("All images processed and saved to the final_processed_folder directory.")
