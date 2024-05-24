import json
import os
import subprocess
from typing import Dict

import requests
from langchain import PromptTemplate, SagemakerEndpoint
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.prompts.prompt import PromptTemplate
from langchain.vectorstores import FAISS
from PIL import Image
from transformers import Tool
from transformers.tools import HfAgent
from langchain_community.chat_models.bedrock import BedrockChat
from langchain.retrievers.bedrock import AmazonKnowledgeBasesRetriever
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import boto3
import pprint
from botocore.client import Config
import json

session = boto3.session.Session()
print('Sessions region: ',session.region_name)
region = 'us-east-1'
bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_client = boto3.client('bedrock-runtime', region_name = region)
bedrock_agent_client = boto3.client("bedrock-agent-runtime",
                              config=bedrock_config, region_name = region)

print(region)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
HUGGING_FACE_KEY = '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'
modelId = 'anthropic.claude-3-sonnet-20240229-v1:0' # change this to use a different version from the model provider
kb_id = "<knowledge base id>"


sa_prompt = """
You are an expert AWS Certified Solutions Architect. Your role is to help customers understand best practices on building on AWS. You will generate Python commands using available tools to help will customers solve their problem effectively.
To assist you, you have access to three tools. Each tool has a description that explains its functionality, the inputs it takes, and the outputs it provides.
First, you should explain which tool you'll use to perform the task and why. Then, you'll generate Python code. Python instructions should be simple assignment operations. You can print intermediate results if it's beneficial.

Tools:
<<all_tools>>

Task: "Help customers understand best practices on building on AWS by using relevant context from the AWS Well-Architected Framework."

I will use the AWS Well-Architected Framework Query Tool because it provides direct access to AWS Well-Architected Framework to extract information.

Answer:
```py
response = well_architected_tool(query="How can I design secure VPCs?")
print(f"{response}.")
```

Task: "Write a function in Python to upload a file to Amazon S3"

I will use the Code Generation Tool because it can generate code based on the provided requirements.

Answer:
```py

python_code = code_generation_tool(prompt="Write a function in Python to upload a file to Amazon S3")
print(f"{python_code}")
```

Task: "Create a diagram for the following architecture: three EC2 instances connected to an S3 bucket and a RDS database."

I will use the Diagram Creation Tool because it can create insightful diagrams to represent the given AWS architecture.

Answer:

```py
architecture_diagram = diagram_creation_tool(query="Three EC2 instances connected to an S3 bucket and a RDS database.")
```


Task: "<<prompt>>"

I will use the following
"""
class AWSCatalogTool(Tool):
    name = "aws_catalog_tool"
    description = "Use this tool to run an AWS Service Catalog product."
    client = boto3.client('servicecatalog',region_name='us-east-1')
    def get_provisioned_product_status(product_id):
        try:
            response = client.describe_provisioned_status(Id=product_id)
            return response['ProvisionedProductDetail']['Status']
        except Exception as e:
             print(f'An error occured while getting status: {str(e)}')
             return None

    def wait_for_status(product_id, target_status, max_attempts=10, interval_seconds=10):
        print(f'target reponse to check: {product_id}')
        attempts= 0
        while attempts < max_attempts:
            status = get_provisioned_product_status(product_id)
            print(f"status: {status}")
            if status == target_status:
                print(f'Provisioned Product reached target status: {status}')
                return f'Provisioned Product reached target status: {status}'
                break
            elif status == 'FAILED':
                print(f'Provisioned Product failed with status: {status}')
                return f'Provisioned Product failed with status: {status}'
                break
            else:
                print(f"Current status: {status}. Waiting for {target_status}...")
                return f"Current status: {status}. Waiting for {target_status}..."
                time.sleep(interval_seconds)
                attempt += 1
        else:
            print(f"Max attempts reached. Provisioned Product status: {status}")
            return f"Max attempts reached. Provisioned Product status: {status}"



    def __call__(self,product_name: str):
        try:
            self.client = boto3.client('servicecatalog',region_name='us-east-1')
            product = self.client.search_products(Filters={'FullTextSearch': [product_name]})['ProductViewSummaries'][0]
            print(product)
            response = self.client.provision_product(ProductId=product['ProductId'],ProvisionedProductName='37sssieersrq43444ss5',ProvisioningArtifactId='pa-mhftvd4y7zkdg')
            print(response)
            self.product_id=response['RecordDetail']['ProvisionedProductId']
            self.target_status = 'COMPLETED'
            print(f"product id: {product_id} | target_status: {target_status} -- pass to wait_for_status func ")
            status_response = wait_for_status(self.product_id,self.target_status)
            #if response['RecordDetail']:
             #   print("Product provisioned successfully.")
              #  print("Product details:")
                #for output in response['RecordDetail']:
                    #print(f"{output['OutputKey']} = {output['OutputValue']}")
            #else:
             #   response = "Provisioning failed"
              #  print("Error provisioning product.")i
            print(status_response)
            return status_response
            
        except Exception as e:
            print(f'An error occured: {str(e)}')
            response= f'An error occured: {str(e)}'
            return response
        #response = self.client.execute_product(
         #   ProductId=product_id,
          #  ProvisioningArtifactId='your_provisioning_artifact_id',
          #  AcceptLanguage='en'
        # )
        #print(response)
        #return response
    #def run(self, product_name: str):
     #   product = self.client.search_products(Name=product_name)['ProductViewSummaryList'][0]
      #  response = self.client.provision_product(ProductId=product['ProductId'])
       # if response['RecordOutputs']:
        #    print("Product provisioned successfully.")
      #   #   print("Product details:")
       #     for output in response['RecordOutputs']:
    #            print(f"{output['OutputKey']} = {output['OutputValue']}")
     #   else:
         #   print("Error provisioning product.")
        ##response = self.client.execute_product(
         #   ProductId=product_id,
          #  ProvisioningArtifactId='your_provisioning_artifact_id',
          #  AcceptLanguage='en'
    # )
        #print(response)
        #return response

