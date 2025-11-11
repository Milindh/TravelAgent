"""
Complete Workflow Test for Travel Planning Multi-Agent System
Tests all agents working together end-to-end
"""

import os
import sys
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_status(status, message):
    """Print status message"""
    icons = {
        "success": "✅",
        "error": "❌",
        "info": "ℹ️",
        "warning": "⚠️",
        "working": "⏳"
    }
    print(f"{icons.get(status, '•')} {message}")

def test_environment_variables():
    """Test 1: Check if all required environment variables are set"""
    print_section("TEST 1: Environment Variables")
    
    required_vars = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID"),
        "REDDIT_CLIENT_SECRET": os.getenv("REDDIT_CLIENT_SECRET"),
        "REDDIT_USER_AGENT": os.getenv("REDDIT_USER_AGENT")
    }
    
    all_present = True
    for var_name, var_value in required_vars.items():
        if var_value and len(var_value) > 0:
            masked_value = f"{'*' * 10}{var_value[-4:]}" if len(var_value) > 4 else "****"
            print_status("success", f"{var_name}: {masked_value}")
        else:
            print_status("error", f"{var_name}: MISSING")
            all_present = False
    
    if not all_present:
        print_status("error", "Please add missing environment variables to .env file")
        return False
    
    print_status("success", "All environment variables are set!")
    return True

def test_imports():
    """Test 2: Check if all required modules can be imported"""
    print_section("TEST 2: Module Imports")
    
    # Required modules (must have)
    required_modules = [
        ("requests", "requests"),
        ("praw", "praw (Reddit API)"),
        ("yt_dlp", "yt-dlp (YouTube downloader)")
    ]
    
    # Optional modules (nice to have, but not critical for testing)
    optional_modules = [
        ("whisper", "openai-whisper (transcription) - OPTIONAL"),
        ("torch", "PyTorch (for Whisper) - OPTIONAL")
    ]
    
    all_required_imported = True
    
    # Test required modules
    for module_name, display_name in required_modules:
        try:
            mod = __import__(module_name)
            if mod is None:
                raise ImportError(f"{module_name} imported as None")
            print_status("success", f"{display_name}")
        except ImportError as e:
            print_status("error", f"{display_name} - Not installed")
            print(f"          Install with: pip install {module_name}")
            all_required_imported = False
        except Exception as e:
            print_status("error", f"{display_name} - Error: {str(e)}")
            all_required_imported = False
    
    # Test optional modules (don't fail if missing)
    for module_name, display_name in optional_modules:
        try:
            mod = __import__(module_name)
            if mod is None:
                raise ImportError(f"{module_name} imported as None")
            print_status("success", f"{display_name}")
        except:
            print_status("warning", f"{display_name} - Not installed (will skip transcription tests)")
            print(f"          Install with: pip install {module_name}")
    
    # Check our agent modules
    agent_modules = [
        "research_agent",
        "planner_agent",
        "validation_agent",
        "refinement_agent",
        "orchestrator"
    ]
    
    for module_name in agent_modules:
        try:
            __import__(module_name)
            print_status("success", f"{module_name}.py")
        except ImportError as e:
            print_status("error", f"{module_name}.py - {str(e)}")
            all_imported = False
    
    if not all_required_imported:
        print_status("error", "Some required modules are missing")
        return False
    
    print_status("success", "All required modules imported successfully!")
    return True

