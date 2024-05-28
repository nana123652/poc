import json
import boto3
from botocore.client import Config, BotoCoreError, ClientError
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

class AWSWellArchTool(Tool):
    name = "well_architected_tool"
    description = "Use this tool for any AWS related question to help customers understand best practices on building on AWS. It will use the relevant context from the AWS Well-Architected Framework to answer the customer's query. The input is the customer's question. The tool returns an answer for the customer using the relevant context."
    inputs = ["text"]
    outputs = ["text"]

    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name='us-east-1')

    def qa_chain(self, query):
        # Find relevant docs using embeddings
        embeddings = HuggingFaceEmbeddings()
        vectorstore = FAISS.load_local("local_index", embeddings, allow_dangerous_deserialization=True)
        docs = vectorstore.similarity_search(query)

        doc_sources_string = "\n".join(doc.metadata["source"] for doc in docs)

        # Prepare the prompt
        prompt_template = """Use the following pieces of context to answer the question at the end.
        {context}
        Question: {question}
        Answer:"""
        prompt = prompt_template.format(context=doc_sources_string, question=query)

        bedrock_model_id = "ai21.j2-ultra-v1"  # Set the foundation model
        # Invoke the Bedrock model
        try:
            body = json.dumps({
                "prompt": prompt,
                "maxTokens": 1024,
                "temperature": 0,
                "topP": 0.5,
                "stopSequences": [],
                "countPenalty": {"scale": 0},
                "presencePenalty": {"scale": 0},
                "frequencyPenalty": {"scale": 0}
            })
            response = self.client.invoke_model(body=body, modelId=bedrock_model_id, accept='application/json', contentType='application/json')
            response_body = json.loads(response.get('body').read())
            response_text = response_body.get("completions")[0].get("data").get("text")
            print("Generated answer:")
            print(response_text)
            return {"ans": str(response_text), "docs": doc_sources_string}

        except (BotoCoreError, ClientError) as error:
            print("Error:", error)
            raise error

    def __call__(self, query):
        result = self.qa_chain(query)
        return {result}