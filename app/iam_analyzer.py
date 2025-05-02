import re
from typing import Dict, List
from models.models import IAMPolicyAnalysis

def analyze_iam_policy(file_path: str) -> Dict:
    """
    Analyze an IAM policy document for common issues
    """
    # In a real implementation, you would parse the actual policy
    # This is a simplified version for demonstration
    
    # Read file content (simplified - would need proper parsing for different formats)
    with open(file_path, 'r') as file:
        content = file.read()
    
    issues = []
    recommendations = []
    severity = "low"
    
    # Check for overly permissive actions
    if re.search(r'"Action":\s*"\*"', content):
        issues.append("Policy contains overly permissive action ('*')")
        recommendations.append("Replace wildcard action with specific actions needed")
        severity = "high"
    
    # Check for overly permissive resources
    if re.search(r'"Resource":\s*"\*"', content):
        issues.append("Policy contains overly permissive resource ('*')")
        recommendations.append("Restrict resources to specific ARNs needed")
        severity = "high"
    
    # Check for missing conditions
    if '"Condition":' not in content:
        issues.append("Policy lacks conditions for added security")
        recommendations.append("Consider adding conditions like IP restrictions or MFA requirements")
        severity = "medium"
    
    return {
        "issues": issues,
        "recommendations": recommendations,
        "severity": severity
    }