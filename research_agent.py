"""
Travel Research Agent
Gathers comprehensive destination data from YouTube, Reddit, and web sources
"""

import os
import json
import yt_dlp
import requests
from datetime import datetime
from typing import List, Dict, Optional
import praw
from pathlib import Path

class ResearchAgent:
    def __init__(
        self,
        gemini_api_key: str,
        reddit_client_id: str,
        reddit_client_secret: str,
        reddit_user_agent: str
    ):
        """Initialize Research Agent with API credentials"""
        self.gemini_api_key = gemini_api_key
        self.gemini_api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent'
        self.reddit = praw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=reddit_user_agent
        )
        
        # Create directories for storing data
        Path("data/transcripts").mkdir(parents=True, exist_ok=True)
        Path("data/temp_audio").mkdir(parents=True, exist_ok=True)
    
    def research_destination(
        self,
        destination: str,
        preferences: Optional[Dict] = None,
        max_youtube_videos: int = 5,
        max_reddit_posts: int = 20
    ) -> Dict:
        """
        Main research method - orchestrates all data gathering
        
        Args:
            destination: Target destination (e.g., "Tokyo", "Paris")
            preferences: User preferences like interests, budget level
            max_youtube_videos: Number of YouTube videos to process
            max_reddit_posts: Number of Reddit posts to gather
        
        Returns:
            Complete research data dictionary
        """
        print(f"\n🔍 Starting research for {destination}...")
        
        research_data = {
            "destination": destination,
            "preferences": preferences or {},
            "research_date": datetime.now().isoformat(),
            "youtube_insights": [],
            "reddit_insights": [],
            "summary_insights": []
        }
        
        # 1. YouTube Research
        print("\n📺 Gathering YouTube insights...")
        youtube_data = self._gather_youtube_insights(
            destination, 
            max_videos=max_youtube_videos
        )
        research_data["youtube_insights"] = youtube_data
        
        # 2. Reddit Research
        print("\n🗨️  Gathering Reddit discussions...")
        reddit_data = self._gather_reddit_insights(
            destination,
            max_posts=max_reddit_posts
        )
        research_data["reddit_insights"] = reddit_data
        
        # 3. Generate summary insights
        print("\n💡 Generating summary insights...")
        research_data["summary_insights"] = self._generate_summary_insights(
            youtube_data,
            reddit_data,
            destination
        )
        
        # Save research data
        self._save_research_data(destination, research_data)
        
        print(f"\n✅ Research complete for {destination}!")
        return research_data
    
    def _gather_youtube_insights(
        self, 
        destination: str, 
        max_videos: int = 5
    ) -> List[Dict]:
        """Download, transcribe, and extract insights from YouTube videos"""
        youtube_insights = []
        
        # Search for travel guide videos
        search_query = f"{destination} travel guide 2024 2025"
        video_urls = self._search_youtube_videos(search_query, max_results=max_videos)
        
        for i, video_url in enumerate(video_urls, 1):
            print(f"  Processing video {i}/{len(video_urls)}...")
            
            try:
                # Download audio
                audio_path, metadata = self._download_youtube_audio(video_url)
                
                # Transcribe
                transcript = self._transcribe_audio(audio_path)
                
                # Clean up audio file
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                
                # Store insight
                youtube_insights.append({
                    "video_id": metadata["id"],
                    "title": metadata["title"],
                    "channel": metadata["channel"],
                    "url": video_url,  # Full URL
                    "duration_minutes": round(metadata["duration"] / 60, 1),
                    "view_count": metadata["view_count"],
                    "upload_date": metadata["upload_date"],
                    "transcript": transcript,
                    "transcript_length": len(transcript)
                })
                
                print(f"    ✓ Processed: {metadata['title'][:50]}...")
                
            except Exception as e:
                print(f"    ✗ Error processing video: {str(e)}")
                continue
        
        return youtube_insights
    
    def _search_youtube_videos(self, query: str, max_results: int = 5) -> List[str]:
        """
        Search for YouTube videos and return URLs
        Note: This is a simplified version. In production, use YouTube Data API
        """
        # For prototype, return example URLs or use yt-dlp search
        # In production, integrate with YouTube Data API
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            video_urls = [
                f"https://www.youtube.com/watch?v={entry['id']}" 
                for entry in search_results['entries']
            ]
        
        return video_urls
    
    def _download_youtube_audio(self, video_url: str) -> tuple:
        """Download audio from YouTube video"""
        output_path = "data/temp_audio"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{output_path}/%(id)s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_file = f"{output_path}/{info['id']}.mp3"
            
            metadata = {
                'id': info['id'],
                'title': info['title'],
                'channel': info.get('uploader', 'Unknown'),
                'duration': info['duration'],
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', 'Unknown')
            }
        
        return audio_file, metadata
    
    def _transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio using Gemini API
        Note: Gemini doesn't have native audio transcription yet.
        You'll need to use Google Cloud Speech-to-Text or Whisper locally.
        For now, we'll use a placeholder that you can replace.
        """
        # Option 1: Use local Whisper (recommended)
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_file_path)
            return result["text"]
        except ImportError:
            print("Whisper not installed. Install with: pip install openai-whisper")
            return "[Transcription unavailable - install Whisper]"
        
        # Option 2: Use Google Cloud Speech-to-Text (if you have it)
        # from google.cloud import speech_v1
        # client = speech_v1.SpeechClient()
        # ... implement speech-to-text here
    
    def _gather_reddit_insights(
        self, 
        destination: str, 
        max_posts: int = 20
    ) -> List[Dict]:
        """Gather insights from Reddit travel communities"""
        reddit_insights = []
        
        # Target subreddits
        subreddits = ['travel', 'solotravel', 'TravelHacks']
        
        # Try destination-specific subreddit (e.g., r/Tokyo, r/Paris)
        destination_sub = destination.replace(" ", "")
        subreddits.append(destination_sub)
        
        for sub_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                
                # Search for destination-related posts
                for post in subreddit.search(
                    destination, 
                    limit=max_posts // len(subreddits),
                    sort='top',
                    time_filter='year'
                ):
                    # Get top comments
                    post.comments.replace_more(limit=0)
                    top_comments = []
                    
                    for comment in post.comments.list()[:10]:
                        if hasattr(comment, 'body') and comment.score > 3:
                            top_comments.append({
                                'text': comment.body,
                                'score': comment.score
                            })
                    
                    reddit_insights.append({
                        'subreddit': sub_name,
                        'title': post.title,
                        'text': post.selftext,
                        'score': post.score,
                        'url': f"https://reddit.com{post.permalink}",
                        'num_comments': post.num_comments,
                        'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                        'top_comments': top_comments
                    })
                
                print(f"  ✓ Gathered insights from r/{sub_name}")
                
            except Exception as e:
                print(f"  ✗ Error accessing r/{sub_name}: {str(e)}")
                continue
        
        # Sort by score
        reddit_insights.sort(key=lambda x: x['score'], reverse=True)
        
        return reddit_insights[:max_posts]
    
    def _generate_summary_insights(
        self,
        youtube_data: List[Dict],
        reddit_data: List[Dict],
        destination: str
    ) -> List[str]:
        """
        Use Gemini LLM to generate high-level insights from all research data
        """
        # Prepare condensed data for LLM
        youtube_summaries = [
            f"Video: {video['title']}\nKey points from transcript: {video['transcript'][:500]}..."
            for video in youtube_data[:3]  # Top 3 videos
        ]
        
        reddit_summaries = [
            f"Reddit post ({post['score']} upvotes): {post['title']}\n{post['text'][:300]}"
            for post in reddit_data[:5]  # Top 5 posts
        ]
        
        prompt = f"""Based on the following research about {destination}, extract 8-10 key insights that would help someone plan a trip:

