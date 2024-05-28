
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
from agent_tools.q_answer import QATool


os.environ["TOKENIZERS_PARALLELISM"] = "false"
HUGGING_FACE_KEY = ''



sa_prompt = """
You are an expert Agent. Your role is to help customers with tasks. You will generate Python commands using available tools to help will customers solve their problem effectively.
To assist you, you have access to five tools. Each tool has a description that explains its functionality, the inputs it takes, and the outputs it provides.
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

Task: "Provision S3 Service Catalog Product"

I will use the AWS Catalog Tool Tool because it provisions AWS resources using service catalog.

Answer:
```py

response = aws_catalog_tool(product_name="S3")
print(f"{response}")
```

Task: "Can you give me the name of the model that has the most downloads in the 'text-to-video' task on the Hugging Face Hub?"

I will use the Model Download Counter Tool because returns the most downloaded model of a given task on the Hugging Face Hub.

Answer:

```py
most_downloaded_model = model_download_counter(task="text-to-video")
print(f"The most downloaded model for the 'text-to-video' task is {most_downloaded_model}.")
```

Task: "Generate running sagemaker instances"

I will use the Sagemaker Running Instances to retrieve information about running SageMaker instances

Answer:
```py
response = sagemaker_running_instances()
print(f"{response}")
```


Task: "Who is Steve Jobs?"

I will use the Question Answering Tool because it has the capability to answer any questions

Answer:
```py
response = question_answering_tool(query="Who is Steve Jobs?")
print(f"{response}")
```

Task: "<<prompt>>"

I will use the following
"""

def start_agent(model_endpoint="https://nnu78adxthljszhh.us-east-1.aws.endpoints.huggingface.cloud",):
   
    # Start tools
    well_arch_tool = AWSWellArchTool()
    aws_catalog= AWSCatalogTool()
    model_download = HFModelDownloadsTool()
    sagemaker_app = SageMakerRunningInstancesTool()
    q_answer = QATool()
    #code_gen_tool = CodeGenerationTool()
    #diagram_gen_tool = DiagramCreationTool()
    print('LLM Model powering transformer agent Engine: ',model_endpoint)

    # Start Agent Engine
    agent = HfAgent(
        model_endpoint, #model inference endpoint
        token=HUGGING_FACE_KEY, #hugging face key
        run_prompt_template=sa_prompt, #custom agent prompt
        additional_tools=[well_arch_tool,aws_catalog,model_download,sagemaker_app,q_answer], #custom tools created
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
