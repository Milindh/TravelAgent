"""
Travel Validation Agent
Validates travel plans for logical consistency and practical feasibility
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class ValidationIssue:
    """Represents a validation issue found in a plan"""
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "timing", "budget", "logistics", "availability"
    day_number: Optional[int]
    problem: str
    suggestion: str
    affected_activities: List[str]

@dataclass
class ValidationResult:
    """Result of validating a single plan"""
    plan_id: str
    status: str  # "APPROVED", "APPROVED_WITH_WARNINGS", "NEEDS_REVISION"
    issues: List[ValidationIssue]
    warnings: List[str]
    score: float  # 0-100, overall plan quality score


class ValidationAgent:
    """Validates travel plans against a set of rules"""
    
    # Validation thresholds
    MAX_DAILY_ACTIVITIES = 8
    MIN_DAILY_ACTIVITIES = 3
    MAX_DAILY_COST_VARIANCE = 0.4  # 40% variance from average is acceptable
    MAX_WALKING_DISTANCE_PER_DAY = 15  # km
    MIN_TIME_BETWEEN_ACTIVITIES = 0.5  # hours (30 minutes)
    MAX_ACTIVITY_DURATION = 6  # hours for a single activity
    BUDGET_TOLERANCE = 0.10  # 10% over budget is acceptable
    
    def __init__(self):
        """Initialize Validation Agent"""
        pass
    
    def validate_plans(
        self, 
        plans: List,  # List[TravelPlan]
        user_requirements: Dict
    ) -> List[ValidationResult]:
        """
        Validate all plans
        
        Args:
            plans: List of TravelPlan objects from Planner Agent
            user_requirements: Original user requirements including budget
        
        Returns:
            List of ValidationResult objects
        """
        print(f"\n✅ Validating {len(plans)} travel plans...")
        
        validation_results = []
        
        for plan in plans:
            print(f"\n  Validating Plan {plan.plan_id}: {plan.plan_name}...")
            result = self._validate_single_plan(plan, user_requirements)
            validation_results.append(result)
            
            # Display result
            status_icon = {
                "APPROVED": "✓",
                "APPROVED_WITH_WARNINGS": "⚠",
                "NEEDS_REVISION": "✗"
            }
            print(f"    {status_icon[result.status]} Status: {result.status}")
            print(f"    Quality Score: {result.score:.1f}/100")
            if result.issues:
                print(f"    Issues Found: {len(result.issues)}")
        
        print(f"\n✅ Validation complete!")
        return validation_results
    
    def _validate_single_plan(
        self, 
        plan, 
        user_requirements: Dict
    ) -> ValidationResult:
        """Validate a single travel plan"""
        
        issues = []
        warnings = []
        
        # Run all validation checks
        issues.extend(self._validate_budget(plan, user_requirements))
        issues.extend(self._validate_timing(plan))
        issues.extend(self._validate_daily_balance(plan))
        issues.extend(self._validate_activity_feasibility(plan))
        issues.extend(self._validate_cost_distribution(plan))
        warnings.extend(self._check_warnings(plan))
        
        # Calculate quality score
        score = self._calculate_quality_score(plan, issues)
        
        # Determine status
        critical_issues = [i for i in issues if i.severity == "critical"]
        high_issues = [i for i in issues if i.severity == "high"]
        
        if critical_issues:
            status = "NEEDS_REVISION"
        elif high_issues:
            status = "APPROVED_WITH_WARNINGS"
        else:
            status = "APPROVED"
        
        return ValidationResult(
            plan_id=plan.plan_id,
            status=status,
            issues=issues,
            warnings=warnings,
            score=score
        )
    
    def _validate_budget(self, plan, user_requirements: Dict) -> List[ValidationIssue]:
        """Validate plan stays within budget"""
        issues = []
        
        user_budget = user_requirements.get('budget', 0)
        plan_cost = plan.total_cost
        
        # Check if over budget
        if plan_cost > user_budget * (1 + self.BUDGET_TOLERANCE):
            over_amount = plan_cost - user_budget
            over_percentage = (over_amount / user_budget) * 100
            
            issues.append(ValidationIssue(
                severity="critical",
                category="budget",
                day_number=None,
                problem=f"Total cost ${plan_cost:.2f} exceeds budget ${user_budget:.2f} by ${over_amount:.2f} ({over_percentage:.1f}%)",
                suggestion=f"Reduce accommodation tier, eliminate expensive activities, or increase budget by ${over_amount:.2f}",
                affected_activities=[]
            ))
        
        # Check if significantly under budget (might indicate low quality)
        elif plan_cost < user_budget * 0.6:
            issues.append(ValidationIssue(
                severity="low",
                category="budget",
                day_number=None,
                problem=f"Plan only uses {(plan_cost/user_budget)*100:.1f}% of available budget",
                suggestion="Consider upgrading accommodation or adding premium experiences",
                affected_activities=[]
            ))
        
        return issues
    
    def _validate_timing(self, plan) -> List[ValidationIssue]:
        """Validate timing and scheduling of activities"""
        issues = []
        
        for day in plan.daily_plans:
            activities = day.activities
            
            # Check if too many activities
            if len(activities) > self.MAX_DAILY_ACTIVITIES:
                issues.append(ValidationIssue(
                    severity="high",
                    category="timing",
                    day_number=day.day_number,
                    problem=f"Day {day.day_number} has {len(activities)} activities (max recommended: {self.MAX_DAILY_ACTIVITIES})",
                    suggestion="Remove or combine some activities to avoid exhaustion",
                    affected_activities=[a.name for a in activities]
                ))
            
            # Check if too few activities
            elif len(activities) < self.MIN_DAILY_ACTIVITIES:
                issues.append(ValidationIssue(
                    severity="low",
                    category="timing",
                    day_number=day.day_number,
                    problem=f"Day {day.day_number} only has {len(activities)} activities",
                    suggestion="Consider adding more experiences to make the most of your day",
                    affected_activities=[a.name for a in activities]
                ))
            
            # Check timing between consecutive activities
            for i in range(len(activities) - 1):
                current = activities[i]
                next_activity = activities[i + 1]
                
                # Parse times
                current_time = datetime.strptime(current.time, "%H:%M")
                next_time = datetime.strptime(next_activity.time, "%H:%M")
                
                # Calculate buffer time
                current_end = current_time + timedelta(hours=current.duration_hours)
                buffer_time = (next_time - current_end).total_seconds() / 3600
                
                if buffer_time < self.MIN_TIME_BETWEEN_ACTIVITIES:
                    issues.append(ValidationIssue(
                        severity="high",
                        category="timing",
                        day_number=day.day_number,
                        problem=f"Only {buffer_time*60:.0f} minutes between '{current.name}' and '{next_activity.name}'",
                        suggestion=f"Add at least 30 minutes buffer for travel/breaks",
                        affected_activities=[current.name, next_activity.name]
                    ))
                
                # Check for overlapping activities
                if buffer_time < 0:
                    issues.append(ValidationIssue(
                        severity="critical",
                        category="timing",
                        day_number=day.day_number,
                        problem=f"Activities overlap: '{current.name}' ends after '{next_activity.name}' starts",
                        suggestion="Reschedule one of these activities",
                        affected_activities=[current.name, next_activity.name]
                    ))
            
            # Check for unreasonably long activities
            for activity in activities:
                if activity.duration_hours > self.MAX_ACTIVITY_DURATION:
                    issues.append(ValidationIssue(
                        severity="medium",
                        category="timing",
                        day_number=day.day_number,
                        problem=f"Activity '{activity.name}' is scheduled for {activity.duration_hours} hours",
                        suggestion="Consider splitting into multiple shorter activities or reducing duration",
                        affected_activities=[activity.name]
                    ))
        
        return issues
    
    def _validate_daily_balance(self, plan) -> List[ValidationIssue]:
        """Validate each day is balanced and not overloaded"""
        issues = []
        
        for day in plan.daily_plans:
            # Calculate total active time
            total_hours = sum(activity.duration_hours for activity in day.activities)
            
            # Check if day is too packed
            if total_hours > 12:
                issues.append(ValidationIssue(
                    severity="high",
                    category="logistics",
                    day_number=day.day_number,
                    problem=f"Day {day.day_number} has {total_hours:.1f} hours of activities (over 12 hours)",
                    suggestion="Reduce number of activities or shorten durations to avoid exhaustion",
                    affected_activities=[a.name for a in day.activities]
                ))
            
            # Check if day is too light
            elif total_hours < 4:
                issues.append(ValidationIssue(
                    severity="low",
                    category="logistics",
                    day_number=day.day_number,
                    problem=f"Day {day.day_number} only has {total_hours:.1f} hours of activities",
                    suggestion="Add more activities to make better use of the day",
                    affected_activities=[a.name for a in day.activities]
                ))
            
            # Check activity category distribution
            categories = [a.category for a in day.activities]
            if categories.count('dining') > 4:
                issues.append(ValidationIssue(
                    severity="low",
                    category="logistics",
                    day_number=day.day_number,
                    problem=f"Day {day.day_number} has too many dining activities",
                    suggestion="Balance with more sightseeing or cultural activities",
                    affected_activities=[a.name for a in day.activities if a.category == 'dining']
                ))
        
        return issues
    
    def _validate_activity_feasibility(self, plan) -> List[ValidationIssue]:
        """Validate activities are feasible and realistic"""
        issues = []
        
        for day in plan.daily_plans:
            # Check for activities with zero or negative cost (suspicious)
            for activity in day.activities:
                if activity.estimated_cost < 0:
                    issues.append(ValidationIssue(
                        severity="critical",
                        category="budget",
                        day_number=day.day_number,
                        problem=f"Activity '{activity.name}' has negative cost ${activity.estimated_cost}",
                        suggestion="Correct the cost estimate",
                        affected_activities=[activity.name]
                    ))
                
                # Check for unrealistic free activities in paid venues
                if activity.estimated_cost == 0 and 'museum' in activity.name.lower():
                    issues.append(ValidationIssue(
                        severity="medium",
                        category="budget",
                        day_number=day.day_number,
                        problem=f"Activity '{activity.name}' listed as free but may require admission",
                        suggestion="Verify if entrance fee is required",
                        affected_activities=[activity.name]
                    ))
        
        return issues
    
    def _validate_cost_distribution(self, plan) -> List[ValidationIssue]:
        """Validate costs are distributed reasonably across days"""
        issues = []
        
        if not plan.daily_plans:
            return issues
        
        daily_costs = [day.total_cost for day in plan.daily_plans]
        avg_cost = sum(daily_costs) / len(daily_costs)
        
        for day in plan.daily_plans:
            # Check for days that are significantly more expensive
            if day.total_cost > avg_cost * (1 + self.MAX_DAILY_COST_VARIANCE):
                over_amount = day.total_cost - avg_cost
                issues.append(ValidationIssue(
                    severity="low",
                    category="budget",
                    day_number=day.day_number,
                    problem=f"Day {day.day_number} cost ${day.total_cost:.2f} is ${over_amount:.2f} above average",
                    suggestion="Consider redistributing expensive activities across multiple days",
                    affected_activities=[]
                ))
        
        return issues
    
    def _check_warnings(self, plan) -> List[str]:
        """Generate helpful warnings (not errors)"""
        warnings = []
        
        # Check if accommodation is specified
        if not plan.accommodation or not plan.accommodation.get('name'):
            warnings.append("No specific accommodation recommended - user should research options")
        
        # Check if transportation details are provided
        if not plan.transportation or not plan.transportation.get('daily'):
            warnings.append("Transportation details are minimal - add more specific guidance")
        
        # Check for source attribution
        total_activities = sum(len(day.activities) for day in plan.daily_plans)
        activities_with_sources = sum(
            1 for day in plan.daily_plans 
            for activity in day.activities 
            if activity.source
        )
        
        if activities_with_sources < total_activities * 0.5:
            warnings.append(f"Only {activities_with_sources}/{total_activities} activities have source attribution")
        
        return warnings
    
    def _calculate_quality_score(self, plan, issues: List[ValidationIssue]) -> float:
        """Calculate overall quality score (0-100)"""
        
        base_score = 100.0
        
        # Deduct points based on issue severity
        severity_penalties = {
            "critical": 20,
            "high": 10,
            "medium": 5,
            "low": 2
        }
        
        for issue in issues:
            base_score -= severity_penalties.get(issue.severity, 0)
        
        # Ensure score doesn't go below 0
        return max(0, base_score)
    
    def save_validation_results(
        self, 
        validation_results: List[ValidationResult],
        destination: str
    ):
        """Save validation results to JSON"""
        
        results_dict = {
            'validated_at': datetime.now().isoformat(),
            'destination': destination,
            'results': [
                {
                    'plan_id': result.plan_id,
                    'status': result.status,
                    'score': result.score,
                    'issues': [
                        {
                            'severity': issue.severity,
                            'category': issue.category,
                            'day_number': issue.day_number,
                            'problem': issue.problem,
                            'suggestion': issue.suggestion,
                            'affected_activities': issue.affected_activities
                        }
                        for issue in result.issues
                    ],
                    'warnings': result.warnings
                }
                for result in validation_results
            ]
        }
        
        filename = f"data/validation_{destination.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Validation results saved to: {filename}")


# Example usage
if __name__ == "__main__":
    # This would normally receive plans from PlannerAgent
    # For demonstration, load from saved plans file
    
    validator = ValidationAgent()
    
    # Load plans (in real usage, these come directly from PlannerAgent)
    # plans = planner_agent.create_plans(...)
    
    # User requirements
    user_requirements = {
        "budget": 3000.00,
        "duration_days": 7
    }
    
    # Validate plans
    # validation_results = validator.validate_plans(plans, user_requirements)
    
    # Display results
    # for result in validation_results:
    #     print(f"\nPlan {result.plan_id}: {result.status} (Score: {result.score}/100)")
    #     if result.issues:
    #         print("Issues:")
    #         for issue in result.issues:
    #             print(f"  [{issue.severity}] {issue.problem}")
    
    print("Validation Agent ready to use!")