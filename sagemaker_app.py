import boto3
import pandas as pd
from transformers import Tool


class SageMakerRunningInstancesTool(Tool):
      # Attributes
    name = "sagemaker_running_instances"
    description = "A tool to retrieve information about running SageMaker instances"
    inputs = "None (no parameters required)"
    output_type = "Pandas DataFrame containing details of running SageMaker instances"

    def __init__(self):
        self.client = boto3.client('sagemaker',region_name='us-east-1')
        self.account_id = boto3.client("sts",region_name='us-east-1').get_caller_identity()["Account"]
        self.running_instances = []

    def get_running_instances(self):
        response_apps = self.client.list_apps(MaxResults=10, SortOrder='Ascending', SortBy='CreationTime')
        while True:
            for app in response_apps["Apps"]:
                if app["AppType"] != "JupyterServer" and app["Status"] != "Deleted":
                    if 'SpaceName' in app.keys():
                        response = self.client.describe_app(
                            DomainId=app["DomainId"],
                            SpaceName=app["SpaceName"],
                            AppType=app["AppType"],
                            AppName=app["AppName"]
                        )
                    elif 'UserProfileName' in app.keys():
                        response = self.client.describe_app(
                            DomainId=app["DomainId"],
                            UserProfileName=app["UserProfileName"],
                            AppType=app["AppType"],
                            AppName=app["AppName"]
                        )
                    self.running_instances.append({
                        "AppArn": response["AppArn"],
                        "DomainId": response["DomainId"],
                        "UserProfileSpaceName": response["SpaceName"] if 'SpaceName' in app.keys() else response["UserProfileName"],
                        "Status": response["Status"],
                        "InstanceType": response["ResourceSpec"]["InstanceType"],
                        "CreationTime": str(response["CreationTime"]),
                        "SageMakerImageArn": response["ResourceSpec"]["SageMakerImageArn"],
                    })
            if "NextToken" in response_apps:
                response_apps = self.client.list_apps(
                    NextToken=response_apps["NextToken"],
                    MaxResults=10,
                    SortOrder='Ascending',
                    SortBy='CreationTime'
                )
            else:
                break

    def get_dataframe(self):
        self.get_running_instances()
        return pd.DataFrame(self.running_instances)

    def __call__(self):
        return self.get_dataframe()
  


