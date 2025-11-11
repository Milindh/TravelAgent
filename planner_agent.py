"""
Travel Planner Agent
Creates 3 distinct itinerary options based on research data and user requirements
"""

import json
import requests
from typing import Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

@dataclass
class Activity:
    """Single activity in the itinerary"""
    time: str
    name: str
    location: str
    description: str
    estimated_cost: float
    duration_hours: float
    category: str  # e.g., "dining", "sightseeing", "culture"
    source: str  # Attribution to YouTube/Reddit source

@dataclass
class DayPlan:
    """Plan for a single day"""
    day_number: int
    date: str
    theme: str
    activities: List[Activity]
    total_cost: float
    notes: str

@dataclass
class TravelPlan:
    """Complete travel plan"""
    plan_id: str
    plan_name: str
    theme: str
    total_cost: float
    cost_breakdown: Dict[str, float]
    daily_plans: List[DayPlan]
    accommodation: Dict
    transportation: Dict
    key_highlights: List[str]
    pace: str  # "relaxed", "moderate", "packed"


class PlannerAgent:
    def __init__(self, gemini_api_key: str):
        """Initialize Planner Agent"""
        self.gemini_api_key = gemini_api_key
        self.gemini_api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent'
        
    def create_plans(
        self,
        research_data: Dict,
        user_requirements: Dict
    ) -> List[TravelPlan]:
        """
        Main planning method - creates 3 distinct travel plans
        
        Args:
            research_data: Output from Research Agent
            user_requirements: {
                "destination": str,
                "start_date": str (YYYY-MM-DD),
                "duration_days": int,
                "budget": float,
                "travelers": int,
                "preferences": Dict (interests, pace, style)
            }
        
        Returns:
            List of 3 TravelPlan objects
        """
        print(f"\n📋 Creating 3 travel plans for {user_requirements['destination']}...")
        
        destination = user_requirements["destination"]
        budget = user_requirements["budget"]
        
        # Define 3 different plan themes based on budget
        plan_themes = [
            {
                "id": "A",
                "name": f"{destination} Budget Explorer",
                "theme": "budget",
                "budget_allocation": budget * 0.75,
                "accommodation_level": "budget",
                "dining_style": "local_cheap",
                "pace": "packed",
                "focus": "Maximize experiences while minimizing costs"
            },
            {
                "id": "B",
                "name": f"{destination} Balanced Adventure",
                "theme": "balanced",
                "budget_allocation": budget,
                "accommodation_level": "mid-range",
                "dining_style": "mixed",
                "pace": "moderate",
                "focus": "Best mix of comfort and authentic experiences"
            },
            {
                "id": "C",
                "name": f"{destination} Premium Experience",
                "theme": "luxury",
                "budget_allocation": budget * 1.3,
                "accommodation_level": "upscale",
                "dining_style": "fine_dining",
                "pace": "relaxed",
                "focus": "Curated high-end experiences with comfort"
            }
        ]
        
        plans = []
        
        for theme_config in plan_themes:
            print(f"\n  Creating Plan {theme_config['id']}: {theme_config['name']}...")
            
            plan = self._generate_single_plan(
                research_data=research_data,
                user_requirements=user_requirements,
                theme_config=theme_config
            )
            
            plans.append(plan)
            print(f"    ✓ Plan {theme_config['id']} complete - Total: ${plan.total_cost:.2f}")
        
        print(f"\n✅ All 3 plans created!")
        return plans
    
    def _generate_single_plan(
        self,
        research_data: Dict,
        user_requirements: Dict,
        theme_config: Dict
    ) -> TravelPlan:
        """Generate a single travel plan using LLM"""
        
        # Prepare context for LLM
        context = self._prepare_planning_context(
            research_data,
            user_requirements,
            theme_config
        )
        
        # Generate plan via LLM
        plan_json = self._call_planner_llm(context)
        
        # Parse and structure the plan
        travel_plan = self._parse_plan_json(plan_json, theme_config)
        
        return travel_plan
    
    def _prepare_planning_context(
        self,
        research_data: Dict,
        user_requirements: Dict,
        theme_config: Dict
    ) -> str:
        """Prepare context string for LLM"""
        
        # Extract key insights
        youtube_insights = "\n".join([
            f"- {video['title']} (by {video['channel']}): {video['transcript'][:300]}..."
            for video in research_data.get('youtube_insights', [])[:3]
        ])
        
        reddit_insights = "\n".join([
            f"- Reddit ({post['score']} upvotes): {post['title']}"
            for post in research_data.get('reddit_insights', [])[:5]
        ])
        
        summary_insights = "\n".join([
            f"- {insight}"
            for insight in research_data.get('summary_insights', [])
        ])
        
        context = f"""You are an expert travel planner creating a {theme_config['theme']} itinerary.

DESTINATION: {user_requirements['destination']}
DURATION: {user_requirements['duration_days']} days
BUDGET: ${theme_config['budget_allocation']:.2f}
START DATE: {user_requirements['start_date']}
TRAVELERS: {user_requirements['travelers']}
PREFERENCES: {user_requirements.get('preferences', {})}

PLAN THEME: {theme_config['name']}
FOCUS: {theme_config['focus']}
ACCOMMODATION LEVEL: {theme_config['accommodation_level']}
DINING STYLE: {theme_config['dining_style']}
PACE: {theme_config['pace']}

RESEARCH INSIGHTS:

YouTube Travel Guides:
{youtube_insights}

Reddit Community Insights:
{reddit_insights}

Key Summary Points:
{summary_insights}

Create a detailed day-by-day itinerary that:
1. Stays within the budget (±5%)
2. Matches the {theme_config['pace']} pace
3. Reflects the {theme_config['theme']} style
4. Cites sources from research (YouTube videos, Reddit posts)
5. Includes realistic timing and costs
6. Groups activities logically by location
"""
        
        return context
    
    def _call_planner_llm(self, context: str) -> Dict:
        """Call Gemini LLM to generate the plan"""
        
        system_instruction = """You are a professional travel planner. Create detailed, realistic itineraries in JSON format.

For each day, include:
- 4-7 activities (depending on pace)
- Specific timing (e.g., "09:00", "14:30")
- Realistic costs
- Activity descriptions
- Location names
- Duration in hours
- Category (dining, sightseeing, culture, shopping, etc.)
- Source attribution with URL (format: "YouTube: [Title] - [URL]" or "Reddit: [Title] - [URL]")

IMPORTANT: For source attribution, you MUST include the actual URL from the research data provided.
Format: "YouTube: Video Title (by Channel Name) - https://youtube.com/watch?v=..."
or "Reddit: Post Title - https://reddit.com/r/travel/comments/..."

Also include:
- Accommodation recommendations with costs
- Transportation suggestions
- Daily cost breakdowns
- Key highlights of the trip

Output ONLY valid JSON, no markdown formatting."""

        user_prompt = f"""{context}

Return a JSON object with this structure:
{{
  "daily_plans": [
    {{
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "theme": "Day theme",
      "activities": [
        {{
          "time": "09:00",
          "name": "Activity name",
          "location": "Specific location",
          "description": "What to do",
          "estimated_cost": 25.00,
          "duration_hours": 2.0,
          "category": "sightseeing",
          "source": "YouTube: Video Title or Reddit: Post Title"
        }}
      ],
      "notes": "Any special notes for this day"
    }}
  ],
  "accommodation": {{
    "name": "Hotel/Hostel name",
    "type": "hotel/hostel/airbnb",
    "location": "Neighborhood",
    "cost_per_night": 80.00,
    "total_nights": 7
  }},
  "transportation": {{
    "arrival": "Airport transfer method and cost",
    "daily": "How to get around (subway pass, etc.)",
    "estimated_daily_cost": 10.00
  }},
  "key_highlights": ["Highlight 1", "Highlight 2", "Highlight 3"]
}}"""

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
            plan_text = result['candidates'][0]['content']['parts'][0]['text']
            plan_json = json.loads(plan_text)
            
            return plan_json
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            raise
    
    def _parse_plan_json(self, plan_json: Dict, theme_config: Dict) -> TravelPlan:
        """Parse LLM JSON output into TravelPlan object"""
        
        # Parse daily plans
        daily_plans = []
        total_activities_cost = 0
        
        for day_data in plan_json['daily_plans']:
            activities = []
            day_cost = 0
            
            for act_data in day_data['activities']:
                activity = Activity(
                    time=act_data['time'],
                    name=act_data['name'],
                    location=act_data['location'],
                    description=act_data['description'],
                    estimated_cost=act_data['estimated_cost'],
                    duration_hours=act_data['duration_hours'],
                    category=act_data['category'],
                    source=act_data['source']
                )
                activities.append(activity)
                day_cost += act_data['estimated_cost']
            
            day_plan = DayPlan(
                day_number=day_data['day_number'],
                date=day_data['date'],
                theme=day_data['theme'],
                activities=activities,
                total_cost=day_cost,
                notes=day_data.get('notes', '')
            )
            daily_plans.append(day_plan)
            total_activities_cost += day_cost
        
        # Calculate total cost
        accommodation = plan_json['accommodation']
        accommodation_cost = accommodation['cost_per_night'] * accommodation['total_nights']
        
        transportation = plan_json['transportation']
        transport_cost = transportation.get('estimated_daily_cost', 0) * len(daily_plans)
        
        total_cost = total_activities_cost + accommodation_cost + transport_cost
        
        # Create TravelPlan
        travel_plan = TravelPlan(
            plan_id=theme_config['id'],
            plan_name=theme_config['name'],
            theme=theme_config['theme'],
            total_cost=total_cost,
            cost_breakdown={
                'activities': total_activities_cost,
                'accommodation': accommodation_cost,
                'transportation': transport_cost
            },
            daily_plans=daily_plans,
            accommodation=accommodation,
            transportation=transportation,
            key_highlights=plan_json['key_highlights'],
            pace=theme_config['pace']
        )
        
        return travel_plan
    
    def save_plans(self, plans: List[TravelPlan], destination: str):
        """Save plans to JSON file"""
        plans_dict = {
            'generated_at': datetime.now().isoformat(),
            'destination': destination,
            'plans': [self._plan_to_dict(plan) for plan in plans]
        }
        
        filename = f"data/plans_{destination.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(plans_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Plans saved to: {filename}")
    
    def _plan_to_dict(self, plan: TravelPlan) -> Dict:
        """Convert TravelPlan to dictionary for JSON serialization"""
        return {
            'plan_id': plan.plan_id,
            'plan_name': plan.plan_name,
            'theme': plan.theme,
            'total_cost': plan.total_cost,
            'cost_breakdown': plan.cost_breakdown,
            'pace': plan.pace,
            'key_highlights': plan.key_highlights,
            'accommodation': plan.accommodation,
            'transportation': plan.transportation,
            'daily_plans': [
                {
                    'day_number': day.day_number,
                    'date': day.date,
                    'theme': day.theme,
                    'total_cost': day.total_cost,
                    'notes': day.notes,
                    'activities': [asdict(act) for act in day.activities]
                }
                for day in plan.daily_plans
            ]
        }


# Example usage
if __name__ == "__main__":
    # Load research data
    with open('data/research_tokyo_20250107_123456.json', 'r') as f:
        research_data = json.load(f)
    
    # Initialize planner
    planner = PlannerAgent(gemini_api_key="your-gemini-api-key")
    
    # User requirements
    user_requirements = {
        "destination": "Tokyo",
        "start_date": "2025-12-01",
        "duration_days": 7,
        "budget": 3000.00,
        "travelers": 2,
        "preferences": {
            "interests": ["food", "culture", "photography"],
            "pace": "moderate",
            "dietary_restrictions": []
        }
    }
    
    # Create plans
    plans = planner.create_plans(research_data, user_requirements)
    
    # Display summary
    for plan in plans:
        print(f"\n{'='*60}")
        print(f"Plan {plan.plan_id}: {plan.plan_name}")
        print(f"Theme: {plan.theme} | Pace: {plan.pace}")
        print(f"Total Cost: ${plan.total_cost:.2f}")
        print(f"Key Highlights: {', '.join(plan.key_highlights[:3])}")
    
    # Save plans
    planner.save_plans(plans, user_requirements['destination'])