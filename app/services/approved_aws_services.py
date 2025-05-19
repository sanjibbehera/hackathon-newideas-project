APPROVED_SERVICES = {
    "IAM": "Identity and Access Management",
    "EC2": "Elastic Compute Cloud",
    "S3": "Simple Storage Service",
    "Lambda": "AWS Lambda",
    "RDS": "Relational Database Service",
    "Aurora": "Aurora Database",
    "EKS": "Elastic Kubernetes Service",
    "DynamoDB": "DynamoDB"
}

def is_service_approved(service_name: str) -> bool:
    """Check if service is in approved list (case-insensitive)"""
    return service_name.upper() in [s.upper() for s in APPROVED_SERVICES.keys()]

def get_approved_services_list() -> list:
    """Return formatted list of approved services for messages"""
    return [f"{k} ({v})" for k, v in APPROVED_SERVICES.items()]