YouTube Travel Guides:
{chr(10).join(youtube_summaries)}

Reddit Discussions:
{chr(10).join(reddit_summaries)}

Provide insights in these categories:
1. Must-see attractions
2. Hidden gems / local favorites
3. Food recommendations
4. Transportation tips
5. Budget considerations
6. Things to avoid
7. Best times to visit
8. Cultural tips

Format each insight as a concise bullet point."""

        # Call Gemini API
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
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
            insights_text = result['candidates'][0]['content']['parts'][0]['text']
            insights = [line.strip() for line in insights_text.split('\n') if line.strip()]
            
            return insights
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return ["Error generating insights - check API key and connection"]
    
    def _save_research_data(self, destination: str, research_data: Dict):
        """Save research data to JSON file"""
        filename = f"data/research_{destination.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(research_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Research data saved to: {filename}")


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = ResearchAgent(
        gemini_api_key="your-gemini-api-key",
        reddit_client_id="your-reddit-client-id",
        reddit_client_secret="your-reddit-secret",
        reddit_user_agent="TravelPlannerBot/1.0"
    )
    
    # Research a destination
    research_data = agent.research_destination(
        destination="Tokyo",
        preferences={
            "interests": ["food", "culture", "photography"],
            "budget_level": "mid-range"
        },
        max_youtube_videos=3,  # Start small for testing
        max_reddit_posts=10
    )
    
    print(f"\n📊 Research Summary:")
    print(f"  YouTube videos processed: {len(research_data['youtube_insights'])}")
    print(f"  Reddit posts gathered: {len(research_data['reddit_insights'])}")
    print(f"  Key insights generated: {len(research_data['summary_insights'])}")