
import json
import os
import subprocess
from typing import Dict
import requests

from PIL import Image

from transformers import Tool
from transformers.tools import HfAgent


#Agent Tools
from agent_tools.model_downloads import HFModelDownloadsTool
from agent_tools.aws_catalog import AWSCatalogTool
from agent_tools.sagemaker_app import SageMakerRunningInstancesTool
from agent_tools.well_architected_tool import AWSWellArchTool



os.environ["TOKENIZERS_PARALLELISM"] = "false"
HUGGING_FACE_KEY = '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'



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
    aws_catalog= AWSCatalogTool()
    model_download = HFModelDownloadsTool()
    sagemaker_app = SageMakerRunningInstancesTool()

    #code_gen_tool = CodeGenerationTool()
    #diagram_gen_tool = DiagramCreationTool()
    print('Model powering transformer agent: ',model_endpoint)

    # Start Agent
    agent = HfAgent(
        model_endpoint,
        token=HUGGING_FACE_KEY,
        run_prompt_template=sa_prompt,
        #additional_tools=[code_gen_tool, well_arch_tool, diagram_gen_tool],
        additional_tools=[well_arch_tool,aws_catalog,model_download,sagemaker_app],
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
            #continue
        except:
            continue

    return agent
