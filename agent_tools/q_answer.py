import json
import boto3
#from botocore.client import Config, BotoCoreError, ClientError
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from transformers import Tool

class QATool(Tool):
    name = "question_answering_tool"
    description = "Use this tool to answer any questions"
    inputs = ["text"]
    outputs = ["text"]

    # Constructor :  initialize objects of a class
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name='us-east-1')

    def qa_chain(self, query):
        bedrock_model_id = "ai21.j2-ultra-v1"  # AI21 Labs Set the foundation model https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
        # Invoke the Bedrock model
        try:
            body = json.dumps({
                "prompt": query,
                "maxTokens": 1024,
                "temperature": 0,
                "topP": 0.5,
                "stopSequences": [],
                "countPenalty": {"scale": 0},
                "presencePenalty": {"scale": 0},
                "frequencyPenalty": {"scale": 0}
            })

            # GENERATION
            response = self.client.invoke_model(body=body, modelId=bedrock_model_id, accept='application/json', contentType='application/json')
            response_body = json.loads(response.get('body').read())
            response_text = response_body.get("completions")[0].get("data").get("text")
            print("Generated answer:")
            print(response_text)
            return str(response_text)

        except Exception as error:
            print("Error:", error)
            raise error

    def __call__(self, query):
        result = self.qa_chain(query)
        print(result)
        return result
