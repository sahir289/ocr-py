import os
import re
from typing import Optional

import boto3

from image_processor import ImageProcessor

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

class OCRExtractor:
    def __init__(self):
        self.client = boto3.client('textract', region_name=region_name)
        self.results = {
            "amount": None,
            "transaction_id": None,
            "bank_name": None,
            "timestamp": None
        }

    def process_document(self, im_bytes):
        try:
            # Detect document text using AWS Textract
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