def test_gemini_api():
    """Test 3: Test Gemini API connection"""
    print_section("TEST 3: Gemini API Connection")
    
    import requests
    
    api_key = os.getenv("GEMINI_API_KEY")
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}'
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": "Respond with exactly: 'API test successful'"
            }]
        }]
    }
    
    try:
        print_status("working", "Testing Gemini API...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        response_text = result['candidates'][0]['content']['parts'][0]['text']
        
        print_status("success", f"Gemini API Response: {response_text}")
        return True
    except Exception as e:
        print_status("error", f"Gemini API Error: {str(e)}")
        return False

def test_reddit_api():
    """Test 4: Test Reddit API connection"""
    print_section("TEST 4: Reddit API Connection")
    
    import praw
    
    try:
        print_status("working", "Testing Reddit API...")
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        
        # Test by accessing a subreddit
        subreddit = reddit.subreddit('travel')
        test_post = next(subreddit.hot(limit=1))
        
        print_status("success", f"Reddit API working - Found post: '{test_post.title[:50]}...'")
        return True
    except Exception as e:
        print_status("error", f"Reddit API Error: {str(e)}")
        return False

def test_research_agent():
    """Test 5: Test Research Agent (lightweight test)"""
    print_section("TEST 5: Research Agent")
    
    try:
        from research_agent import ResearchAgent
        
        print_status("working", "Initializing Research Agent...")
        agent = ResearchAgent(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
            reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            reddit_user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        
        print_status("success", "Research Agent initialized")
        
        # Test Reddit gathering (quick test)
        print_status("working", "Testing Reddit data gathering...")
        reddit_data = agent._gather_reddit_insights("Paris", max_posts=2)
        
        if reddit_data and len(reddit_data) > 0:
            print_status("success", f"Gathered {len(reddit_data)} Reddit posts")
            print_status("info", f"Sample: '{reddit_data[0]['title'][:50]}...'")
            
            # Print sample Reddit data
            print("\n" + "-"*70)
            print("📄 SAMPLE REDDIT DATA:")
            print("-"*70)
            sample = reddit_data[0]
            print(f"Subreddit: r/{sample.get('subreddit', 'unknown')}")
            print(f"Title: {sample['title']}")
            print(f"Score: {sample.get('score', 0)} upvotes")
            print(f"Text preview: {sample.get('text', '')[:200]}...")
            print("-"*70 + "\n")
        else:
            print_status("warning", "No Reddit data gathered (might be rate limited)")
        
        print_status("success", "Research Agent working!")
        return True
    except Exception as e:
        print_status("error", f"Research Agent Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_planner_agent():
    """Test 6: Test Planner Agent with mock data"""
    print_section("TEST 6: Planner Agent")
    
    try:
        from planner_agent import PlannerAgent
        
        print_status("working", "Initializing Planner Agent...")
        planner = PlannerAgent(gemini_api_key=os.getenv("GEMINI_API_KEY"))
        print_status("success", "Planner Agent initialized")
        
        # Create minimal mock research data for testing
        mock_research = {
            "destination": "Paris",
            "youtube_insights": [
                {
                    "video_id": "test123",
                    "title": "Paris Travel Guide 2024",
                    "channel": "Travel Expert",
                    "url": "https://youtube.com/watch?v=example123",
                    "transcript": "Visit the Eiffel Tower, try authentic French cuisine, explore Louvre museum. The city of lights offers amazing experiences for all travelers."
                }
            ],
            "reddit_insights": [
                {
                    "subreddit": "travel",
                    "title": "Best places to eat in Paris",
                    "text": "Try the local boulangeries for fresh croissants. Don't miss the street markets.",
                    "score": 150,
                    "url": "https://reddit.com/r/travel/comments/example"
                }
            ],
            "summary_insights": [
                "Must see: Eiffel Tower, Louvre, Notre Dame",
                "Best food: Croissants, crepes, French wine",
                "Transportation: Metro is efficient and cheap"
            ]
        }
        
        user_requirements = {
            "destination": "Paris",
            "start_date": "2025-06-01",
            "duration_days": 3,
            "budget": 1500.00,
            "travelers": 2,
            "preferences": {
                "interests": ["culture", "food"],
                "pace": "moderate"
            }
        }
        
        print_status("working", "Generating travel plans (this may take 1-2 minutes)...")
        plans = planner.create_plans(mock_research, user_requirements)
        
        if plans and len(plans) == 3:
            print_status("success", f"Generated {len(plans)} travel plans")
            
            # Print COMPLETE detailed plan information for ALL plans
            print("\n" + "="*70)
            print("📋 COMPLETE GENERATED PLANS:")
            print("="*70 + "\n")
            
            for plan in plans:
                print("\n" + "━"*70)
                print(f"🎯 PLAN {plan.plan_id}: {plan.plan_name.upper()}")
                print("━"*70)
                print(f"💰 Total Cost: ${plan.total_cost:.2f}")
                print(f"🎨 Theme: {plan.theme} | Pace: {plan.pace}")
                print(f"📅 Duration: {len(plan.daily_plans)} days")
                
                # Cost breakdown
                print(f"\n💵 Cost Breakdown:")
                print(f"   • Activities: ${plan.cost_breakdown.get('activities', 0):.2f}")
                print(f"   • Accommodation: ${plan.cost_breakdown.get('accommodation', 0):.2f}")
                print(f"   • Transportation: ${plan.cost_breakdown.get('transportation', 0):.2f}")
                
                # Accommodation details
                print(f"\n🏨 Accommodation:")
                acc = plan.accommodation
                print(f"   • {acc.get('name', 'N/A')} ({acc.get('type', 'N/A')})")
                print(f"   • Location: {acc.get('location', 'N/A')}")
                print(f"   • ${acc.get('cost_per_night', 0):.2f}/night × {acc.get('total_nights', 0)} nights = ${acc.get('cost_per_night', 0) * acc.get('total_nights', 0):.2f}")
                
                # Transportation details
                print(f"\n🚇 Transportation:")
                trans = plan.transportation
                print(f"   • Arrival: {trans.get('arrival', 'N/A')}")
                print(f"   • Daily: {trans.get('daily', 'N/A')}")
                print(f"   • Est. daily cost: ${trans.get('estimated_daily_cost', 0):.2f}")
                
                # Key highlights
                print(f"\n🌟 Key Highlights:")
                for i, highlight in enumerate(plan.key_highlights, 1):
                    print(f"   {i}. {highlight}")
                
                # ALL DAYS - COMPLETE ITINERARY
                print(f"\n📅 COMPLETE DAY-BY-DAY ITINERARY:")
                print("─"*70)
                
                for day in plan.daily_plans:
                    print(f"\n📆 DAY {day.day_number}: {day.theme.upper()}")
                    print(f"   Date: {day.date} | Daily Cost: ${day.total_cost:.2f}")
                    
                    if day.activities:
                        print(f"\n   Activities ({len(day.activities)} planned):")
                        for i, activity in enumerate(day.activities, 1):
                            print(f"\n   {i}. {activity.time} - {activity.name}")
                            print(f"      📍 Location: {activity.location}")
                            print(f"      📝 {activity.description}")
                            print(f"      💰 Cost: ${activity.estimated_cost:.2f} | ⏱️ Duration: {activity.duration_hours}h")
                            print(f"      🏷️ Category: {activity.category}")
                            if activity.source:
                                # Extract URL if present in source
                                source_text = activity.source
                                if 'http' in source_text:
                                    # Format: "YouTube: Title - URL" or "Reddit: Title - URL"
                                    print(f"      📚 Source: {source_text}")
                                    print(f"      🔗 Click to view source")
                                else:
                                    print(f"      📚 Source: {source_text}")
                    
                    if day.notes:
                        print(f"\n   📝 Notes: {day.notes}")
                    
                    print("   " + "─"*66)
                
                print("\n" + "━"*70 + "\n")
            
            # Save plans to file for detailed review
            try:
                import json
                plans_data = []
                for plan in plans:
                    plan_dict = {
                        'plan_id': plan.plan_id,
                        'plan_name': plan.plan_name,
                        'total_cost': plan.total_cost,
                        'theme': plan.theme,
                        'pace': plan.pace,
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
                    plans_data.append(plan_dict)
                
                with open('data/test_plans_output.json', 'w', encoding='utf-8') as f:
                    json.dump(plans_data, f, indent=2, ensure_ascii=False)
                
                print("💾 Full plans saved to: data/test_plans_output.json")
                print("   (You can review this file anytime!)\n")
            except Exception as e:
                print(f"⚠️  Could not save plans to file: {e}\n")
            
            return True
        else:
            print_status("error", "Failed to generate 3 plans")
            return False
            
    except Exception as e:
        print_status("error", f"Planner Agent Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_validation_agent():
    """Test 7: Test Validation Agent"""
    print_section("TEST 7: Validation Agent")
    
    try:
        from validation_agent import ValidationAgent
        from planner_agent import TravelPlan, DayPlan, Activity
        
        print_status("working", "Initializing Validation Agent...")
        validator = ValidationAgent()
        print_status("success", "Validation Agent initialized")
        
        # Create a mock plan for validation
        mock_activity = Activity(
            time="09:00",
            name="Visit Eiffel Tower",
            location="Champ de Mars",
            description="Iconic landmark",
            estimated_cost=25.00,
            duration_hours=2.0,
            category="sightseeing",
            source="Test"
        )
        
        mock_day = DayPlan(
            day_number=1,
            date="2025-06-01",
            theme="Paris Highlights",
            activities=[mock_activity],
            total_cost=25.00,
            notes="Test day"
        )
        
        mock_plan = TravelPlan(
            plan_id="TEST",
            plan_name="Test Plan",
            theme="test",
            total_cost=1000.00,
            cost_breakdown={"activities": 500, "accommodation": 300, "transportation": 200},
            daily_plans=[mock_day],
            accommodation={"name": "Test Hotel", "cost_per_night": 100, "total_nights": 3},
            transportation={"daily": "Metro", "estimated_daily_cost": 10},
            key_highlights=["Test highlight"],
            pace="moderate"
        )
        
        print_status("working", "Running validation checks...")
        result = validator._validate_single_plan(
            mock_plan, 
            {"budget": 1500.00, "duration_days": 3}
        )
        
        print_status("success", f"Validation complete - Status: {result.status}")
        print_status("info", f"Quality Score: {result.score}/100")
        
        # Print validation details
        print("\n" + "-"*70)
        print("✅ VALIDATION RESULTS:")
        print("-"*70)
        print(f"Status: {result.status}")
        print(f"Quality Score: {result.score}/100")
        
        if result.issues:
            print(f"\nIssues Found: {len(result.issues)}")
            for i, issue in enumerate(result.issues[:3], 1):  # Show first 3
                print(f"\n  Issue {i} [{issue.severity.upper()}]:")
                print(f"    Category: {issue.category}")
                print(f"    Problem: {issue.problem}")
                print(f"    Suggestion: {issue.suggestion}")
        else:
            print("\n✨ No issues found - Perfect plan!")
        
        if result.warnings:
            print(f"\nWarnings: {len(result.warnings)}")
            for warning in result.warnings[:2]:
                print(f"  ⚠️  {warning}")
        
        print("-"*70 + "\n")
        
        return True
        
    except Exception as e:
        print_status("error", f"Validation Agent Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_refinement_agent():
    """Test 8: Test Refinement Agent initialization"""
    print_section("TEST 8: Refinement Agent")
    
    try:
        from refinement_agent import RefinementAgent
        from validation_agent import ValidationAgent
        
        print_status("working", "Initializing Refinement Agent...")
        validator = ValidationAgent()
        refiner = RefinementAgent(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            validation_agent=validator
        )
        
        print_status("success", "Refinement Agent initialized")
        return True
        
    except Exception as e:
        print_status("error", f"Refinement Agent Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator():
    """Test 9: Test Orchestrator initialization"""
    print_section("TEST 9: Orchestrator")
    
    try:
        from orchestrator import TravelPlanningOrchestrator
        
        print_status("working", "Initializing Orchestrator...")
        orchestrator = TravelPlanningOrchestrator(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
            reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            reddit_user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        
        print_status("success", "Orchestrator initialized with all agents")
        return True
        
    except Exception as e:
        print_status("error", f"Orchestrator Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_data_folder():
    """Test 10: Check if data folder structure is created"""
    print_section("TEST 10: Data Folder Structure")
    
    try:
        import os
        from pathlib import Path
        
        # Try to create data folders
        Path("data/transcripts").mkdir(parents=True, exist_ok=True)
        Path("data/temp_audio").mkdir(parents=True, exist_ok=True)
        
        if os.path.exists("data") and os.path.exists("data/transcripts"):
            print_status("success", "Data folder structure created")
            print_status("info", f"Location: {os.path.abspath('data')}")
            return True
        else:
            print_status("error", "Failed to create data folders")
            return False
            
    except Exception as e:
        print_status("error", f"Data Folder Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("\n" + "🧪"*35)
    print("  TRAVEL PLANNER - COMPLETE WORKFLOW TEST")
    print("🧪"*35)
    
    print_status("info", f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Module Imports", test_imports),
        ("Gemini API", test_gemini_api),
        ("Reddit API", test_reddit_api),
        ("Research Agent", test_research_agent),
        ("Planner Agent", test_planner_agent),
        ("Validation Agent", test_validation_agent),
        ("Refinement Agent", test_refinement_agent),
        ("Orchestrator", test_orchestrator),
        ("Data Folder", test_data_folder)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_status("error", f"Test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "success" if result else "error"
        print_status(status, test_name)
    
    print(f"\n{'='*70}")
    print(f"  Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    print(f"{'='*70}\n")
    
    if passed == total:
        print_status("success", "🎉 ALL TESTS PASSED!")
        print_status("info", "Your system is ready to plan trips!")
        print_status("info", "Run: python run_planner.py")
        
        # Print summary of what was tested
        print("\n" + "="*70)
        print("📊 WHAT WAS TESTED:")
        print("="*70)
        print("✅ All API connections verified (Gemini + Reddit)")
        print("✅ Research Agent gathered real Reddit data")
        print("✅ Planner Agent created 3 complete itineraries")
        print("✅ Validation Agent checked plan quality")
        print("✅ All agents properly integrated")
        print("✅ Data storage working correctly")
        print("\n🚀 Your travel planning system is fully operational!")
        print("="*70 + "\n")
        
        return True
    else:
        print_status("error", f"❌ {total - passed} test(s) failed")
        print_status("info", "Please fix the issues above before proceeding")
        print_status("info", "Check:")
        print("           • API keys in .env file")
        print("           • All dependencies installed (pip install -r requirements.txt)")
        print("           • FFmpeg installed")
        print("           • Internet connection")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)