class AWSWellArchTool(Tool):
    name = "well_architected_tool"
    description = "Use this tool for any AWS related question to help customers understand best practices on building on AWS. It will use the relevant context from the AWS Well-Architected Framework to answer the customer's query. The input is the customer's question. The tool returns an answer for the customer using the relevant context."
    inputs = ["text"]
    outputs = ["text"]

    def qa_chain(self):
        prompt_template = """Use the following pieces of context to answer the question at the end.

        {context}

        Question: {question}
        Answer:"""
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        class ContentHandler(LLMContentHandler):
            content_type = "application/json"
            accepts = "application/json"

            def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
                # clean prompt
                prompt = prompt.replace("\\n,", "").replace("\n", "").strip()

                payload = {
                    "prompt": prompt,
                    "maxTokens": 2048,
                    "temperature": 0.7,
                    "numResults": 1,
                }

                payload = json.dumps(payload).encode("utf-8")
                return payload

            def transform_output(self, output: bytes) -> str:
                response_json = json.loads(output.read().decode("utf-8"))
                print(response_json)
                return response_json["completions"][0]["data"]["text"]
        
        inference_component_name='meta-textgeneration-llama-3-8b-20240523-055253'
        content_handler = ContentHandler()
        llm=SagemakerEndpoint(
                endpoint_name="jumpstart-dft-meta-textgeneration-l-20240523-055253",
                region_name="us-east-1",
                endpoint_kwargs={"InferenceComponentName":inference_component_name}, 
                #endpoint_kwargs={f'InferenceComponentName": {inference_component_name}'},
                #endpoint_kwargs={"CustomAttributes": "accept_eula=true,InferenceComponentName="+inference_component_name },
                #credentials_profile_name="default",
                content_handler=content_handler,
        )
        print(str(llm.endpoint_kwargs))
        # Setup chain
        chain = load_qa_chain(
            llm,
            prompt=PROMPT,
        )

        return chain

    def __call__(self, query):
        chain = self.qa_chain()
        # Find docs
        embeddings = HuggingFaceEmbeddings()
        vectorstore = FAISS.load_local("local_index", embeddings, allow_dangerous_deserialization=True)
        docs = vectorstore.similarity_search(query)

        doc_sources_string = ""
        for doc in docs:
            doc_sources_string += doc.metadata["source"] + "\n"

        results = chain(
            {"input_documents": docs, "question": query}, return_only_outputs=True
        )

        resp_json = {"ans": str(results["output_text"]), "docs": doc_sources_string}

        return resp_json

class CodeGenerationTool(Tool):
    name = "code_generation_tool"
    description = "Use this tool only when you need to generate code based on a customers's request. The input is the customer's question. The tool returns code that the customer can use."

    inputs = ["text"]
    outputs = ["text"]

    def call_endpoint(self, payload):
        API_URL = "https://nnu78adxthljszhh.us-east-1.aws.endpoints.huggingface.cloud"
        headers = {"Authorization": f"Bearer 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"}
        response = requests.post(API_URL, headers=headers, json=payload)
        #print('ssss...........: ', response)
        return response.json()

    def __call__(self, prompt):
        print(f'here pomt: {prompt}')
        output = self.call_endpoint(
            {
                "inputs": prompt,
                "parameters": {
                    "do_sample": False,
                    "max_new_tokens": 500,
                    "return_full_text": False,
                    "temperature": 0.01,
                },
            }
        )
        print(output)
        generated_text = output[0]["generated_text"]

        #print(f'generated_code: {generated_text}')
        # Clean up code
        lines = generated_text.split("\n")
        updated_lines = []

        for line in lines:
            if line == ".":
                line = line.replace(".", "")
            if "endoftext" in line:
                line = ""

            updated_lines.append(line)

        # Join the updated lines to create the updated code
        updated_code = "\n".join(updated_lines)

        return updated_code


