from fastapi import APIRouter, Query
from ..services.aws_error_service import AWSErrorService

router = APIRouter(prefix="/aws", tags=["AWS Errors"])

@router.get("/search")
async def search_errors(
    query: str,
    service: str = Query(None, enum=["IAM", "EC2", "S3", "Lambda", "RDS", "Aurora", "EKS", "DynamoDB"]),
    limit: int = 8
):
    return AWSErrorService().search_errors(query, service, limit)