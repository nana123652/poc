import boto3
import time
from transformers import Tool


class AWSCatalogTool(Tool):
    name = "aws_catalog_tool"
    description = "Use this tool to provision AWS resources in service catalog"
    inputs = ["text"]
    outputs = ["text"]


    def __init__(self):
        self.client = boto3.client('servicecatalog', region_name='us-east-1')
        self.product_id = None
        self.target_status = 'AVAILABLE'

    def get_provisioned_product_status(self, product_id):
        try:
            response = self.client.describe_provisioned_status(Id=product_id)
            return response['ProvisionedProductDetail']['Status']
        except Exception as e:
            print(f'An error occurred while getting status: {str(e)}')
            return None

    def wait_for_status(self, product_id, target_status, max_attempts=20, interval_seconds=15):
        print(f'Target response to check: {product_id}')
        attempts = 0
        while attempts < max_attempts:
            status = self.describe_provisioned_product(Id=product_id)
            print(f"Current status: {status}. Waiting for {target_status}...")
            if status == target_status:
                print(f'Provisioned Product reached target status: {status}')
                return f'Provisioned Product reached target status: {status}'
            elif status == 'ERROR':
                print(f'Provisioned Product failed with status: {status}')
                return f'Provisioned Product failed with status: {status}'
            else:
                time.sleep(interval_seconds)
                attempts += 1
        print(f"Max attempts reached. Provisioned Product status: {status}")
        return f"Max attempts reached. Provisioned Product status: {status}"

    def __call__(self, product_name: str):
        try:
            product = self.client.search_products(Filters={'FullTextSearch': [product_name]})['ProductViewSummaries'][0]
            response = self.client.provision_product(ProductId=product['ProductId'], ProvisionedProductName='re34rerersrq43444ss5', ProvisioningArtifactId='pa-mhftvd4y7zkdg')
            self.product_id = response['RecordDetail']['ProvisionedProductId']
            status_response = self.wait_for_status(self.product_id, self.target_status)
            return status_response,response
        except Exception as e:
            print(f'An error occurred: {str(e)}')
            return f'An error occurred: {str(e)}'