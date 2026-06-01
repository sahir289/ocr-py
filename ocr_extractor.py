import os
import re
from typing import Optional

import boto3
# import cv2
# import numpy as np
# import pytesseract

from image_processor import ImageProcessor
# # Set Tesseract path for local OCR
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# def _ensure_tessdata_prefix():
#     """Ensure TESSDATA_PREFIX points to a valid tessdata directory if possible."""
#     pref = os.environ.get('TESSDATA_PREFIX')
#     if pref and os.path.isdir(pref):
#         return pref

#     candidates = [
#         r"C:\Program Files\Tesseract-OCR\tessdata",
#         r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
#     ]

#     try:
#         exe_dir = os.path.dirname(pytesseract.pytesseract.tesseract_cmd)
#         candidates.append(os.path.join(exe_dir, 'tessdata'))
#     except Exception:
#         pass

#     for c in candidates:
#         if c and os.path.isdir(c):
#             os.environ['TESSDATA_PREFIX'] = c
#             return c

#     return None


# # Attempt to auto-set TESSDATA_PREFIX
# _ensure_tessdata_prefix()

region_name = os.environ.get('AWS_REGION')

timestamp_patterns = [
    r'(\d{1,2}\s[A-Za-z]{3,9}\s\d{4}\s*,\s*\d{1,2}:\d{2}\s[APap][Mm]{1,2})'
    r'(\d{1,2}):(\d{2})\s([APap][Mm]),\s(\d{1,2})\s([A-Za-z]+)\s(\d{4})'
    r'\b(\d{1,2}:\d{2}\s*[APMapm]{2}\s+on\s+\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})\b',
    r'(\d{1,2})\s([A-Za-z]+)\s(\d{4})\sat\s(\d{1,2}):(\d{2})\s([APap][Mm])'
    r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\s+\d{1,2}:\d{2}\s*[APMapm]{2})\b',
    r'\b(\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}:\d{2})\b',
    r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?)\b',
    r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',
    r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4}\s+\d{1,2}:\d{2}\s*[APMapm]{0,2})\b',
    r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4},?\s+\d{1,2}:\d{2}\s*[APMapm]{2})\b',
    r'\b(\d{1,2}:\d{2}\s*[APMapm]{2})\b',
    r'\b(\d{2}:\d{2}:\d{2})\b',
    r'\b(\d{4}[-/]\d{2}[-/]\d{2})\b',
    r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4},\s+\d{1,2}:\d{2}\s*[APMapm]{2})\b'
]

