"""
View the complete test plans in a beautiful format
Run this after test_complete_workflow.py to see all details
"""

import json
import os
from datetime import datetime

def print_header(text, char="="):
    """Print a formatted header"""
    width = 70
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")

def print_plan_summary(plan_data):
    """Print a comprehensive summary of a single plan"""
    
    print_header(f"📋 {plan_data['plan_name'].upper()}", "━")
    
    # Basic info
    print(f"🆔 Plan ID: {plan_data['plan_id']}")
    print(f"💰 Total Cost: ${plan_data['total_cost']:,.2f}")
    print(f"🎨 Theme: {plan_data['theme']}")
    print(f"⚡ Pace: {plan_data['pace']}")
    print(f"📅 Duration: {len(plan_data['daily_plans'])} days")
    
    # Cost breakdown with percentages
    total = plan_data['total_cost']
    activities = plan_data.get('cost_breakdown', {}).get('activities', 0)
    accommodation = plan_data.get('cost_breakdown', {}).get('accommodation', 0)
    transportation = plan_data.get('cost_breakdown', {}).get('transportation', 0)
    
    print(f"\n💵 Cost Breakdown:")
    print(f"   Activities:      ${activities:>8,.2f}  ({activities/total*100:>5.1f}%)")
    print(f"   Accommodation:   ${accommodation:>8,.2f}  ({accommodation/total*100:>5.1f}%)")
    print(f"   Transportation:  ${transportation:>8,.2f}  ({transportation/total*100:>5.1f}%)")
    print(f"   {'─'*50}")
    print(f"   TOTAL:           ${total:>8,.2f}  (100.0%)")
    
    # Accommodation
    acc = plan_data['accommodation']
    print(f"\n🏨 Accommodation:")
    print(f"   Name: {acc.get('name', 'N/A')}")
    print(f"   Type: {acc.get('type', 'N/A')}")
    print(f"   Location: {acc.get('location', 'N/A')}")
    print(f"   Rate: ${acc.get('cost_per_night', 0):.2f} per night")
    print(f"   Nights: {acc.get('total_nights', 0)}")
    print(f"   Total: ${acc.get('cost_per_night', 0) * acc.get('total_nights', 0):.2f}")
    
    # Transportation
    trans = plan_data['transportation']
    print(f"\n🚇 Transportation:")
    print(f"   Arrival: {trans.get('arrival', 'N/A')}")
    print(f"   Daily Transport: {trans.get('daily', 'N/A')}")
    print(f"   Daily Cost: ${trans.get('estimated_daily_cost', 0):.2f}")
    
    # Key highlights
    print(f"\n🌟 Trip Highlights:")
    for i, highlight in enumerate(plan_data.get('key_highlights', []), 1):
        print(f"   {i}. {highlight}")
    
    # Daily itinerary
    print(f"\n📅 COMPLETE ITINERARY:")
    print("─" * 70)
    
    for day in plan_data['daily_plans']:
        print(f"\n{'='*70}")
        print(f"📆 DAY {day['day_number']}: {day['theme'].upper()}")
        print(f"{'='*70}")
        print(f"Date: {day['date']}")
        print(f"Daily Budget: ${day['total_cost']:.2f}")
        
        if day['activities']:
            print(f"\n🎯 Activities ({len(day['activities'])} planned):")
            
            total_duration = sum(act['duration_hours'] for act in day['activities'])
            print(f"Total active time: {total_duration:.1f} hours")
            
            for i, activity in enumerate(day['activities'], 1):
                print(f"\n{'─'*70}")
                print(f"{i}. {activity['time']} - {activity['name']}")
                print(f"{'─'*70}")
                print(f"   📍 Location: {activity['location']}")
                print(f"   📝 Description: {activity['description']}")
                print(f"   💰 Cost: ${activity['estimated_cost']:.2f}")
                print(f"   ⏱️  Duration: {activity['duration_hours']} hours")
                print(f"   🏷️  Category: {activity['category']}")
                if activity.get('source'):
                    source = activity['source']
                    print(f"   📚 Inspired by: {source}")
                    # If URL is in source, highlight it
                    if 'http' in source:
                        # Try to extract just the URL
                        if ' - http' in source:
                            parts = source.split(' - http')
                            url = 'http' + parts[1] if len(parts) > 1 else source
                            print(f"   🔗 Link: {url}")
                        elif 'https://' in source:
                            import re
                            urls = re.findall(r'https://[^\s]+', source)
                            if urls:
                                print(f"   🔗 Link: {urls[0]}")
        
        if day.get('notes'):
            print(f"\n📝 Daily Notes:")
            print(f"   {day['notes']}")
        
        print(f"\n{'─'*70}\n")
    
    print("━" * 70 + "\n")

