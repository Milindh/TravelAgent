"""
Verify that source links are being included in generated plans
Run this after test_complete_workflow.py to check URL inclusion
"""

import json
import os
import re

def extract_urls(text):
    """Extract all URLs from text"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)

def analyze_plan_sources(plan):
    """Analyze sources in a single plan"""
    stats = {
        'total_activities': 0,
        'activities_with_sources': 0,
        'sources_with_urls': 0,
        'youtube_urls': [],
        'reddit_urls': [],
        'other_urls': []
    }
    
    for day in plan.get('daily_plans', []):
        for activity in day.get('activities', []):
            stats['total_activities'] += 1
            
            source = activity.get('source', '')
            if source:
                stats['activities_with_sources'] += 1
                
                # Extract URLs
                urls = extract_urls(source)
                if urls:
                    stats['sources_with_urls'] += 1
                    
                    for url in urls:
                        if 'youtube.com' in url or 'youtu.be' in url:
                            stats['youtube_urls'].append(url)
                        elif 'reddit.com' in url:
                            stats['reddit_urls'].append(url)
                        else:
                            stats['other_urls'].append(url)
    
    return stats

def main():
    """Main verification function"""
    
    print("="*70)
    print("🔍 SOURCE LINKS VERIFICATION".center(70))
    print("="*70)
    
    # Check if plans file exists
    plans_file = 'data/test_plans_output.json'
    
    if not os.path.exists(plans_file):
        print(f"\n❌ Plans file not found: {plans_file}")
        print("\n💡 Run this first:")
        print("   python test_complete_workflow.py")
        return
    
    print(f"\n📂 Loading plans from: {plans_file}")
    
    with open(plans_file, 'r', encoding='utf-8') as f:
        plans = json.load(f)
    
    print(f"✅ Loaded {len(plans)} plans\n")
    
    # Analyze each plan
    all_stats = []
    
    for i, plan in enumerate(plans, 1):
        plan_name = plan.get('plan_name', f'Plan {i}')
        print("─"*70)
        print(f"📋 {plan_name}")
        print("─"*70)
        
        stats = analyze_plan_sources(plan)
        all_stats.append(stats)
        
        # Display stats
        print(f"Total Activities: {stats['total_activities']}")
        print(f"Activities with Sources: {stats['activities_with_sources']} ({stats['activities_with_sources']/stats['total_activities']*100:.1f}%)")
        print(f"Sources with URLs: {stats['sources_with_urls']} ({stats['sources_with_urls']/max(stats['activities_with_sources'], 1)*100:.1f}%)")
        
        print(f"\n🔗 URL Breakdown:")
        print(f"   YouTube URLs: {len(stats['youtube_urls'])}")
        print(f"   Reddit URLs: {len(stats['reddit_urls'])}")
        print(f"   Other URLs: {len(stats['other_urls'])}")
        
        # Show sample URLs
        if stats['youtube_urls']:
            print(f"\n📺 Sample YouTube URLs:")
            for url in stats['youtube_urls'][:2]:
                print(f"   • {url}")
        
        if stats['reddit_urls']:
            print(f"\n🗨️  Sample Reddit URLs:")
            for url in stats['reddit_urls'][:2]:
                print(f"   • {url}")
        
        print()
    
    # Overall summary
    print("="*70)
    print("📊 OVERALL SUMMARY")
    print("="*70)
    
    total_activities = sum(s['total_activities'] for s in all_stats)
    total_with_sources = sum(s['activities_with_sources'] for s in all_stats)
    total_with_urls = sum(s['sources_with_urls'] for s in all_stats)
    total_youtube = sum(len(s['youtube_urls']) for s in all_stats)
    total_reddit = sum(len(s['reddit_urls']) for s in all_stats)
    
    print(f"\nAcross all {len(plans)} plans:")
    print(f"  Total Activities: {total_activities}")
    print(f"  With Source Attribution: {total_with_sources} ({total_with_sources/total_activities*100:.1f}%)")
    print(f"  With URLs: {total_with_urls} ({total_with_urls/max(total_with_sources, 1)*100:.1f}%)")
    print(f"\n  YouTube Links: {total_youtube}")
    print(f"  Reddit Links: {total_reddit}")
    print(f"  Total Links: {total_youtube + total_reddit}")
    
    # Recommendations
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)
    
    if total_with_urls == 0:
        print("\n⚠️  NO URLs FOUND!")
        print("\nPossible issues:")
        print("  1. Research Agent not capturing URLs")
        print("  2. Planner Agent not including URLs in sources")
        print("  3. Mock data being used (test data)")
        print("\nSolutions:")
        print("  • Check that research_agent.py saves 'url' field")
        print("  • Verify planner_agent.py prompt includes URL instruction")
        print("  • Run with real data instead of mock data")
    
    elif total_with_urls < total_with_sources * 0.5:
        print("\n⚠️  Low URL coverage!")
        print(f"  Only {total_with_urls}/{total_with_sources} sources have URLs")
        print("\nThis might be because:")
        print("  • Some sources don't have URLs (like 'N/A')")
        print("  • Gemini didn't include URLs in all sources")
        print("\nTip: Check the planner agent prompt to ensure URLs are required")
    
    else:
        print("\n✅ Good URL coverage!")
        print(f"  {total_with_urls}/{total_with_sources} sources include URLs")
        print("\nYour plans have proper source attribution with links!")
        print("Users can click through to verify recommendations.")
    
    # Check for common issues
    print("\n" + "─"*70)
    print("🔧 QUALITY CHECKS")
    print("─"*70)
    
    issues_found = []
    
    # Check if any URLs are just placeholders
    for plan in plans:
        for day in plan.get('daily_plans', []):
            for activity in day.get('activities', []):
                source = activity.get('source', '')
                if 'example' in source.lower() or 'test' in source.lower():
                    issues_found.append(f"Placeholder URL in: {activity.get('name', 'Unknown')}")
    
    if issues_found:
        print("\n⚠️  Found potential placeholder URLs:")
        for issue in issues_found[:5]:
            print(f"   • {issue}")
        if len(issues_found) > 5:
            print(f"   ... and {len(issues_found) - 5} more")
        print("\n💡 This is normal for test data. Real runs will have actual URLs.")
    else:
        print("\n✅ No placeholder URLs detected")
        print("   All URLs appear to be real sources!")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()