class DiagramCreationTool(Tool):
    name = "diagram_creation_tool"
    description = (
        "This is a tool that generates diagrams based on a customers's request."
    )
    inputs = ["text"]
    outputs = ["image"]

    def save_and_run_python_code(self, code: str, file_name: str = "test_diag.py"):
        # Save the code to a file
        with open(file_name, "w") as file:
            file.write(code)

        # Run the code using a subprocess
        try:
            result = subprocess.run(
                ["python", file_name], capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            print("Error occurred while running the code:")
            print(e.stdout)
            print(e.stderr)

    def process_code(self, code):
        # Split the code into lines
        lines = code.split("\n")

        # Initialize variables to store the updated code and diagram filename
        updated_lines = []
        diagram_filename = None
        inside_diagram_block = False

        for line in lines:
            if line == ".":
                line = line.replace(".", "")
            if "endoftext" in line:
                line = ""
            if "# In[" in line:
                line = ""

            # Check if the line contains "with Diagram("
            if "with Diagram(" in line:
                # Extract the diagram name between "with Diagram('NAME',"
                diagram_name = (
                    line.split("with Diagram(")[1].split(",")[0].strip("'").strip('"')
                )

                # Convert the diagram name to lowercase, replace spaces with underscores, and add ".png" extension
                diagram_filename = diagram_name.lower().replace(" ", "_") + ".png"

                # Check if the line contains "filename="
                if "filename=" in line:
                    # Extract the filename from the "filename=" parameter
                    diagram_filename = (
                        line.split("filename=")[1].split(")")[0].strip("'").strip('"')
                        + ".png"
                    )

                inside_diagram_block = True

            # Check if the line contains the end of the "with Diagram:" block
            if inside_diagram_block and line.strip() == "":
                inside_diagram_block = False

            # TODO: not sure if it handles all edge cases...
            # Only include lines that are inside the "with Diagram:" block or not related to the diagram
            if inside_diagram_block or not line.strip().startswith("diag."):
                updated_lines.append(line)

        # Join the updated lines to create the updated code
        updated_code = "\n".join(updated_lines)

        return updated_code, diagram_filename

    def call_endpoint(self, payload):
        headers = {"Authorization": f"Bearer {HUGGING_FACE_KEY}"}
        API_URL = "https://api-inference.huggingface.co/models/bigcode/starcoder"
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()

    def __call__(self, query):
        query_header = "Write a function in Python using the Diagrams library to draw"

        output = self.call_endpoint(
            {
                "inputs": query_header + query,
                "parameters": {
                    "do_sample": False,
                    "max_new_tokens": 500,
                    "return_full_text": False,
                    "temperature": 0.01,
                },
            }
        )
        code = output[0]["generated_text"]

        # Clean up hallucinated code
        code, file_name = self.process_code(code)
        code = code.replace("```python", "").replace("```", "").replace('"""', "")

        try:
            # Code to run
            self.save_and_run_python_code(code)
        except Exception as e:
            print(e)
            return

        return Image.open(file_name)


def start_agent(model_endpoint="https://nnu78adxthljszhh.us-east-1.aws.endpoints.huggingface.cloud",):
    # Start tools
    well_arch_tool = AWSWellArchTool()
    code_gen_tool = CodeGenerationTool()
    diagram_gen_tool = DiagramCreationTool()
    aws_catalog= AWSCatalogTool()
    print('Model powering transformer agent: ',model_endpoint)

    # Start Agent
    agent = HfAgent(
        model_endpoint,
        token=HUGGING_FACE_KEY,
        #run_prompt_template=sa_prompt,
        #additional_tools=[code_gen_tool, well_arch_tool, diagram_gen_tool],
        additional_tools=[aws_catalog],
    )

    default_tools = [
        "document_qa",
        "image_captioner",
        "image_qa",
        "image_segmenter",
        "transcriber",
        "summarizer",
        "text_classifier",
        "text_qa",
        "text_reader",
        "translator",
        "image_transformer",
        "text_downloader",
        "image_generator",
        "video_generator",
    ]

    # Remove default tools
    for tool in default_tools:
        try:
            del agent.toolbox[tool]
        except:
            continue

    return agent
