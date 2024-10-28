from collections import defaultdict
from typing import Any

import boto3


class OCRQueryExtractor:
    def __init__(self, file_data: Any):
        self.file_data = file_data
        self.client = boto3.client('textract')
        self.queries = [
            {
                'Text': 'What is the transaction amount?',
                'Alias': 'amount',
                'Pages': ["1"]
            },
            {
                'Text': 'What is the transaction ID?',
                'Alias': 'transaction_id',
                'Pages': ["1"]
            },
            {
                'Text': "What bank processed this transaction? Include any text that mentions 'bank'.",
                'Alias': 'bank_name',
                'Pages': ["1"]
            },
            {
                "Text": "Please provide the date and time when the transaction occurred.",
                'Alias': 'timestamp',
                'Pages': ["1"]
            }
        ]

    def process_document(self):
        try:
            # Detect document text using AWS Textract
            result_json = self.client.analyze_document(
                Document={'Bytes': self.file_data},
                FeatureTypes=["QUERIES"],
                QueriesConfig={"Queries": self.queries}
            )
            print(f"result_json : {result_json['Blocks']}")
            return result_json["Blocks"]
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    def get_extracted_data(self) -> dict:
        text_blocks = self.process_document()
        resp_dict = self.__gen_resp_dict(text_blocks)
        return resp_dict

    def __gen_resp_dict(self, text_blocks):
        query_result_map = {}
        for block in text_blocks:
            if block["BlockType"] == "QUERY_RESULT":
                block_id = block["Id"]
                block_val = block["Text"]
                query_result_map[block_id] = block_val

        query_val_map = {
            "amount": [],
            "transaction_id": [],
            "bank_name": [],
            "timestamp": []
        }
        for block in text_blocks:
            if block["BlockType"] == "QUERY":
                alias = block["Query"]["Alias"]
                for rels in block.get("Relationships", []):
                    if rels["Type"] == "ANSWER":
                        for answer_id in rels.get("Ids", []):
                            query_val_map[alias].append(
                                query_result_map[answer_id])

        for key, vals in query_val_map.items():
            query_val_map[key] = "\n".join(vals)

        print(f"query_val_map : {query_val_map}")
        return query_val_map
