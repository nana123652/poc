import boto3
import csv

account_id =  boto3.client("sts").get_caller_identity()["Account"]
client = boto3.client('sagemaker')


response_apps = client.list_apps(
    #NextToken='string',
    MaxResults=10,
    SortOrder='Ascending',
    SortBy='CreationTime',
)

running_instances = []
while True:
    for app in response_apps["Apps"]:
        if app["AppType"] != "JupyterServer" and app["Status"] != "Deleted":
            if 'SpaceName' in app.keys():
                response = client.describe_app(
                    DomainId=app["DomainId"],
                    SpaceName=app["SpaceName"],
                    AppType=app["AppType"],
                    AppName=app["AppName"]
                )
                #print(response)
                running_instances.append(
                    {
                        "AppArn": response["AppArn"],
                        "DomainId": response["DomainId"],
                        "UserProfileSpaceName": response["SpaceName"],
                        "Status": response["Status"],
                        "InstanceType": response["ResourceSpec"]["InstanceType"],
                        "CreationTime": str(response["CreationTime"]),
                        "SageMakerImageArn": response["ResourceSpec"]["SageMakerImageArn"],

                    }
                )
            elif 'UserProfileName' in app.keys():
                response = client.describe_app(
                    DomainId=app["DomainId"],
                    UserProfileName=app["UserProfileName"],
                    AppType=app["AppType"],
                    AppName=app["AppName"]
                )
                #print(response)
                running_instances.append(
                    {
                        "AppArn": response["AppArn"],
                        "DomainId": response["DomainId"],
                        "UserProfileSpaceName": response["UserProfileName"],
                        "Status": response["Status"],
                        "InstanceType": response["ResourceSpec"]["InstanceType"],
                        "CreationTime": str(response["CreationTime"]),
                        "SageMakerImageArn": response["ResourceSpec"]["SageMakerImageArn"],

                    }
                )
    if "NextToken" in response_apps:
        response_apps = client.list_apps(
            NextToken=response_apps["NextToken"],
            MaxResults=10,
            SortOrder='Ascending',
            SortBy='CreationTime'
        )
    else:
        break

print(running_instances)
keys = running_instances[0].keys()
        
with open(f'sagemaker_running_instances_{account_id}.csv', 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(running_instances)
