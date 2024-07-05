To perform license plate region detection using YOLOv8, follow these steps:
Make sure to place the training data and label files in the `data/car` directory, sourced from the Kaggle license plate dataset.
https://www.kaggle.com/datasets/andrewmvd/car-plate-detection
1. Execute `xml2txt.py` to convert XML annotations to text format.
2. Next, run `split.py` to split the dataset into training and validation sets.
3. Finally, use `train.py` to train the YOLOv8 model for license plate region detection.

Make sure to have the necessary dependencies installed and the dataset properly prepared before executing these scripts.

Make sure to modify the `car_data.yaml` file path to the correct `train` and `valid` folders. 
The trained weight file will be saved at `runs/detect/train/weights/best.pt`, please change it to `best_plate.pt`.

4. For face recognition, use the pre-trained model located at `/runs/detect/train/weights/best_face.pt`.

To perform image blurring, execute `licenseplate_humanface_erase.py` and place the images to be processed in the `Process/original` folder.
During the process, the license plate data will be first processed and placed in the `Process/plate_processed` folder, followed by facial blurring. 
The final processed data will be stored in the `Process/final_processed` folder.

