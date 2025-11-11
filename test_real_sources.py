"""
Test with REAL Reddit data to verify URL capture
This skips YouTube (slow) and just tests Reddit URLs
"""

import os
from dotenv import load_dotenv
from research_agent import ResearchAgent
from planner_agent import PlannerAgent
import json

load_dotenv()

def test_real_reddit_urls():
    """Test that real Reddit URLs are captured and used"""
    
    print("="*70)
    print("🧪 TESTING REAL SOURCE URLs")
    print("="*70)
    
    # Initialize Research Agent
    print("\n1️⃣ Initializing Research Agent...")
    research_agent = ResearchAgent(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT")
    )
    
    # Gather REAL Reddit data (skip YouTube for speed)
    print("\n2️⃣ Gathering REAL Reddit data for Paris...")
    print("   (This will take ~10-20 seconds)")
    
    reddit_data = research_agent._gather_reddit_insights(
        destination="Paris",
        max_posts=5  # Just 5 posts for quick test
    )
    
    print(f"\n✅ Gathered {len(reddit_data)} Reddit posts")
    
    # Check if URLs are present
    print("\n3️⃣ Checking URLs in Reddit data...")
    urls_found = 0
    
    for i, post in enumerate(reddit_data[:3], 1):  # Check first 3
        url = post.get('url', '')
        if url and 'reddit.com' in url:
            print(f"   ✅ Post {i}: {post['title'][:50]}...")
            print(f"      URL: {url}")
            urls_found += 1
        else:
            print(f"   ❌ Post {i}: No URL or invalid URL")
    
    if urls_found == 0:
        print("\n❌ NO REDDIT URLs FOUND!")
        print("   This is the problem - Research Agent not capturing URLs")
        return False
    
    print(f"\n✅ Found {urls_found} valid Reddit URLs!")
    
    # Create research data with Reddit only
    print("\n4️⃣ Creating research package with real URLs...")
    
    research_data = {
        "destination": "Paris",
        "youtube_insights": [
            {
                "video_id": "placeholder",
                "title": "Paris Travel Guide (Placeholder)",
                "channel": "Test Channel",
                "url": "https://youtube.com/watch?v=test",
                "transcript": "This is a placeholder for YouTube data. In real use, download actual videos."
            }
        ],
        "reddit_insights": reddit_data,  # REAL DATA!
        "summary_insights": [
            "Eiffel Tower is a must-see",
            "Try local bakeries for breakfast",
            "Metro is the best way to get around"
        ]
    }
    
    # Save for inspection
    with open('data/test_real_research.json', 'w', encoding='utf-8') as f:
        json.dump(research_data, f, indent=2, ensure_ascii=False)
    
    print("   ✅ Saved to: data/test_real_research.json")
    
    # Now test with Planner Agent
    print("\n5️⃣ Testing with Planner Agent...")
    print("   (This will take ~2-3 minutes to generate 3 plans)")
    
    planner = PlannerAgent(gemini_api_key=os.getenv("GEMINI_API_KEY"))
    
    user_requirements = {
        "destination": "Paris",
        "start_date": "2025-06-01",
        "duration_days": 3,
        "budget": 1500.00,
        "travelers": 2,
        "preferences": {
            "interests": ["food", "culture"],
            "pace": "moderate"
        }
    }
    
    try:
        plans = planner.create_plans(research_data, user_requirements)
        
        print(f"\n✅ Generated {len(plans)} plans!")
        
        # Check if Reddit URLs appear in plans
        print("\n6️⃣ Checking if Reddit URLs appear in plans...")
        
        total_activities = 0
        activities_with_reddit_urls = 0
        sample_urls = []
        
        for plan in plans:
            for day in plan.daily_plans:
                for activity in day.activities:
                    total_activities += 1
                    source = activity.source or ""
                    
                    if 'reddit.com' in source.lower():
                        activities_with_reddit_urls += 1
                        if len(sample_urls) < 3:
                            sample_urls.append({
                                'activity': activity.name,
                                'source': source
                            })
        
        print(f"\n📊 Results:")
        print(f"   Total activities across all plans: {total_activities}")
        print(f"   Activities with Reddit URLs: {activities_with_reddit_urls}")
        print(f"   Coverage: {activities_with_reddit_urls/max(total_activities,1)*100:.1f}%")
        
        if sample_urls:
            print(f"\n✅ REAL URLs FOUND! Sample:")
            for sample in sample_urls:
                print(f"\n   Activity: {sample['activity']}")
                print(f"   Source: {sample['source'][:100]}...")
        else:
            print(f"\n⚠️  No Reddit URLs in generated plans")
            print(f"   Gemini may not be following instructions to include URLs")
        
        # Save plans
        plans_data = []
        for plan in plans:
            plan_dict = {
                'plan_id': plan.plan_id,
                'plan_name': plan.plan_name,
                'daily_plans': [
                    {
                        'day_number': day.day_number,
                        'activities': [
                            {
                                'name': act.name,
                                'source': act.source
                            }
                            for act in day.activities
                        ]
                    }
                    for day in plan.daily_plans
                ]
            }
            plans_data.append(plan_dict)
        
        with open('data/test_real_plans.json', 'w', encoding='utf-8') as f:
            json.dump(plans_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved plans to: data/test_real_plans.json")
        print(f"   You can inspect this file to see all source attributions")
        
        return activities_with_reddit_urls > 0
        
    except Exception as e:
        print(f"\n❌ Error during planning: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("🎯 OBJECTIVE: Verify real URLs are captured and used")
    print("="*70)
    print("\nThis test will:")
    print("  1. Gather REAL Reddit posts (with actual URLs)")
    print("  2. Pass them to Planner Agent")
    print("  3. Check if URLs appear in generated plans")
    print("\n" + "="*70 + "\n")
    
    success = test_real_reddit_urls()
    
    print("\n" + "="*70)
    if success:
        print("✅ SUCCESS: Real URLs are working!")
        print("="*70)
        print("\n💡 Next steps:")
        print("   1. Run the full system: python run_planner.py")
        print("   2. Real YouTube URLs will also be included")
        print("   3. All source links will be genuine!")
    else:
        print("❌ ISSUE: URLs not appearing in plans")
        print("="*70)
        print("\n💡 Possible causes:")
        print("   1. Gemini not following URL instruction in prompt")
        print("   2. URL format not being preserved")
        print("   3. Need to adjust planner prompt")
        print("\n📝 Check data/test_real_plans.json to see actual sources")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()