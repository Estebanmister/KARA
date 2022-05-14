"""
Used to connect to the COLAB notebook that host the vision transformer
"""
import base64
import json
from io import BytesIO
import requests
from VIDI import VisualCore


class VITCloud(VisualCore):
    def __init__(self, url):
        self.api = url

    def caption(self, image, extension=None):
        if extension is None:
            extension = image.format
        return "They show you an image of " + self.__obtain(image, extension)

    def perceive(self, image, extension=None):
        if extension is None:
            extension = image.format
        return "You seem to be in " + self.__obtain(image, extension)

    def __obtain(self, image, extension):
        if extension == 'JPG':
            extension = 'JPEG'
        imagefile = BytesIO()
        image.save(imagefile, format=extension)
        b = imagefile.getvalue()
        im_bytes = b
        im_b64 = base64.b64encode(im_bytes).decode("utf8")

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        payload = json.dumps({"image": im_b64, "other_key": "value"})
        response = requests.post(self.api+"/describe", data=payload, headers=headers)
        try:
            data = response.json()
            return data['output']
        except requests.exceptions.RequestException:
            return ""