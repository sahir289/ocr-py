import base64
import io

import cv2
import numpy as np
from PIL import Image


class ImageProcessor:

    @staticmethod
    def convert_image_to_bw_base64(base64_string):
        try:
            if base64_string.startswith("data:image"):
                base64_string = base64_string.split(",")[1]

            image_data = ImageProcessor.image_base64_decode(base64_string)

            with Image.open(io.BytesIO(image_data)) as image:
                bw_image = image.convert("L")

                buffered = io.BytesIO()
                bw_image.save(buffered, format="PNG")

                bw_base64_string = buffered.getvalue()

            return bw_base64_string

        except Exception as e:
            print(f"Error converting image to black and white: {e}")
            return None

    @staticmethod
    def invert_image(base64_string):
        try:

            image_data = base64.b64decode(base64_string)
            np_array = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("Could not decode the image from base64.")

            inverted_image = cv2.bitwise_not(image)
            _, buffer = cv2.imencode('.png', inverted_image)
            image_bytes = buffer.tobytes()
            return image_bytes

        except Exception as e:
            print(f"Error converting image to black and white: {e}")
            return None

    @staticmethod
    def image_base64_decode(data):
        im_bytes = base64.b64decode(data)
        return im_bytes
