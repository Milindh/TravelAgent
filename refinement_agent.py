"""
Travel Refinement Agent
Handles user feedback and iteratively modifies selected travel plans
"""

from typing import Dict, List, Optional
import requests
from datetime import datetime
import json


class RefinementAgent:
    """Refines travel plans based on user feedback"""
    
    def __init__(self, gemini_api_key: str, validation_agent):
        """
        Initialize Refinement Agent
        
        Args:
            gemini_api_key: Gemini API key for LLM calls
            validation_agent: Instance of ValidationAgent for re-validation
        """
        self.gemini_api_key = gemini_api_key
        self.gemini_api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent'
        self.validation_agent = validation_agent
        self.refinement_history = []
    
    def refine_plan(
        self,
        original_plan,  # TravelPlan object
        user_feedback: str,
        user_requirements: Dict,
        research_data: Optional[Dict] = None
    ):
        """
        Refine a travel plan based on user feedback
        
        Args:
            original_plan: The TravelPlan object user selected
            user_feedback: Natural language feedback from user
            user_requirements: Original user requirements (budget, dates, etc.)
            research_data: Optional research data for adding new activities
        
        Returns:
            Refined TravelPlan object
        """
        print(f"\n🔧 Refining Plan {original_plan.plan_id}...")
        print(f"User feedback: {user_feedback}")
        
        # Parse user feedback to understand what changes are needed
        change_requests = self._parse_feedback(user_feedback, original_plan)
        
        print(f"\n  Identified {len(change_requests)} change requests:")
        for req in change_requests:
            print(f"    - {req['type']}: {req['description']}")
        
        # Apply changes
        refined_plan = self._apply_changes(
            original_plan,
            change_requests,
            user_requirements,
            research_data
        )
        
        # Re-validate the refined plan
        print(f"\n  Re-validating refined plan...")
        validation_result = self.validation_agent._validate_single_plan(
            refined_plan,
            user_requirements
        )
        
        # Store refinement in history
        self.refinement_history.append({
            'timestamp': datetime.now().isoformat(),
            'feedback': user_feedback,
            'changes': change_requests,
            'validation_status': validation_result.status,
            'validation_score': validation_result.score
        })
        
        print(f"  ✓ Refinement complete!")
        print(f"  Validation: {validation_result.status} (Score: {validation_result.score:.1f}/100)")
        
        if validation_result.issues:
            print(f"  ⚠ {len(validation_result.issues)} issues found in refined plan")
            for issue in validation_result.issues[:3]:  # Show first 3
                print(f"    - [{issue.severity}] {issue.problem}")
        
        return refined_plan, validation_result
    
    def _parse_feedback(self, feedback: str, original_plan) -> List[Dict]:
        """
        Use Gemini LLM to parse natural language feedback into structured change requests
        """
        
        # Prepare plan summary for context
        plan_summary = self._create_plan_summary(original_plan)
        
        system_instruction = """You are an expert at understanding travel plan modification requests.
Parse the user's feedback into specific, actionable change requests.

Change types:
- "add": Add new activity/experience
- "remove": Remove existing activity
- "replace": Replace one activity with another
- "modify": Adjust timing, cost, or details of existing activity
- "rebalance": Adjust pace, redistribute time/budget

Output JSON array of change requests with this structure:
[
  {
    "type": "add|remove|replace|modify|rebalance",
    "description": "Brief description of the change",
    "target": "What to change (activity name, day number, or 'overall')",
    "details": {
      "specific_details": "Any specific requirements"
    }
  }
]"""

        user_prompt = f"""Current plan summary:
{plan_summary}

User feedback: "{feedback}"

Parse this feedback into structured change requests."""

        full_prompt = f"{system_instruction}\n\n{user_prompt}"

        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(
                f"{self.gemini_api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            parsed_text = result['candidates'][0]['content']['parts'][0]['text']
            parsed = json.loads(parsed_text)
            
            return parsed.get('changes', [])
        except Exception as e:
            print(f"Error parsing feedback with Gemini: {e}")
            return []
    
    def _create_plan_summary(self, plan) -> str:
        """Create a concise summary of the plan for LLM context"""
        
        summary_lines = [
            f"Plan: {plan.plan_name}",
            f"Theme: {plan.theme} | Pace: {plan.pace}",
            f"Total Cost: ${plan.total_cost:.2f}",
            f"Duration: {len(plan.daily_plans)} days",
            "\nDaily breakdown:"
        ]
        
        for day in plan.daily_plans:
            summary_lines.append(f"\nDay {day.day_number} - {day.theme}:")
            for activity in day.activities:
                summary_lines.append(
                    f"  {activity.time} - {activity.name} at {activity.location} "
                    f"(${activity.estimated_cost}, {activity.duration_hours}h)"
                )
        
        return "\n".join(summary_lines)
    
    def _apply_changes(
        self,
        original_plan,
        change_requests: List[Dict],
        user_requirements: Dict,
        research_data: Optional[Dict]
    ):
        """
        Apply change requests to create refined plan
        Uses Gemini LLM to intelligently modify the plan
        """
        
        # Convert plan to JSON for LLM processing
        from copy import deepcopy
        plan_dict = self._plan_to_dict(original_plan)
        
        # Prepare context
        change_descriptions = "\n".join([
            f"{i+1}. {change['type']}: {change['description']}"
            for i, change in enumerate(change_requests)
        ])
        
        research_context = ""
        if research_data:
            research_context = f"""
Research data available:
- {len(research_data.get('youtube_insights', []))} YouTube travel guides
- {len(research_data.get('reddit_insights', []))} Reddit discussions
- Summary insights: {', '.join(research_data.get('summary_insights', [])[:5])}
"""
        
        system_instruction = """You are an expert travel planner modifying an itinerary based on user feedback.

Apply the requested changes while:
1. Maintaining the overall budget (±5%)
2. Keeping daily schedules logical and balanced
3. Ensuring smooth transitions between activities
4. Preserving the overall travel style and pace
5. Citing sources when adding new activities

Return the complete modified plan in the same JSON structure."""

        user_prompt = f"""Original plan:
{json.dumps(plan_dict, indent=2)}

Changes requested:
{change_descriptions}

{research_context}

Budget constraint: ${user_requirements.get('budget', 0):.2f}
Duration: {user_requirements.get('duration_days', 0)} days

Apply these changes and return the complete modified plan as JSON."""

        full_prompt = f"{system_instruction}\n\n{user_prompt}"

        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(
                f"{self.gemini_api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            refined_plan_text = result['candidates'][0]['content']['parts'][0]['text']
            refined_plan_dict = json.loads(refined_plan_text)
            
            # Convert back to TravelPlan object
            refined_plan = self._dict_to_plan(refined_plan_dict, original_plan.plan_id)
            
            return refined_plan
        except Exception as e:
            print(f"Error applying changes with Gemini: {e}")
            return original_plan  # Return original if refinement fails
    
    def _plan_to_dict(self, plan) -> Dict:
        """Convert TravelPlan to dictionary"""
        from dataclasses import asdict
        
        return {
            'plan_id': plan.plan_id,
            'plan_name': plan.plan_name,
            'theme': plan.theme,
            'pace': plan.pace,
            'total_cost': plan.total_cost,
            'cost_breakdown': plan.cost_breakdown,
            'accommodation': plan.accommodation,
            'transportation': plan.transportation,
            'key_highlights': plan.key_highlights,
            'daily_plans': [
                {
                    'day_number': day.day_number,
                    'date': day.date,
                    'theme': day.theme,
                    'total_cost': day.total_cost,
                    'notes': day.notes,
                    'activities': [
                        {
                            'time': act.time,
                            'name': act.name,
                            'location': act.location,
                            'description': act.description,
                            'estimated_cost': act.estimated_cost,
                            'duration_hours': act.duration_hours,
                            'category': act.category,
                            'source': act.source
                        }
                        for act in day.activities
                    ]
                }
                for day in plan.daily_plans
            ]
        }
    
    def _dict_to_plan(self, plan_dict: Dict, plan_id: str):
        """Convert dictionary back to TravelPlan object"""
        # Import here to avoid circular dependency
        from planner_agent import TravelPlan, DayPlan, Activity
        
        # Reconstruct daily plans
        daily_plans = []
        for day_data in plan_dict['daily_plans']:
            activities = [
                Activity(
                    time=act['time'],
                    name=act['name'],
                    location=act['location'],
                    description=act['description'],
                    estimated_cost=act['estimated_cost'],
                    duration_hours=act['duration_hours'],
                    category=act['category'],
                    source=act.get('source', '')
                )
                for act in day_data['activities']
            ]
            
            daily_plans.append(DayPlan(
                day_number=day_data['day_number'],
                date=day_data['date'],
                theme=day_data['theme'],
                activities=activities,
                total_cost=day_data['total_cost'],
                notes=day_data.get('notes', '')
            ))
        
        # Create TravelPlan
        return TravelPlan(
            plan_id=plan_id,
            plan_name=plan_dict['plan_name'],
            theme=plan_dict['theme'],
            total_cost=plan_dict['total_cost'],
            cost_breakdown=plan_dict['cost_breakdown'],
            daily_plans=daily_plans,
            accommodation=plan_dict['accommodation'],
            transportation=plan_dict['transportation'],
            key_highlights=plan_dict['key_highlights'],
            pace=plan_dict['pace']
        )
    
    def interactive_refinement_session(
        self,
        original_plan,
        user_requirements: Dict,
        research_data: Optional[Dict] = None,
        max_iterations: int = 5
    ):
        """
        Interactive refinement session with multiple rounds of feedback
        
        This simulates a conversation where user can make multiple changes
        """
        print(f"\n🔄 Starting interactive refinement session")
        print(f"You can make up to {max_iterations} rounds of changes")
        print("Type 'done' when you're satisfied with the plan\n")
        
        current_plan = original_plan
        iteration = 0
        
        while iteration < max_iterations:
            print(f"\n--- Iteration {iteration + 1}/{max_iterations} ---")
            print(f"Current plan: {current_plan.plan_name}")
            print(f"Total cost: ${current_plan.total_cost:.2f}")
            
            # In a real application, this would get input from UI
            # For demo purposes, we'll show the structure
            feedback = input("\nWhat would you like to change? (or 'done'): ")
            
            if feedback.lower() == 'done':
                print("\n✓ Plan finalized!")
                break
            
            # Refine based on feedback
            current_plan, validation_result = self.refine_plan(
                current_plan,
                feedback,
                user_requirements,
                research_data
            )
            
            iteration += 1
        
        if iteration == max_iterations:
            print(f"\n⚠ Reached maximum iterations ({max_iterations})")
        
        return current_plan
    
    def save_refinement_history(self, destination: str):
        """Save refinement history to file"""
        
        if not self.refinement_history:
            print("No refinement history to save")
            return
        
        filename = f"data/refinement_history_{destination.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.refinement_history, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Refinement history saved to: {filename}")


# Example usage
if __name__ == "__main__":
    from validation_agent import ValidationAgent
    
    # Initialize agents
    validator = ValidationAgent()
    refiner = RefinementAgent(
        gemini_api_key="your-gemini-api-key",
        validation_agent=validator
    )
    
    # In real usage:
    # 1. User selects Plan B from the 3 options
    # selected_plan = plans[1]  # Plan B
    
    # 2. User provides feedback
    # user_feedback = "I want more time in Shibuya, and replace that expensive restaurant with something under $50"
    
    # 3. Refine the plan
    # refined_plan, validation = refiner.refine_plan(
    #     original_plan=selected_plan,
    #     user_feedback=user_feedback,
    #     user_requirements=user_requirements,
    #     research_data=research_data
    # )
    
    # 4. Show user the refined plan
    # 5. Allow further refinements if needed
    
    print("Refinement Agent ready to use!")