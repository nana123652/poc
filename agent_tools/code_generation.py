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