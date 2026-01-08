"""
Cyber Threat News Intelligence
Fetches and correlates live cybersecurity news with analysis
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class CyberNewsIntelligence:
    def __init__(self):
        self.api_key = os.environ.get('NEWS_API_KEY')
        self.base_url = 'https://newsapi.org/v2/everything'
        
        # Cybersecurity keywords for filtering
        self.keywords = [
            'cybersecurity', 'data breach', 'phishing', 'malware',
            'ransomware', 'zero-day', 'vulnerability', 'exploit',
            'hacking', 'cyber attack', 'security breach', 'threat actor'
        ]
    
    def fetch_recent_threats(self, days_back: int = 7, max_results: int = 20) -> List[Dict]:
        """
        Fetch recent cybersecurity news
        """
        if not self.api_key:
            return []
        
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            params = {
                'q': 'cybersecurity OR "data breach" OR phishing OR malware OR ransomware',
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': max_results,
                'apiKey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                return [
                    {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'impact_level': self._assess_impact(article)
                    }
                    for article in articles
                ]
            else:
                return []
                
        except Exception as e:
            print(f"News fetch error: {e}")
            return []
    
    def _assess_impact(self, article: Dict) -> str:
        """
        Assess impact level based on article content
        Uses calm, analytical language
        """
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = f"{title} {description}"
        
        # High impact indicators
        high_impact_terms = [
            'zero-day', 'critical vulnerability', 'widespread',
            'major breach', 'millions affected', 'ransomware attack',
            'supply chain', 'nation-state'
        ]
        
        # Medium impact indicators
        medium_impact_terms = [
            'vulnerability', 'exploit', 'breach', 'malware',
            'phishing campaign', 'security flaw'
        ]
        
        if any(term in content for term in high_impact_terms):
            return 'significant'
        elif any(term in content for term in medium_impact_terms):
            return 'moderate'
        else:
            return 'informational'
    
    def correlate_with_analysis(self, analysis_input: str, news_items: List[Dict]) -> Optional[Dict]:
        """
        Check if current analysis relates to recent news
        """
        input_lower = analysis_input.lower()
        
        for item in news_items:
            title_lower = item['title'].lower()
            desc_lower = item.get('description', '').lower()
            
            # Extract domains/keywords from news
            # Simple correlation - can be enhanced with NLP
            if any(word in input_lower for word in title_lower.split() if len(word) > 5):
                return {
                    'related': True,
                    'article': item,
                    'context': f"This may relate to a recent threat: {item['title']}"
                }
        
        return None
    
    def get_threat_summary(self, news_items: List[Dict]) -> Dict:
        """
        Generate summary of current threat landscape
        """
        if not news_items:
            return {
                'total_threats': 0,
                'significant': 0,
                'moderate': 0,
                'informational': 0,
                'summary': 'No recent threat intelligence available'
            }
        
        impact_counts = {
            'significant': 0,
            'moderate': 0,
            'informational': 0
        }
        
        for item in news_items:
            impact = item.get('impact_level', 'informational')
            impact_counts[impact] = impact_counts.get(impact, 0) + 1
        
        summary_parts = []
        if impact_counts['significant'] > 0:
            summary_parts.append(f"{impact_counts['significant']} significant threats")
        if impact_counts['moderate'] > 0:
            summary_parts.append(f"{impact_counts['moderate']} moderate threats")
        
        summary = ', '.join(summary_parts) if summary_parts else 'Routine threat activity'
        
        return {
            'total_threats': len(news_items),
            'significant': impact_counts['significant'],
            'moderate': impact_counts['moderate'],
            'informational': impact_counts['informational'],
            'summary': summary
        }
