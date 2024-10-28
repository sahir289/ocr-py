import base64
from typing import Any

import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from ocr_extractor import OCRExtractor

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
        ocr_extractor = OCRExtractor()
        results = ocr_extractor.get_extracted_data(file_data)
        print(f"results : {results}")
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        # Log and handle any other errors
        print(f"Error: {e}")
        return {"status": "failure", "data": "Something went wrong"}


if __name__ == '__main__':
    try:
        print("App server init called")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        print("Server started")
    except Exception:
        print("Exception in app start: ")
