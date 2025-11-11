"""
Multi-Agent Travel Planning Orchestrator
Coordinates all agents and manages the complete workflow
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

# Import all agents
from research_agent import ResearchAgent
from planner_agent import PlannerAgent
from validation_agent import ValidationAgent
from refinement_agent import RefinementAgent


class TravelPlanningOrchestrator:
    """
    Orchestrates the complete travel planning workflow across all agents
    
    Workflow:
    1. User Query → Research Agent
    2. Research Data → Planner Agent (creates 3 plans)
    3. 3 Plans → Validation Agent
    4. Present validated plans to user
    5. User selects plan + provides feedback → Refinement Agent
    6. Loop refinement until user satisfied
    """
    
    def __init__(
        self,
        gemini_api_key: str,
        reddit_client_id: str,
        reddit_client_secret: str,
        reddit_user_agent: str
    ):
        """Initialize orchestrator with all agents"""
        
        print("🚀 Initializing Travel Planning System...")
        
        # Initialize all agents
        self.research_agent = ResearchAgent(
            gemini_api_key=gemini_api_key,
            reddit_client_id=reddit_client_id,
            reddit_client_secret=reddit_client_secret,
            reddit_user_agent=reddit_user_agent
        )
        
        self.planner_agent = PlannerAgent(gemini_api_key=gemini_api_key)
        
        self.validation_agent = ValidationAgent()
        
        self.refinement_agent = RefinementAgent(
            gemini_api_key=gemini_api_key,
            validation_agent=self.validation_agent
        )
        
        # Session state
        self.current_session = None
        
        print("✅ System initialized!\n")
    
    def plan_trip(
        self,
        user_requirements: Dict,
        max_youtube_videos: int = 5,
        max_reddit_posts: int = 20
    ) -> Dict:
        """
        Complete trip planning workflow
        
        Args:
            user_requirements: {
                "destination": str,
                "start_date": str (YYYY-MM-DD),
                "duration_days": int,
                "budget": float,
                "travelers": int,
                "preferences": Dict
            }
            max_youtube_videos: Number of YouTube videos to process
            max_reddit_posts: Number of Reddit posts to gather
        
        Returns:
            Complete session data with research, plans, and validation
        """
        
        print("="*70)
        print("🌍 TRAVEL PLANNING SESSION STARTED")
        print("="*70)
        
        destination = user_requirements["destination"]
        
        # Initialize session
        self.current_session = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "destination": destination,
            "user_requirements": user_requirements,
            "stage": "research",
            "started_at": datetime.now().isoformat(),
            "research_data": None,
            "plans": None,
            "validation_results": None,
            "selected_plan": None,
            "final_plan": None
        }
        
        # STAGE 1: Research
        print(f"\n{'='*70}")
        print("📚 STAGE 1: RESEARCH")
        print(f"{'='*70}")
        
        research_data = self.research_agent.research_destination(
            destination=destination,
            preferences=user_requirements.get("preferences"),
            max_youtube_videos=max_youtube_videos,
            max_reddit_posts=max_reddit_posts
        )
        
        self.current_session["research_data"] = research_data
        self.current_session["stage"] = "planning"
        
        # STAGE 2: Planning
        print(f"\n{'='*70}")
        print("🗓️  STAGE 2: PLANNING")
        print(f"{'='*70}")
        
        plans = self.planner_agent.create_plans(
            research_data=research_data,
            user_requirements=user_requirements
        )
        
        self.current_session["plans"] = plans
        self.current_session["stage"] = "validation"
        
        # STAGE 3: Validation
        print(f"\n{'='*70}")
        print("✅ STAGE 3: VALIDATION")
        print(f"{'='*70}")
        
        validation_results = self.validation_agent.validate_plans(
            plans=plans,
            user_requirements=user_requirements
        )
        
        self.current_session["validation_results"] = validation_results
        self.current_session["stage"] = "presentation"
        
        # Save session data
        self._save_session()
        
        print(f"\n{'='*70}")
        print("🎯 READY FOR USER SELECTION")
        print(f"{'='*70}")
        
        return self.current_session
    
    def present_plans_summary(self):
        """Display summary of the 3 plans for user selection"""
        
        if not self.current_session or not self.current_session["plans"]:
            print("No plans available to present")
            return
        
        plans = self.current_session["plans"]
        validation_results = self.current_session["validation_results"]
        
        print(f"\n{'='*70}")
        print(f"🎉 YOUR {self.current_session['destination'].upper()} ADVENTURE OPTIONS")
        print(f"{'='*70}\n")
        
        for i, (plan, validation) in enumerate(zip(plans, validation_results), 1):
            status_icon = {
                "APPROVED": "✓",
                "APPROVED_WITH_WARNINGS": "⚠",
                "NEEDS_REVISION": "✗"
            }[validation.status]
            
            print(f"{'─'*70}")
            print(f"OPTION {plan.plan_id}: {plan.plan_name}")
            print(f"{'─'*70}")
            print(f"Theme: {plan.theme.upper()} | Pace: {plan.pace.upper()}")
            print(f"Total Cost: ${plan.total_cost:,.2f}")
            print(f"Status: {status_icon} {validation.status} (Quality: {validation.score:.0f}/100)")
            
            if validation.issues:
                print(f"\n⚠ Issues ({len(validation.issues)}):")
                for issue in validation.issues[:2]:  # Show first 2
                    print(f"  • [{issue.severity}] {issue.problem}")
            
            print(f"\n🌟 Highlights:")
            for highlight in plan.key_highlights[:3]:
                print(f"  • {highlight}")
            
            print(f"\n💰 Cost Breakdown:")
            print(f"  • Accommodation: ${plan.cost_breakdown['accommodation']:,.2f}")
            print(f"  • Activities: ${plan.cost_breakdown['activities']:,.2f}")
            print(f"  • Transportation: ${plan.cost_breakdown['transportation']:,.2f}")
            
            print()
        
        print(f"{'='*70}\n")
    
    def select_and_refine_plan(
        self,
        selected_plan_id: str,
        user_feedback: Optional[str] = None
    ):
        """
        User selects a plan and optionally provides refinement feedback
        
        Args:
            selected_plan_id: "A", "B", or "C"
            user_feedback: Optional refinement requests
        """
        
        if not self.current_session or not self.current_session["plans"]:
            print("No plans available for selection")
            return
        
        # Find selected plan
        plans = self.current_session["plans"]
        selected_plan = next((p for p in plans if p.plan_id == selected_plan_id), None)
        
        if not selected_plan:
            print(f"Plan {selected_plan_id} not found")
            return
        
        print(f"\n{'='*70}")
        print(f"✨ You selected: {selected_plan.plan_name}")
        print(f"{'='*70}\n")
        
        self.current_session["selected_plan"] = selected_plan
        self.current_session["stage"] = "refinement"
        
        # If user provides feedback, refine the plan
        if user_feedback:
            print(f"\n{'='*70}")
            print("🔧 STAGE 4: REFINEMENT")
            print(f"{'='*70}")
            
            refined_plan, validation = self.refinement_agent.refine_plan(
                original_plan=selected_plan,
                user_feedback=user_feedback,
                user_requirements=self.current_session["user_requirements"],
                research_data=self.current_session["research_data"]
            )
            
            self.current_session["final_plan"] = refined_plan
            self.current_session["final_validation"] = validation
        else:
            # Use selected plan as-is
            self.current_session["final_plan"] = selected_plan
        
        self.current_session["stage"] = "complete"
        self._save_session()
        
        print(f"\n{'='*70}")
        print("🎊 YOUR TRIP IS READY!")
        print(f"{'='*70}\n")
    
    def continue_refinement(self, additional_feedback: str):
        """
        Continue refining the current plan
        
        Args:
            additional_feedback: More changes to apply
        """
        
        if not self.current_session or not self.current_session.get("final_plan"):
            print("No plan available for refinement")
            return
        
        print(f"\n{'='*70}")
        print("🔧 CONTINUING REFINEMENT")
        print(f"{'='*70}")
        
        current_plan = self.current_session["final_plan"]
        
        refined_plan, validation = self.refinement_agent.refine_plan(
            original_plan=current_plan,
            user_feedback=additional_feedback,
            user_requirements=self.current_session["user_requirements"],
            research_data=self.current_session["research_data"]
        )
        
        self.current_session["final_plan"] = refined_plan
        self.current_session["final_validation"] = validation
        
        self._save_session()
    
    def export_final_plan(self, format: str = "json") -> str:
        """
        Export final plan in various formats
        
        Args:
            format: "json", "markdown", or "pdf"
        
        Returns:
            Filename of exported plan
        """
        
        if not self.current_session or not self.current_session.get("final_plan"):
            print("No final plan available for export")
            return None
        
        final_plan = self.current_session["final_plan"]
        destination = self.current_session["destination"]
        session_id = self.current_session["session_id"]
        
        if format == "json":
            filename = f"data/final_plan_{destination.replace(' ', '_').lower()}_{session_id}.json"
            
            # Convert plan to dict
            plan_dict = self._export_plan_as_dict(final_plan)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(plan_dict, f, indent=2, ensure_ascii=False)
        
        elif format == "markdown":
            filename = f"data/final_plan_{destination.replace(' ', '_').lower()}_{session_id}.md"
            
            markdown_content = self._export_plan_as_markdown(final_plan)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        print(f"\n📄 Final plan exported to: {filename}")
        return filename
    
    def _export_plan_as_dict(self, plan) -> Dict:
        """Convert plan to exportable dictionary"""
        from dataclasses import asdict
        
        return {
            'plan_name': plan.plan_name,
            'destination': self.current_session['destination'],
            'total_cost': plan.total_cost,
            'theme': plan.theme,
            'pace': plan.pace,
            'accommodation': plan.accommodation,
            'transportation': plan.transportation,
            'key_highlights': plan.key_highlights,
            'daily_plans': [
                {
                    'day': day.day_number,
                    'date': day.date,
                    'theme': day.theme,
                    'cost': day.total_cost,
                    'activities': [
                        {
                            'time': act.time,
                            'name': act.name,
                            'location': act.location,
                            'description': act.description,
                            'cost': act.estimated_cost,
                            'duration': f"{act.duration_hours} hours",
                            'category': act.category,
                            'source': act.source
                        }
                        for act in day.activities
                    ]
                }
                for day in plan.daily_plans
            ]
        }
    
    def _export_plan_as_markdown(self, plan) -> str:
        """Generate markdown format of the plan"""
        
        lines = [
            f"# {plan.plan_name}",
            f"",
            f"**Destination:** {self.current_session['destination']}",
            f"**Theme:** {plan.theme} | **Pace:** {plan.pace}",
            f"**Total Budget:** ${plan.total_cost:,.2f}",
            f"",
            f"## 🏨 Accommodation",
            f"- **{plan.accommodation['name']}** ({plan.accommodation['type']})",
            f"- Location: {plan.accommodation['location']}",
            f"- Cost: ${plan.accommodation['cost_per_night']}/night × {plan.accommodation['total_nights']} nights = ${plan.accommodation['cost_per_night'] * plan.accommodation['total_nights']:,.2f}",
            f"",
            f"## 🚗 Transportation",
            f"- Arrival: {plan.transportation['arrival']}",
            f"- Daily: {plan.transportation['daily']}",
            f"- Estimated daily cost: ${plan.transportation['estimated_daily_cost']}",
            f"",
            f"## 🌟 Key Highlights",
            ""
        ]
        
        for highlight in plan.key_highlights:
            lines.append(f"- {highlight}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Daily itineraries
        for day in plan.daily_plans:
            lines.extend([
                f"## Day {day.day_number}: {day.theme}",
                f"**Date:** {day.date} | **Daily Cost:** ${day.total_cost:.2f}",
                ""
            ])
            
            for activity in day.activities:
                lines.extend([
                    f"### {activity.time} - {activity.name}",
                    f"📍 **Location:** {activity.location}",
                    f"💵 **Cost:** ${activity.estimated_cost} | ⏱️ **Duration:** {activity.duration_hours}h",
                    f"",
                    f"{activity.description}",
                    f"",
                    f"*Source: {activity.source}*",
                    ""
                ])
            
            if day.notes:
                lines.extend([
                    f"**📝 Notes:** {day.notes}",
                    ""
                ])
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _save_session(self):
        """Save current session state"""
        
        if not self.current_session:
            return
        
        session_id = self.current_session["session_id"]
        destination = self.current_session["destination"]
        
        filename = f"data/session_{destination.replace(' ', '_').lower()}_{session_id}.json"
        
        # Create serializable version of session
        session_data = {
            "session_id": self.current_session["session_id"],
            "destination": self.current_session["destination"],
            "user_requirements": self.current_session["user_requirements"],
            "stage": self.current_session["stage"],
            "started_at": self.current_session["started_at"],
            "has_research": self.current_session["research_data"] is not None,
            "num_plans": len(self.current_session["plans"]) if self.current_session["plans"] else 0,
            "selected_plan_id": self.current_session["selected_plan"].plan_id if self.current_session.get("selected_plan") else None,
            "refinement_count": len(self.refinement_agent.refinement_history)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)


# Example usage
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = TravelPlanningOrchestrator(
        gemini_api_key="your-gemini-api-key",
        reddit_client_id="your-reddit-client-id",
        reddit_client_secret="your-reddit-secret",
        reddit_user_agent="TravelPlannerBot/1.0"
    )
    
    # Define user requirements
    user_requirements = {
        "destination": "Tokyo",
        "start_date": "2025-12-01",
        "duration_days": 7,
        "budget": 3000.00,
        "travelers": 2,
        "preferences": {
            "interests": ["food", "culture", "photography"],
            "pace": "moderate",
            "style": "authentic_local"
        }
    }
    
    # STAGE 1-3: Research, Plan, Validate
    session = orchestrator.plan_trip(
        user_requirements=user_requirements,
        max_youtube_videos=3,  # Start small for testing
        max_reddit_posts=10
    )
    
    # Display options to user
    orchestrator.present_plans_summary()
    
    # STAGE 4: User selects and refines
    orchestrator.select_and_refine_plan(
        selected_plan_id="B",  # User chooses Plan B
        user_feedback="I want more time exploring Shibuya, and replace the expensive restaurant with local ramen spots under $20"
    )
    
    # Optional: Continue refining
    # orchestrator.continue_refinement(
    #     "Also add a visit to teamLab Borderless on Day 3"
    # )
    
    # Export final plan
    orchestrator.export_final_plan(format="markdown")
    orchestrator.export_final_plan(format="json")
    
    print("\n" + "="*70)
    print("🎉 TRAVEL PLANNING COMPLETE!")
    print("="*70)