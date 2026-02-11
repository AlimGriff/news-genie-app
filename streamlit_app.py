"""
News Genie Agent - Intelligent News Aggregation and Analysis
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import logging
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """Represents a news article"""
    title: str
    description: str
    url: str
    source: str
    published_at: datetime
    category: str
    sentiment: str = "neutral"
    summary: str = ""
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "category": self.category,
            "sentiment": self.sentiment,
            "summary": self.summary,
            "keywords": self.keywords
        }

class NewsGenieAgent:
    """
    News Genie Agent for fetching, categorizing, and analyzing news
    """
    
    CATEGORIES = [
        "Business", "Technology", "Sports", "Entertainment", 
        "Health", "Science", "Politics", "General"
    ]
    
    SENTIMENT_KEYWORDS = {
        "positive": ["success", "growth", "win", "breakthrough", "achievement", 
                     "innovation", "improve", "gain", "rise", "profit"],
        "negative": ["fail", "crisis", "decline", "loss", "problem", "concern",
                     "risk", "threat", "drop", "controversy"],
        "neutral": ["report", "announce", "state", "update", "change", "develop"]
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "demo"  # Use demo key if none provided
        self.articles: List[NewsArticle] = []
        self.user_preferences = {
            "categories": [],
            "keywords": [],
            "sources": []
        }
        self.statistics = {
            "total_articles": 0,
            "by_category": defaultdict(int),
            "by_sentiment": defaultdict(int),
            "by_source": defaultdict(int)
        }
    
    def fetch_news(self, query: str = "", category: str = "", 
                   max_results: int = 20) -> List[NewsArticle]:
        """
        Fetch news from NewsAPI
        For demo purposes, returns sample data if API fails
        """
        articles = []
        
        try:
            # Try to fetch from NewsAPI
            if self.api_key and self.api_key != "demo":
                articles = self._fetch_from_api(query, category, max_results)
        except Exception as e:
            logger.warning(f"API fetch failed: {e}. Using sample data.")
        
        # If API fails or no key, use sample data
        if not articles:
            articles = self._generate_sample_news(category, max_results)
        
        # Process articles
        for article in articles:
            article.sentiment = self._analyze_sentiment(article)
            article.summary = self._generate_summary(article)
            article.keywords = self._extract_keywords(article)
            
            # Update statistics
            self.statistics["total_articles"] += 1
            self.statistics["by_category"][article.category] += 1
            self.statistics["by_sentiment"][article.sentiment] += 1
            self.statistics["by_source"][article.source] += 1
        
        self.articles.extend(articles)
        logger.info(f"Fetched {len(articles)} articles")
        return articles
    
    def _fetch_from_api(self, query: str, category: str, 
                        max_results: int) -> List[NewsArticle]:
        """Fetch news from NewsAPI.org"""
        base_url = "https://newsapi.org/v2/top-headlines"
        
        params = {
            "apiKey": self.api_key,
            "pageSize": max_results,
            "language": "en"
        }
        
        if query:
            params["q"] = query
        if category and category != "General":
            params["category"] = category.lower()
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for item in data.get("articles", []):
            if item.get("title") and item.get("title") != "[Removed]":
                article = NewsArticle(
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    url=item.get("url", ""),
                    source=item.get("source", {}).get("name", "Unknown"),
                    published_at=self._parse_date(item.get("publishedAt")),
                    category=category or "General"
                )
                articles.append(article)
        
        return articles
    
    def _generate_sample_news(self, category: str = "", 
                             count: int = 20) -> List[NewsArticle]:
        """Generate sample news articles for demo"""
        samples = [
            {
                "title": "AI Revolution: New Breakthrough in Machine Learning",
                "description": "Researchers announce major advancement in neural networks that could transform the industry.",
                "category": "Technology",
                "source": "Tech News"
            },
            {
                "title": "Stock Market Reaches New Heights Amid Economic Recovery",
                "description": "Major indices show significant gains as investors show confidence in economic outlook.",
                "category": "Business",
                "source": "Financial Times"
            },
            {
                "title": "Championship Game Ends in Dramatic Fashion",
                "description": "Thrilling finale sees underdog team clinch victory in final seconds of play.",
                "category": "Sports",
                "source": "Sports Daily"
            },
            {
                "title": "New Health Study Reveals Benefits of Mediterranean Diet",
                "description": "Long-term research confirms positive effects on heart health and longevity.",
                "category": "Health",
                "source": "Health Journal"
            },
            {
                "title": "Climate Scientists Report Concerning Trends in Global Temperatures",
                "description": "Latest data shows acceleration in warming patterns across multiple regions.",
                "category": "Science",
                "source": "Science Today"
            },
            {
                "title": "Major Policy Changes Announced by Government Officials",
                "description": "New legislation aims to address key concerns raised by citizens nationwide.",
                "category": "Politics",
                "source": "Political Review"
            },
            {
                "title": "Blockbuster Film Breaks Box Office Records",
                "description": "Latest release exceeds expectations with record-breaking opening weekend.",
                "category": "Entertainment",
                "source": "Entertainment Weekly"
            },
            {
                "title": "Tech Giant Unveils Revolutionary New Product",
                "description": "Company announces innovative device that promises to change how we interact with technology.",
                "category": "Technology",
                "source": "Tech Insider"
            },
            {
                "title": "Small Business Growth Surges in Rural Areas",
                "description": "Entrepreneurial activity shows significant increase outside major metropolitan regions.",
                "category": "Business",
                "source": "Business Week"
            },
            {
                "title": "Olympic Athletes Prepare for Upcoming Games",
                "description": "Training intensifies as competitors gear up for international competition.",
                "category": "Sports",
                "source": "Olympic News"
            }
        ]
        
        articles = []
        for i, sample in enumerate(samples * 3):  # Repeat to get enough articles
            if len(articles) >= count:
                break
            
            if category and sample["category"] != category:
                continue
            
            article = NewsArticle(
                title=f"{sample['title']} - Update #{i//len(samples) + 1}",
                description=sample["description"],
                url=f"https://example.com/article/{i}",
                source=sample["source"],
                published_at=datetime.now() - timedelta(hours=i),
                category=sample["category"]
            )
            articles.append(article)
        
        return articles[:count]
    
    def _analyze_sentiment(self, article: NewsArticle) -> str:
        """Analyze sentiment of article"""
        text = (article.title + " " + article.description).lower()
        
        scores = {
            "positive": 0,
            "negative": 0,
            "neutral": 0
        }
        
        for sentiment, keywords in self.SENTIMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    scores[sentiment] += 1
        
        if scores["positive"] > scores["negative"]:
            return "positive"
        elif scores["negative"] > scores["positive"]:
            return "negative"
        else:
            return "neutral"
    
    def _generate_summary(self, article: NewsArticle) -> str:
        """Generate a brief summary"""
        if not article.description:
            return article.title
        
        # Simple summary: first sentence of description
        sentences = article.description.split('.')
        summary = sentences[0].strip() + '.'
        
        return summary if len(summary) > 20 else article.description[:100] + "..."
    
    def _extract_keywords(self, article: NewsArticle) -> List[str]:
        """Extract keywords from article"""
        text = (article.title + " " + article.description).lower()
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                       'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was'}
        
        # Extract words
        words = re.findall(r'\b\w+\b', text)
        keywords = [w for w in words if len(w) > 4 and w not in common_words]
        
        # Return top 5 most relevant
        return list(set(keywords))[:5]
    
    def _parse_date(self, date_string: str) -> datetime:
        """Parse date string to datetime"""
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            return datetime.now()
    
    def set_user_preferences(self, categories: List[str] = None, 
                            keywords: List[str] = None,
                            sources: List[str] = None):
        """Set user preferences for personalized news"""
        if categories:
            self.user_preferences["categories"] = categories
        if keywords:
            self.user_preferences["keywords"] = keywords
        if sources:
            self.user_preferences["sources"] = sources
        
        logger.info(f"User preferences updated: {self.user_preferences}")
    
    def get_personalized_news(self, limit: int = 10) -> List[NewsArticle]:
        """Get personalized news based on user preferences"""
        filtered = self.articles
        
        # Filter by categories
        if self.user_preferences["categories"]:
            filtered = [a for a in filtered 
                       if a.category in self.user_preferences["categories"]]
        
        # Filter by keywords
        if self.user_preferences["keywords"]:
            filtered = [a for a in filtered 
                       if any(k in a.title.lower() or k in a.description.lower() 
                             for k in self.user_preferences["keywords"])]
        
        # Filter by sources
        if self.user_preferences["sources"]:
            filtered = [a for a in filtered 
                       if a.source in self.user_preferences["sources"]]
        
        # Sort by recency
        filtered.sort(key=lambda x: x.published_at, reverse=True)
        
        return filtered[:limit]
    
    def get_articles_by_category(self, category: str) -> List[NewsArticle]:
        """Get articles by category"""
        return [a for a in self.articles if a.category == category]
    
    def get_articles_by_sentiment(self, sentiment: str) -> List[NewsArticle]:
        """Get articles by sentiment"""
        return [a for a in self.articles if a.sentiment == sentiment]
    
    def search_articles(self, query: str) -> List[NewsArticle]:
        """Search articles by query"""
        query = query.lower()
        return [a for a in self.articles 
                if query in a.title.lower() or query in a.description.lower()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about fetched articles"""
        return {
            "total_articles": self.statistics["total_articles"],
            "by_category": dict(self.statistics["by_category"]),
            "by_sentiment": dict(self.statistics["by_sentiment"]),
            "by_source": dict(self.statistics["by_source"]),
            "user_preferences": self.user_preferences
        }
    
    def clear_articles(self):
        """Clear all articles"""
        self.articles.clear()
        self.statistics = {
            "total_articles": 0,
            "by_category": defaultdict(int),
            "by_sentiment": defaultdict(int),
            "by_source": defaultdict(int)
        }
        logger.info("Articles cleared")


if __name__ == "__main__":
    # Example usage
    agent = NewsGenieAgent()
    
    # Fetch news
    articles = agent.fetch_news(category="Technology", max_results=10)
    
    print(f"\nFetched {len(articles)} articles")
    print("\nFirst article:")
    print(f"Title: {articles[0].title}")
    print(f"Category: {articles[0].category}")
    print(f"Sentiment: {articles[0].sentiment}")
    print(f"Summary: {articles[0].summary}")
    
    # Get statistics
    stats = agent.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")