def compare_plans(plans_data):
    """Create a comparison table of all plans"""
    
    print_header("📊 PLAN COMPARISON", "=")
    
    print(f"{'Metric':<30} {'Plan A':<20} {'Plan B':<20} {'Plan C':<20}")
    print("─" * 95)
    
    # Extract data for comparison
    plan_a = plans_data[0]
    plan_b = plans_data[1]
    plan_c = plans_data[2]
    
    # Compare costs
    print(f"{'Total Cost':<30} ${plan_a['total_cost']:<18,.2f} ${plan_b['total_cost']:<18,.2f} ${plan_c['total_cost']:<18,.2f}")
    
    # Compare themes
    print(f"{'Theme':<30} {plan_a['theme']:<20} {plan_b['theme']:<20} {plan_c['theme']:<20}")
    
    # Compare pace
    print(f"{'Pace':<30} {plan_a['pace']:<20} {plan_b['pace']:<20} {plan_c['pace']:<20}")
    
    # Compare accommodation
    print(f"{'Accommodation Type':<30} {plan_a['accommodation']['type']:<20} {plan_b['accommodation']['type']:<20} {plan_c['accommodation']['type']:<20}")
    
    acc_a = plan_a['accommodation']['cost_per_night']
    acc_b = plan_b['accommodation']['cost_per_night']
    acc_c = plan_c['accommodation']['cost_per_night']
    print(f"{'Accommodation per Night':<30} ${acc_a:<18.2f} ${acc_b:<18.2f} ${acc_c:<18.2f}")
    
    # Compare activities per day
    activities_a = sum(len(day['activities']) for day in plan_a['daily_plans'])
    activities_b = sum(len(day['activities']) for day in plan_b['daily_plans'])
    activities_c = sum(len(day['activities']) for day in plan_c['daily_plans'])
    
    print(f"{'Total Activities':<30} {activities_a:<20} {activities_b:<20} {activities_c:<20}")
    print(f"{'Avg per Day':<30} {activities_a/len(plan_a['daily_plans']):<20.1f} {activities_b/len(plan_b['daily_plans']):<20.1f} {activities_c/len(plan_c['daily_plans']):<20.1f}")
    
    print("─" * 95 + "\n")

def main():
    """Main function to display test plans"""
    
    print("="*70)
    print("🗺️  TRAVEL PLANNER - TEST PLANS VIEWER".center(70))
    print("="*70)
    
    # Load plans
    plans_file = 'data/test_plans_output.json'
    
    if not os.path.exists(plans_file):
        print(f"\n❌ Plans file not found: {plans_file}")
        print("\n💡 Run this first:")
        print("   python test_complete_workflow.py")
        print("\n   This will generate the plans file, then run this script again.")
        return
    
    print(f"\n📂 Loading plans from: {plans_file}")
    
    with open(plans_file, 'r', encoding='utf-8') as f:
        plans_data = json.load(f)
    
    print(f"✅ Loaded {len(plans_data)} plans\n")
    
    # Menu
    while True:
        print("─" * 70)
        print("What would you like to view?")
        print("─" * 70)
        print("1. View Plan A (Budget Explorer)")
        print("2. View Plan B (Balanced Adventure)")
        print("3. View Plan C (Premium Experience)")
        print("4. Compare All Plans")
        print("5. View All Plans (Complete)")
        print("6. Exit")
        print("─" * 70)
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            print_plan_summary(plans_data[0])
        elif choice == '2':
            print_plan_summary(plans_data[1])
        elif choice == '3':
            print_plan_summary(plans_data[2])
        elif choice == '4':
            compare_plans(plans_data)
        elif choice == '5':
            for plan in plans_data:
                print_plan_summary(plan)
        elif choice == '6':
            print("\n👋 Goodbye! Happy trip planning!\n")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-6.\n")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()