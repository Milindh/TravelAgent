"""
Simple example script to run the Travel Planning Multi-Agent System
"""

import os
from dotenv import load_dotenv
from orchestrator import TravelPlanningOrchestrator

# Load environment variables from .env file
load_dotenv()

def main():
    print("🌍 Welcome to AI Travel Planner!\n")
    
    # Initialize the orchestrator with API keys from .env
    orchestrator = TravelPlanningOrchestrator(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT")
    )
    
    # Define your trip requirements
    user_requirements = {
        "destination": "Tokyo",           # Where you want to go
        "start_date": "2025-12-01",       # Trip start date (YYYY-MM-DD)
        "duration_days": 7,               # How many days
        "budget": 3000.00,                # Total budget in USD
        "travelers": 2,                   # Number of people
        "preferences": {
            "interests": ["food", "culture", "photography", "shopping"],
            "pace": "moderate",           # relaxed/moderate/fast
            "style": "authentic_local"    # What kind of experience
        }
    }
    
    print(f"📍 Planning a {user_requirements['duration_days']}-day trip to {user_requirements['destination']}")
    print(f"💰 Budget: ${user_requirements['budget']:,.2f}")
    print(f"👥 Travelers: {user_requirements['travelers']}")
    print(f"🎯 Interests: {', '.join(user_requirements['preferences']['interests'])}\n")
    
    # STAGE 1-3: Research, Plan, and Validate
    print("Starting the planning process...\n")
    
    session = orchestrator.plan_trip(
        user_requirements=user_requirements,
        max_youtube_videos=3,    # Start with 3 videos (faster for testing)
        max_reddit_posts=10      # Get 10 Reddit posts
    )
    
    # Display the 3 options to the user
    orchestrator.present_plans_summary()
    
    # STAGE 4: User selects a plan and provides feedback
    print("\n" + "="*70)
    print("🎯 SELECTING AND REFINING YOUR PLAN")
    print("="*70 + "\n")
    
    # Example: User selects Plan B and wants some changes
    selected_plan = "B"  # Choose A, B, or C
    
    user_feedback = """
    I like this plan overall, but I'd like to make a few changes:
    1. Add more time exploring Shibuya district
    2. Replace the expensive dinner on Day 3 with local ramen spots (under $20 per person)
    3. Include a visit to teamLab Borderless digital art museum
    """
    
    print(f"You selected: Plan {selected_plan}")
    print(f"\nYour feedback:")
    print(user_feedback)
    
    orchestrator.select_and_refine_plan(
        selected_plan_id=selected_plan,
        user_feedback=user_feedback
    )
    
    # Optional: Continue refining if needed
    # orchestrator.continue_refinement(
    #     "Actually, can we also add a sushi-making class on Day 4?"
    # )
    
    # EXPORT: Save your final plan
    print("\n" + "="*70)
    print("💾 EXPORTING YOUR FINAL PLAN")
    print("="*70 + "\n")
    
    # Export in multiple formats
    markdown_file = orchestrator.export_final_plan(format="markdown")
    json_file = orchestrator.export_final_plan(format="json")
    
    print(f"\n✅ Your trip plan is ready!")
    print(f"\n📄 Files created:")
    print(f"   - Markdown: {markdown_file}")
    print(f"   - JSON: {json_file}")
    
    print(f"\n🎉 Happy travels to {user_requirements['destination']}! ✈️")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Planning interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check:")
        print("  1. All API keys are set in .env file")
        print("  2. Internet connection is working")
        print("  3. Run test_setup.py to verify configuration")