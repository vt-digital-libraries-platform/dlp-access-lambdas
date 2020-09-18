# dlp-access-lambdas

This project contains Lambda functions that update [dlp-access](https://github.com/VTUL/dlp-access) DynamoDB tables to have the necessary data for the collection folder tree. 

- collectionTitleEditFunction: This will modify the titles for IAWA sub-collections to NOT include identifiers to collection table.
- createCollectionMapFunction: This will create JSON files in the CollectionMap-yourenv S3 Bucket and update collection and collectionmap tables.
- createCollectionHeirarchyFunction: This will update collection heirarchy information to collection table.
- createUpdateFunction: This will update archive, collection, and collectionmap table's createdAt, etc fields.
- archiveCollectionHeirarchyFunction: This will update archive/collection heirarchy information to archive table.

## Deploy the dlp-access-lambdas application using CloudFormation stack

#### Step 1: Launch CloudFormation stack
[![Launch Stack](https://cdn.rawgit.com/buildkite/cloudformation-launch-stack-button-svg/master/launch-stack.svg)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?&templateURL=https://vtdlp-dev-cf.s3.amazonaws.com/69ad1fde579ab387572e0bb1d9e84b84.template)

Click *Next* to continue

#### Step 2: Specify stack details

| Name | Description |
|:---  |:------------|
| Stack name | any valid name |
| Region | a valid AWS region. e.g. us-east-1 |
| CollectionTable | DynamoDB Collection table name |
| ArchiveTable | DynamoDB Archive table name |
| CollectionmapTable | DynamoDB Collectionmap table name |
| S3BucketName | Target S3 bucket name |

#### Step 3: Configure stack options
Leave it as is and click **Next**

#### Step 4: Review
Make sure all checkboxes under Capabilities section are **CHECKED**

Click *Create stack*

### Deploy the dlp-access-lambdas application using CloudFormation stack and AWS Cli
```
wget https://vtdlp-dev-cf.s3.amazonaws.com/69ad1fde579ab387572e0bb1d9e84b84.template -O dlpaccesslambas.template

aws cloudformation deploy --template-file dlpaccesslambas.template --stack-name demo --parameter-overrides 'SourceTable=sourcetable TargetTable=targettable Region=us-east-1' --capabilities CAPABILITY_IAM --region us-east-1
```

## Deploy the dlp-access-lambdas application using SAM CLI

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build the application for the first time, run the following in your shell:
```bash
sam build --use-container
```
Above command will build the source of the application. The SAM CLI installs dependencies defined in `requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

To package the application, run the following in your shell:
```bash
sam package --output-template-file packaged.yaml --s3-bucket BUCKETNAME
```
Above command will package the application and upload it to the S3 bucket you specified.

Run the following in your shell to deploy the application to AWS:
```bash
sam deploy --template-file packaged.yaml --stack-name STACKNAME --s3-bucket BUCKETNAME --parameter-overrides 'CollectionTable=CollectionTable ArchiveTable=ArchiveTable CollectionmapTable=CollectionmapTable S3BucketName=S3BucketName Region=us-east-1' --capabilities CAPABILITY_IAM --region us-east-1
```

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
* **AWS Region**: The AWS region you want to deploy your app to.

## Run the dlp-access-lambdas lamdba function through bash
```bash
aws lambda invoke --function-name LambdaFunctioName out --log-type Tail --query 'LogResult' --output text |  base64 -d
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name StackName
```

