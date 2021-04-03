from dataclasses import dataclass

import boto3

from lib.constants import SqsDataType

SQS_OVERPASS = 'overpass'
SQS_WIKIDATA = 'wikidata'

queues = {
    'wikidata_claims': 'https://sqs.eu-central-1.amazonaws.com/238713673548/wikidata-claims',
    'overpass_workload': 'https://sqs.eu-central-1.amazonaws.com/238713673548/overpass_workload',
}


@dataclass
class MessageAttribute:
    key: str
    datatype: SqsDataType
    value: str


class Sqs:
    def __init__(self):
        self.client = boto3.client('sqs')

    def send_message(self, queue: str, message_attributes: list[MessageAttribute]):
        attr = dict()

        for item in message_attributes:
            attr[item.key] = {
                'DataType': item.datatype.value,
                'StringValue': str(item.value),
            }

        self.client.send_message(
            QueueUrl=queue,
            MessageAttributes=attr,
            MessageBody='Data',
        )

    def receive_message(self, queue):
        return self.client.receive_message(
            QueueUrl=queue,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
        )

    def delete_message(self, queue: str, receipt_handle: str):
        self.client.delete_message(
            QueueUrl=queue,
            ReceiptHandle=receipt_handle
        )
