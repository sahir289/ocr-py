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


def extract_rupee(result, random=False):
    amount = None
    if "₹" in result:
        amount = re.search(r'₹\s*([\d,]+(?:\.\d{2})?)', result)
        # amount = re.search(r'₹\s*([\d\s,]+(?:\.\s*\d{2})?)', result)
        if amount:
            amount = amount.group(1)
    elif "amount" in result or "Amount" in result:
        amount = re.search(r'amount[\s:]*([\d,]+(?:\.\d{2})?)', result, re.IGNORECASE)
        if amount:
            amount = amount.group(1)
    elif random:
        # amount = re.search(r'\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\b\d+\.\d{2}\b', result)
        amount = re.search(r'\d{1,3}(?:,\d{1,3})+(?:\.\d{2})?\b|\d+\.\d{2}\b', result)
        if amount:
            amount = amount.group(0)
    try:
        if amount:
            amount = float(str(amount).replace(",", "").replace(" ", ""))
    except Exception as e:
        print(e)
    return amount


def extract_transaction_id(text):
    try:
        pattern = r'\b\d{12}\b'
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        # Remove spaces between digits to handle cases where spaces are present
        for t in text.split("\n"):
            text_normalized = re.sub(r'(?<=\d)\s+(?=\d)', '', t)
            # Regular expression to find exactly 12 consecutive digits
            # Search for the first match in the normalized text
            match = re.search(pattern, text_normalized)
            if match:
                return match.group(0)  # Return the matched 12-digit number

        return None  # Return None if no match found
    except Exception as e:
        print(e)
        return None


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

        shape = img.shape
        img = cv2.resize(img, (int(shape[1] * 1.6), int(shape[0] * 1.6)))
        config = "-l Devanagari --psm 4 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:' ',₹0123456789@.#/"
        result = pytesseract.image_to_string(img, config=config)
        amount = extract_rupee(result)
        transaction_id = extract_transaction_id(result)

        if amount is None or transaction_id is None:
            img_copy = 255 - img
            result1 = pytesseract.image_to_string(img_copy, config=config)
            if amount is None:
                amount = extract_rupee(result1, True)
            if transaction_id is None:
                transaction_id = extract_transaction_id(result1)
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
