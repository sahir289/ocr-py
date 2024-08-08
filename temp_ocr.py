import cv2
import pytesseract
import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import base64
import numpy as np
import re


app = FastAPI(
    title="Optical Character Recognition Server",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"


@app.get("/ping", tags=["readiness"])
def ping():
    """
    Ping to check is server live
    :return: dict
    """
    return {"result": "ok"}


@app.post("/ocr", tags=["get_ocr"])
def get_ocr(file_data: Any = Body(None)):
    try:
        data = file_data.get("image")
        try:
            im_bytes = base64.b64decode(data)
            im_arr = np.frombuffer(im_bytes, dtype=np.uint8)
            img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
        except:
            return {"status": "failure", "data": "Unable to convert base64 to image"}

        config = "-l Devanagari -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:' ',₹0123456789@.#/"
        result = pytesseract.image_to_string(img, config=config)
        amount_regex = r'₹([\d,]+(?:\.\d+)?)'
        twelve_digit_pattern = r'\b\d{12}\b'
        amount = re.findall(amount_regex, result)[0]
        amount = float(amount.replace(",", ""))
        transaction_id = re.findall(twelve_digit_pattern, result)[0]
        return {"status": "success", "data": {"amount": amount, "transaction_id": transaction_id}}
    except Exception as e:
        print(e)
        return {"status": "failure", "data": "Somthing went wrong"}


if __name__ == '__main__':
    try:
        print("App server init called")
        uvicorn.run(app, host="0.0.0.0", port=11000)
        print("Server started")
    except Exception:
        print("Exception in app start: ")