class OCRExtractorpayout:
    def __init__(self):
        # AWS Textract client (commented out for local development)
        self.client = boto3.client('textract', region_name=region_name)
        # self.client = None  # Using local OCR instead
        self.results = {
            "amount": None,
            "transaction_id": None,
            "bank_name": None,
            "timestamp": None
        }

    def process_document(self, im_bytes):
        try:
            # # Local OCR using Tesseract (instead of AWS Textract)
            # # Decode bytes to image
            # im_arr = np.frombuffer(im_bytes, dtype=np.uint8)
            # img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
            
            # # Resize image for better OCR
            # shape = img.shape
            # img = cv2.resize(img, (int(shape[1] * 1.6), int(shape[0] * 1.6)))
            
            # # OCR configuration
            # config = "-l Devanagari --psm 4 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:,₹0123456789@.#/"
            # text = pytesseract.image_to_string(img)
            
            # # Convert text to blocks format similar to AWS Textract
            # blocks = []
            # lines = text.split('\n')
            # for line in lines:
            #     if line.strip():
            #         # Add LINE block
            #         blocks.append({
            #             "BlockType": "LINE",
            #             "Text": line.strip()
            #         })
            #         # Add WORD blocks for each word in the line
            #         words = line.split()
            #         for word in words:
            #             if word.strip():
            #                 blocks.append({
            #                     "BlockType": "WORD",
            #                     "Text": word.strip()
            #                 })
            
            # # print(f"Local OCR result blocks: {len(blocks)}")
            # return blocks
            
            # # AWS Textract code (commented out)
            result_json = self.client.detect_document_text(
                Document={'Bytes': im_bytes})
            print(f"result_json : {result_json['Blocks']}")
            return result_json["Blocks"]
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    def get_extracted_data(self, file_data) -> dict:
        try:
            img_data = file_data.get("image")

            """Base case with the original image"""
            im_bytes = ImageProcessor.image_base64_decode(img_data)
            self.data_Extraction_helper(im_bytes)

            if None in (self.results["amount"], self.results["transaction_id"]):
                print("Inverting image for better results.")
                print(f"Current results : {self.results}")
                im_bytes = ImageProcessor.invert_image(img_data)
                self.data_Extraction_helper(im_bytes)
                print(f"Updated results : {self.results}")

            return self.results
        except Exception as e:
            print(f"get_extracted_data Error : {e}")
            raise


    def data_Extraction_helper(self, im_bytes):
        text_blocks = self.process_document(im_bytes)

        if self.results["amount"] is None:
            self.results["amount"] = self.extract_amount(text_blocks)

        if self.results["transaction_id"] is None:
            self.results["transaction_id"] = self.extract_transaction_id(
                text_blocks)

        if self.results["bank_name"] is None:
            self.results["bank_name"] = self.extract_bank_name(text_blocks)

        if self.results["timestamp"] is None:
            self.results["timestamp"] = self.extract_timestamp(text_blocks)


    def extract_amount(self, text_blocks):
        amount = None
        for block in text_blocks:
            if block["BlockType"] != "WORD":
                continue

            text = block["Text"]
            cleaned_text = str(text).replace(" ", "")

            if "₹" in text:
                amount = self.extract_rupee(cleaned_text)

        if amount is None:
            amount = self.extract_fallback_amount(text_blocks)

        if amount:
            amount = str(amount)

        return amount

    @staticmethod
    def extract_rupee(text: str) -> Optional[float]:
        try:
            amount_match = re.search(r'₹\s*([\d,]+(?:\.\d{2})?)', text)
            if amount_match:
                amount_str = amount_match.group(1).replace(",", "").replace(
                    " ", "")
                return float(amount_str)
        except Exception as exc:
            print(f"Error in extract_rupee: {exc}")


    def extract_transaction_id(self, text_blocks):
        # first preference
        for block in text_blocks:
            if block["BlockType"] != "WORD":
                try:
                    text = str(block["Text"])

                    # Extract Bank Trans Id or UTR Number value
                    bank_trans_pattern = r'(?:Bank\s+Trans\s+Id\.?\:?|UTR\s+Number\.?\:?)\s*(\d{12})'
                    match = re.search(bank_trans_pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                except Exception as exc:
                    print(f"Error in extract_transaction_id with LINE : {exc}")
                continue
            try:
                text = block["Text"]
                cleaned_text = str(text)  # ❗ don't remove spaces

                pattern = r'(\b\d{12}\b|' \
                        r'NEFT[-/: ]?[A-Z0-9]+|' \
                        r'NEFT\s+UTR\s*[:\-]?\s*[A-Z0-9]+|' \
                        r'RTGS[-/: ]?[A-Z0-9]+|' \
                        r'RTGS\s+UTR\s*[:\-]?\s*[A-Z0-9]+|' \
                        r'IMPS[-/: ]?[A-Z0-9]+|' \
                        r'2A[-/: ]?[12]+\b|' \
                        r'IMPS\s+UTR\s*[:\-]?\s*[A-Z0-9]+|' \
                        r'IMPS\s+Ref(?:erence)?\s*(?:No\.?|Number)?\s*[:\-]?\s*\d{10,20})'

                match = re.search(pattern, cleaned_text, re.IGNORECASE)  # ✅ FIXED

                if match:
                    text = match.group(0)

                    result = re.findall(r'[^:/-]+$', text.strip())[-1]
                    return result

                cleaned_text = str(text).replace(" ", "")
                pattern = r'UTR:\s*(\s*\d{12})'
                match = re.search(pattern, cleaned_text)
                if match:
                    return match.group(1).strip()

            except Exception as exc:
                print(f"Error in extract_transaction_id: {exc}")

        # second preference
        for block in text_blocks:
            if block["BlockType"] != "LINE":
                continue
            try:
                text = block["Text"]
                cleaned_text = str(text).replace(" ", "")

                pattern = r'\b[\w\s\.]+:\s*(\d{12})\b'
                match = re.search(pattern, cleaned_text)
                if match:
                    return match.group(1).strip()

            except Exception as exc:
                print(f"Error in extract_transaction_id: {exc}")

    def extract_fallback_amount(self, text_blocks):
        for block in text_blocks:
            if block["BlockType"] not in ("WORD", "LINE"):
                continue

            try:
                text = block["Text"]
                text = str(text).lower()

                amount = re.search(r'(?:amount|settled\s+amt)[\s:]*([\d,]+(?:\.\d{2})?)',
                                   text, re.IGNORECASE)
                if amount:
                    return amount.group(1)

                amount = re.search(
                    r'\d{1,3}(?:,\d{1,3})+(?:\.\d{2})?\b|\d+\.\d{2}\b',
                    text)
                if amount:
                    return amount.group(0)

            except Exception as exc:
                print(f"extract_fallback_amount Error : {exc}")

    def extract_bank_name(self, text_blocks):
        for block in text_blocks:
            if block["BlockType"] != "LINE":
                continue

            try:
                text = str(block["Text"])
                if re.search(r'\b\w+\s+bank\b|\bbank\s+\w+\b', text,
                             re.IGNORECASE):
                    return block["Text"]
            except Exception as exc:
                print(f"extract_bank_name Error : {exc}")

    def extract_timestamp(self, text_blocks):
        try:
            timestamps = []
            for block in text_blocks:
                if block["BlockType"] != "LINE":
                    continue

                try:
                    text = str(block["Text"])

                    for pattern in timestamp_patterns:
                        match = re.search(pattern, text)
                        if match:
                            timestamps.append(text)

                except Exception as exc:
                    print(f"extract_bank_name Error : {exc}")

            return max(timestamps, key=len)
        except Exception as exc:
            print(f"extract_bank_name Error : {exc}")


class OCRExtractorpayin:
    def __init__(self):
        # AWS Textract client (commented out for local development)
        # self.client = boto3.client('textract', region_name=region_name)
        self.client = None  # Using local OCR instead
        self.results = {
            "amount": None,
            "transaction_id": None,
            "bank_name": None,
            "timestamp": None
        }

    def process_document(self, im_bytes):
        try:
            # # Local OCR using Tesseract (instead of AWS Textract)
            # # Decode bytes to image
            # im_arr = np.frombuffer(im_bytes, dtype=np.uint8)
            # img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
            
            # # Resize image for better OCR
            # shape = img.shape
            # img = cv2.resize(img, (int(shape[1] * 1.6), int(shape[0] * 1.6)))
            
            # # OCR configuration
            # text = pytesseract.image_to_string(img)
            
            # # Convert text to blocks format similar to AWS Textract
            # blocks = []
            # lines = text.split('\n')
            # for line in lines:
            #     if line.strip():
            #         # Add LINE block
            #         blocks.append({
            #             "BlockType": "LINE",
            #             "Text": line.strip()
            #         })
            #         # Add WORD blocks for each word in the line
            #         words = line.split()
            #         for word in words:
            #             if word.strip():
            #                 blocks.append({
            #                     "BlockType": "WORD",
            #                     "Text": word.strip()
            #                 })
            
            # # print(f"Local OCR result blocks: {len(blocks)}")
            # return blocks
            
            # AWS Textract code (commented out)
            result_json = self.client.detect_document_text(
                Document={'Bytes': im_bytes})
            print(f"result_json : {result_json['Blocks']}")
            return result_json["Blocks"]
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    def get_extracted_data(self, file_data) -> dict:
        try:
            img_data = file_data.get("image")

            """Base case with the original image"""
            im_bytes = ImageProcessor.image_base64_decode(img_data)
            self.data_Extraction_helper(im_bytes)

            if None in (self.results["amount"], self.results["transaction_id"]):
                print("Inverting image for better results.")
                print(f"Current results : {self.results}")
                im_bytes = ImageProcessor.invert_image(img_data)
                self.data_Extraction_helper(im_bytes)
                print(f"Updated results : {self.results}")

            return self.results
        except Exception as e:
            print(f"get_extracted_data Error : {e}")
            raise


    def data_Extraction_helper(self, im_bytes):
        text_blocks = self.process_document(im_bytes)

        if self.results["amount"] is None:
            self.results["amount"] = self.extract_amount(text_blocks)

        if self.results["transaction_id"] is None:
            self.results["transaction_id"] = self.extract_transaction_id(
                text_blocks)

        if self.results["bank_name"] is None:
            self.results["bank_name"] = self.extract_bank_name(text_blocks)

        if self.results["timestamp"] is None:
            self.results["timestamp"] = self.extract_timestamp(text_blocks)


    def extract_amount(self, text_blocks):
        amount = None
        for block in text_blocks:
            if block["BlockType"] != "WORD":
                continue

            text = block["Text"]
            cleaned_text = str(text).replace(" ", "")

            if "₹" in text:
                amount = self.extract_rupee(cleaned_text)

        if amount is None:
            amount = self.extract_fallback_amount(text_blocks)

        if amount:
            amount = str(amount)

        return amount

    @staticmethod
    def extract_rupee(text: str) -> Optional[float]:
        try:
            amount_match = re.search(r'₹\s*([\d,]+(?:\.\d{2})?)', text)
            if amount_match:
                amount_str = amount_match.group(1).replace(",", "").replace(
                    " ", "")
                return float(amount_str)
        except Exception as exc:
            print(f"Error in extract_rupee: {exc}")


    def extract_transaction_id(self, text_blocks):
        # first preference
        for block in text_blocks:
            if block["BlockType"] != "WORD":
                continue
            try:
                text = block["Text"]
                cleaned_text = str(text).replace(" ", "")

                pattern = r'^\d{12}$'
                match = re.match(pattern, cleaned_text)

                if match:
                    return match.group(0).strip()

                pattern = r'UTR:\s*(\s*\d{12})'
                match = re.search(pattern, cleaned_text)
                if match:
                    return match.group(1).strip()

            except Exception as exc:
                print(f"Error in extract_transaction_id: {exc}")

        # second preference
        for block in text_blocks:
            if block["BlockType"] != "LINE":
                continue
            try:
                text = block["Text"]
                cleaned_text = str(text).replace(" ", "")

                pattern = r'\b[\w\s\.]+:\s*(\d{12})\b'
                match = re.search(pattern, cleaned_text)
                if match:
                    return match.group(1).strip()

            except Exception as exc:
                print(f"Error in extract_transaction_id: {exc}")

    def extract_fallback_amount(self, text_blocks):
        for block in text_blocks:
            if block["BlockType"] not in ("WORD", "LINE"):
                continue

            try:
                text = block["Text"]
                text = str(text).lower()

                amount = re.search(r'amount[\s:]*([\d,]+(?:\.\d{2})?)',
                                   text, re.IGNORECASE)
                if amount:
                    return amount.group(1)

                amount = re.search(
                    r'\d{1,3}(?:,\d{1,3})+(?:\.\d{2})?\b|\d+\.\d{2}\b',
                    text)
                if amount:
                    return amount.group(0)

            except Exception as exc:
                print(f"extract_fallback_amount Error : {exc}")

    def extract_bank_name(self, text_blocks):
        for block in text_blocks:
            if block["BlockType"] != "LINE":
                continue

            try:
                text = str(block["Text"])
                if re.search(r'\b\w+\s+bank\b|\bbank\s+\w+\b', text,
                             re.IGNORECASE):
                    return block["Text"]
            except Exception as exc:
                print(f"extract_bank_name Error : {exc}")

    def extract_timestamp(self, text_blocks):
        try:
            timestamps = []
            for block in text_blocks:
                if block["BlockType"] != "LINE":
                    continue

                try:
                    text = str(block["Text"])

                    for pattern in timestamp_patterns:
                        match = re.search(pattern, text)
                        if match:
                            timestamps.append(text)

                except Exception as exc:
                    print(f"extract_bank_name Error : {exc}")

            return max(timestamps, key=len)
        except Exception as exc:
            print(f"extract_bank_name Error : {exc}")
