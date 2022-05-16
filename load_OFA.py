"""
Works nicely, still have to figure out the limits of the public API
"""
import requests
import base64
from io import BytesIO
from VIDI import VisualCore
import os

# If you are building a bigger application, you might want to replace this with a paid api
hugging_face_api = 'https://hf.space/embed/OFA-Sys/OFA-Image_Caption/+/api/predict/'

headers = {"Authorization": os.getenv("HUG_API")}


class OFACore(VisualCore):
    def __init__(self):
        pass

    def describe(self, image, extension):
        if extension == 'JPG':
            extension = 'JPEG'
        imagefile = BytesIO()
        image.save(imagefile, format=extension)
        b = imagefile.getvalue()
        my_string = base64.b64encode(b)
        my_string = my_string.decode('utf-8')

        r = requests.post(url=hugging_face_api, headers=headers,json={"data":
                  ["data:image/jpeg;base64,"+my_string]})
        return r.json()['data'][0]

    def caption(self, image):
        return "They show you an image of " + self.describe(image)[0]

    def perceive(self, image):
        return "You seem to be in " + self.describe(image)[0]