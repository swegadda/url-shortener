# URL Shortener - Serverless AWS Application

A fully serverless URL shortener built on AWS, based on the architecture from the [AWS DevOps Agent blog post](https://aws.amazon.com/blogs/devops/leverage-agentic-ai-for-autonomous-incident-response-with-aws-devops-agent/).

## Architecture

- **Amazon CloudFront** → serves static assets from S3
- **Amazon API Gateway** → routes API requests to Lambda functions
- **AWS Lambda** → handles create, redirect, and analytics
- **Amazon DynamoDB** → stores URL mappings and click analytics

## Project Structure

```
url-shortener/
├── cdk/                  # AWS CDK infrastructure
│   ├── app.py
│   ├── cdk.json
│   ├── requirements.txt
│   └── stacks/
│       └── url_shortener_stack.py
├── lambda/               # Lambda function code
│   ├── create/
│   │   └── index.py
│   ├── redirect/
│   │   └── index.py
│   └── analytics/
│       └── index.py
└── frontend/             # Static frontend
    └── index.html
```

## Deployment

```bash
cd cdk
pip install -r requirements.txt
cdk bootstrap
cdk deploy
```
