from typing import Optional

# Complete list of AWS services for verification
ALL_AWS_SERVICES = {
    "IAM": "Identity and Access Management",
    "EC2": "Amazon EC2",
    "S3": "Amazon S3",
    "Lambda": "AWS Lambda",
    "RDS": "Relational Database Service",
    "Aurora": "Aurora Database",
    "EKS": "Elastic Kubernetes Service",
    "DynamoDB": "Amazon DynamoDB",
    "Redshift": "Amazon Redshift",
    "SNS": "Simple Notification Service",
    "SQS": "Simple Queue Service",
    "EventBridge": "Amazon EventBridge",
    "BedRock": "Amazon Bedrock",
    "Amplify": "AWS Amplify",
    "AppSync": "AWS AppSync",
    "Athena": "Amazon Athena",
    "AppFlow": "Amazon AppFlow",
    "CloudSearch": "Amazon CloudSearch",
    "DataZone": "Amazon DataZone",
    "EMR": "Amazon EMR",
    "Glue": "AWS Glue",
    "Kinesis": "Amazon Kinesis",
    "Lake Formation": "AWS Lake Formation",
    "MSK": "Amazon MSK",
    "OpenSearch": "Amazon OpenSearch",
    "Managed Service for Apache Flink": "Amazon Managed Service for Apache Flink",
    "QuickSight": "Amazon QuickSight",
    "MWAA": "Amazon MWAA",
    "Step Functions": "Amazon Step Functions",
    "Q": "Amazon Q",
    "Connect": "Amazon Connect",
    "Pinpoint": "Amazon Pinpoint",
    "SES": "Amazon SES",
    "WorkDocs": "Amazon WorkDocs",
    "WorkMail": "Amazon WorkMail",
    "AppRunner": "Amazon AppRunner",
    "Elastic Beanstalk": "AWS Elastic Beanstalk",
    "Lightsail": "Amazon Lightsail",
    "Batch": "AWS Batch",
    "Outposts": "AWS Outposts",
    "SAM": "AWS SAM",
    "App2Container": "AWS App2Container",
    "ECR": "Amazon ECR",
    "ECS": "Amazon ECS",
    "ROSA": "AWS ROSA",
    "KMS": "Amazon KMS",
    "Athena": "AWS Athena",
    "DocumentDB": "Amazon DocumentDB",
    "ElastiCache": "Amazon ElastiCache",
    "Keyspaces": "Amazon Keyspaces",
    "MemoryDB": "Amazon MemoryDB",
    "Neptune": "Amazon Neptune",
    "TimeStream": "Amazon TimeStream",
    "QLDB": "Amazon QLDB",
    "Oracle Database": "AWS Oracle Database",
    "CodeBuild": "AWS CodeBuild",
    "CodeDeploy": "AWS CodeDeploy",
    "CodePipeline": "AWS CodePipeline",
    "XRay": "AWS XRay",
    "CodeArtifact": "AWS CodeArtifact",
    "WorkSpaces": "Amazon WorkSpaces",
    "Support": "AWS Support",
    "Tagging": "AWS Tagging",
    "CodeGuru": "Amazon CodeGuru",
    "Comprehend": "Amazon Comprehend",
    "Lex": "Amazon Lex",
    "Kendra": "Amazon Kendra",
    "Personalize": "Amazon Personalize",
    "Polly": "Amazon Polly",
    "Rekognition": "Amazon Rekognition",
    "Textract": "Amazon Textract",
    "Transcribe": "Amazon Transcribe",
    "Translate": "Amazon Translate",
    "CloudFormation": "Amazon CloudFormation",
    "CloudTrail": "Amazon CloudTrail",
    "Config": "Amazon Config",
    "Control Tower": "Amazon Control Tower",
    "Health": "Amazon Health",
    "Grafana": "Amazon Grafana",
    "Prometheus": "Amazon Prometheus",
    "Resilience Hub": "Amazon Resilience Hub",
    "Service Catalog": "Amazon Service Catalog",
    "Database Migration Service": "Amazon Database Migration Service",
    "DataSync": "Amazon DataSync",
    "Transfer Family": "AWS Transfer Family",
    "API Gateway": "Amazon API Gateway",
    "CloudFront": "Amazon CloudFront",
    "DirectConnect": "Amazon DirectConnect",
    "Elastic Load Balancing": "Amazon Elastic Load Balancing",
    "Route53": "Amazon Route53",
    "Global Accelerator": "Amazon Global Accelerator",
    "VPC": "Amazon VPC",
    "VPN": "Amazon VPN",
    "Audit Manager": "Amazon Audit Manager",
    "Directory Service": "Amazon Directory Service",
    "GuardDuty": "Amazon GuardDuty",
    "Sagemaker": "Amazon Sagemaker",
}

APPROVED_SERVICES = {k: v for k, v in ALL_AWS_SERVICES.items() if k in [
    "IAM", "EC2", "S3", "Lambda", "RDS", "Aurora", 
    "EKS", "DynamoDB", "Redshift", "SNS", "SQS",
    "EventBridge", "BedRock", "Tagging", 
    "Glue", "Athena", "Sagemaker", "WAF", "Elastic Load Balancing",
    "ElastiCache", "Keyspaces", "MQ", "OpenSearch", "ECS", "ECR",
    "KMS"
]}

def is_service_approved(service_name: str) -> bool:
    """Check if service is in approved list (case-insensitive)"""
    return service_name.upper() in [s.upper() for s in APPROVED_SERVICES.keys()]

def get_unapproved_service(message: str) -> Optional[str]:
    """Identify any unapproved AWS service mentioned in message"""
    message_upper = message.upper()
    for service in ALL_AWS_SERVICES:
        if service.upper() in message_upper and not is_service_approved(service):
            # Find the exact casing from our dictionary
            return next((k for k in ALL_AWS_SERVICES if k.upper() == service.upper()), None)
    return None

def get_approved_services_list() -> list:
    """Return formatted list of approved services
    
    Args:
        format: 'list' returns list of strings, 
                'str' returns single formatted string
    """
    services = [f"{k} ({v})" for k, v in APPROVED_SERVICES.items()]
    return "\n".join(services) if format == "str" else services