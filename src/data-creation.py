import cv2
import numpy as np
from datetime import datetime, timedelta
import base64
from PIL import Image
from io import BytesIO
from pymongo import MongoClient

# Step 1: Create a timestamp sequence
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 1, 12)
delta = timedelta(minutes=30)

timestamps = [] 
while start_date <= end_date:
    timestamps.append(start_date)
    start_date += delta

# Step 2: Generate an image with text, convert it to base64
def create_image(id, text):
    # Create a blank 200x200 black image
    image = np.zeros((200,200,3), np.uint8)

    # Put the text in the image
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, text, (50,100), font, 1, (255,255,255), 2, cv2.LINE_AA)
    
    # Convert image to base64
    pil_img = Image.fromarray(image)
    buff = BytesIO()
    pil_img.save(buff, format="PNG")
    img_str = base64.b64encode(buff.getvalue())

    return img_str.decode('utf-8')

# Create images and ids
ids = list(range(1, len(timestamps) + 1))
images = [create_image(i, str(i)) for i in ids]

# Step 3: Create a MongoClient and the collection
client = MongoClient('mongodb://root:example@localhost:27017/')
db = client.test
collection = db.test_collection

# Insert all the information into MongoDB
for id, timestamp, image in zip(ids, timestamps, images):
    doc = {'ID': id, 'date': timestamp, 'Image': image}
    collection.insert_one(doc)

# Step 4: Query the collection to verify the data
for doc in collection.find():
    print(doc)