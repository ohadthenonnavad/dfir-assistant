"""Response quality metrics for evaluating generated responses.

Evaluates response format, content accuracy, and command validity.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from dfir_assistant.evaluation.golden_dataset import GoldenQuery
from dfir_assistant.validation.command_validator import CommandValidator, get_command_validator

logger = logging.getLogger(__name__)


@dataclass
class ResponseResult:
    """Result of a single response evaluation."""
    
    query_id: str
    query_type: str
    response_text: str
    
    # Content accuracy
    expected_terms_found: list[str]
    expected_terms_missing: list[str]
    content_coverage: float
    
    # Format compliance
    has_required_table: bool
    has_code_blocks: bool
    
    # Command validation
    commands_found: int
    commands_valid: int
    command_validity_rate: float
    
    # Overall
    quality_score: float
    issues: list[str] = field(default_factory=list)


@dataclass  
class ResponseReport:
    """Aggregated response evaluation report."""
    
    total_responses: int
    avg_content_coverage: float
    avg_command_validity: float
    avg_quality_score: float
    responses_passing: int
    pass_threshold: float
    passed: bool
    results: list[ResponseResult]
    by_type: dict[str, dict[str, float]] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "total_responses": self.total_responses,
            "avg_content_coverage": round(self.avg_content_coverage, 3),
            "avg_command_validity": round(self.avg_command_validity, 3),
            "avg_quality_score": round(self.avg_quality_score, 3),
            "responses_passing": self.responses_passing,
            "pass_rate": round(self.responses_passing / self.total_responses * 100, 1) if self.total_responses > 0 else 0,
            "pass_threshold": self.pass_threshold,
            "passed": self.passed,
            "by_type": self.by_type,
        }


class ResponseEvaluator:
    """Evaluates response quality against golden dataset.
    
    Checks:
    - Content contains expected terms
    - Format meets type requirements (tables, commands)
    - Commands are valid Volatility plugins
    """
    
    def __init__(
        self,
        pass_threshold: float = 0.8,
        command_validator: CommandValidator | None = None,
    ):
        """Initialize evaluator.
        
        Args:
            pass_threshold: Minimum quality score to pass
            command_validator: CommandValidator instance
        """
        self.pass_threshold = pass_threshold
        self.command_validator = command_validator or get_command_validator()
    
    def evaluate_single(
        self,
        query: GoldenQuery,
        response: str,
    ) -> ResponseResult:
        """Evaluate a single response.
        
        Args:
            query: Golden query with expected content
            response: Generated response text
            
        Returns:
            ResponseResult with metrics
        """
        issues = []
        
        # Check content coverage
        found_terms = []
        missing_terms = []
        
        response_lower = response.lower()
        for term in query.expected_response_contains:
            if term.lower() in response_lower:
                found_terms.append(term)
            else:
                missing_terms.append(term)
        
        content_coverage = len(found_terms) / len(query.expected_response_contains) \
            if query.expected_response_contains else 1.0
        
        if content_coverage < 0.8:
            issues.append(f"Low content coverage: missing {missing_terms}")
        
        # Check format requirements
        has_table = bool(re.search(r'\|.+\|', response))
        has_code = '```' in response
        
        # Type-specific requirements
        if query.type == "anomaly":
            if query.expected_table and not has_table:
                issues.append("Anomaly response missing expected table")
        
        if query.type in ("procedure", "tool_command"):
            if not has_code:
                issues.append("Procedure/command response missing code blocks")
        
        # Validate commands
        validated_commands = self.command_validator.validate_response(response)
        commands_found = len(validated_commands)
        commands_valid = sum(1 for c in validated_commands if c.is_valid)
        command_validity = commands_valid / commands_found if commands_found > 0 else 1.0
        
        # Check expected commands are present
        if query.expected_commands:
            response_upper = response.upper()
            for expected_cmd in query.expected_commands:
                # Normalize command name for matching
                cmd_name = expected_cmd.replace("windows.", "").upper()
                if cmd_name not in response_upper and expected_cmd.upper() not in response_upper:
                    issues.append(f"Missing expected command: {expected_cmd}")
        
        if command_validity < 0.8:
            issues.append(f"Low command validity: {commands_valid}/{commands_found}")
        
        # Calculate quality score
        quality_score = (
            content_coverage * 0.5 +  # Content is most important
            command_validity * 0.3 +   # Command accuracy is critical
            (1.0 if not issues or len(issues) < 2 else 0.8) * 0.2  # Format compliance
        )
        
        return ResponseResult(
            query_id=query.id,
            query_type=query.type,
            response_text=response[:500],  # Truncate for storage
            expected_terms_found=found_terms,
            expected_terms_missing=missing_terms,
            content_coverage=content_coverage,
            has_required_table=has_table,
            has_code_blocks=has_code,
            commands_found=commands_found,
            commands_valid=commands_valid,
            command_validity_rate=command_validity,
            quality_score=quality_score,
            issues=issues,
        )
    
    def evaluate_batch(
        self,
        queries: list[GoldenQuery],
        responses: dict[str, str],
    ) -> ResponseReport:
        """Evaluate multiple responses.
        
        Args:
            queries: List of golden queries
            responses: Map of query_id -> response text
            
        Returns:
            ResponseReport with aggregated metrics
        """
        results = []
        
        for query in queries:
            response = responses.get(query.id, "")
            if not response:
                logger.warning(f"No response for query {query.id}")
                continue
            
            result = self.evaluate_single(query, response)
            results.append(result)
        
        # Aggregate metrics
        total = len(results)
        if total == 0:
            return ResponseReport(
                total_responses=0,
                avg_content_coverage=0,
                avg_command_validity=0,
                avg_quality_score=0,
                responses_passing=0,
                pass_threshold=self.pass_threshold,
                passed=False,
                results=[],
            )
        
        avg_content = sum(r.content_coverage for r in results) / total
        avg_cmd_validity = sum(r.command_validity_rate for r in results) / total
        avg_quality = sum(r.quality_score for r in results) / total
        passing = sum(1 for r in results if r.quality_score >= self.pass_threshold)
        
        # Group by type
        by_type = {}
        for query_type in ["concept", "anomaly", "procedure", "tool_command"]:
            type_results = [r for r in results if r.query_type == query_type]
            if type_results:
                by_type[query_type] = {
                    "count": len(type_results),
                    "avg_quality": sum(r.quality_score for r in type_results) / len(type_results),
                    "avg_coverage": sum(r.content_coverage for r in type_results) / len(type_results),
                }
        
        passed = avg_quality >= self.pass_threshold
        
        return ResponseReport(
            total_responses=total,
            avg_content_coverage=avg_content,
            avg_command_validity=avg_cmd_validity,
            avg_quality_score=avg_quality,
            responses_passing=passing,
            pass_threshold=self.pass_threshold,
            passed=passed,
            results=results,
            by_type=by_type,
        )
    
    def format_report(self, report: ResponseReport) -> str:
        """Format report as human-readable string."""
        lines = [
            "=" * 60,
            "RESPONSE QUALITY REPORT",
            "=" * 60,
            f"Total Responses: {report.total_responses}",
            f"Avg Content Coverage: {report.avg_content_coverage:.1%}",
            f"Avg Command Validity: {report.avg_command_validity:.1%}",
            f"Avg Quality Score: {report.avg_quality_score:.1%}",
            f"Responses Passing: {report.responses_passing}/{report.total_responses}",
            f"Pass Threshold: {report.pass_threshold:.0%}",
            f"Overall: {'✅ PASS' if report.passed else '❌ FAIL'}",
            "",
            "By Type:",
        ]
        
        for query_type, metrics in report.by_type.items():
            lines.append(f"  {query_type}: avg_quality={metrics['avg_quality']:.1%} (n={metrics['count']})")
        
        return "\n".join(lines)
