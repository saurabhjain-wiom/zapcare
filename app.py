import os
import tweepy
import requests
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# AI evangelists: username -> display name
AI_EVANGELISTS = {
    "karpathy": "Andrej Karpathy",
    "elonmusk": "Elon Musk",
    "sama": "Sam Altman",
    "ylecun": "Yann LeCun",
    "demishassabis": "Demis Hassabis",
    "ilyasut": "Ilya Sutskever",
    "gdb": "Greg Brockman",
    "fchollet": "Francois Chollet",
    "drfeifei": "Fei-Fei Li",
    "emollick": "Ethan Mollick",
}


def get_ai_tweets():
    """Fetch recent AI-related tweets from evangelists using Twitter API v2."""
    if not TWITTER_BEARER_TOKEN or TWITTER_BEARER_TOKEN == "your_twitter_bearer_token_here":
        return _mock_tweets()

    try:
        client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=False)
        tweets_data = []

        for username, display_name in AI_EVANGELISTS.items():
            try:
                user = client.get_user(username=username, user_fields=["profile_image_url"])
                if not user.data:
                    continue

                response = client.get_users_tweets(
                    id=user.data.id,
                    max_results=5,
                    tweet_fields=["created_at", "public_metrics", "text"],
                    exclude=["retweets", "replies"],
                )
                if not response.data:
                    continue

                profile_img = getattr(user.data, "profile_image_url", None) or ""

                for tweet in response.data:
                    # Filter for AI-related tweets
                    text_lower = tweet.text.lower()
                    ai_keywords = ["ai", "llm", "gpt", "model", "neural", "machine learning",
                                   "deep learning", "agent", "openai", "anthropic", "gemini",
                                   "training", "inference", "transformer", "gpu", "intelligence"]
                    if not any(kw in text_lower for kw in ai_keywords):
                        continue

                    metrics = tweet.public_metrics or {}
                    tweets_data.append({
                        "id": str(tweet.id),
                        "author": display_name,
                        "username": username,
                        "text": tweet.text,
                        "created_at": tweet.created_at.strftime("%b %d, %Y %H:%M UTC") if tweet.created_at else "",
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "profile_image": profile_img.replace("_normal", "_bigger"),
                        "url": f"https://twitter.com/{username}/status/{tweet.id}",
                    })
            except Exception:
                continue

        # Sort by likes descending
        tweets_data.sort(key=lambda x: x["likes"], reverse=True)
        return tweets_data[:20]

    except Exception as e:
        return {"error": str(e), "tweets": _mock_tweets()}


def _mock_tweets():
    """Return mock tweet data when API keys are not configured."""
    return [
        {
            "id": "mock1",
            "author": "Andrej Karpathy",
            "username": "karpathy",
            "text": "LLMs are getting remarkably good at reasoning. The progress in the last 6 months has been incredible. We're entering a new era of AI capabilities. #AI #LLM",
            "created_at": "Mar 17, 2026 10:00 UTC",
            "likes": 15200,
            "retweets": 2100,
            "profile_image": "",
            "url": "https://twitter.com/karpathy",
        },
        {
            "id": "mock2",
            "author": "Sam Altman",
            "username": "sama",
            "text": "AGI is closer than most people think. The scaling laws continue to hold. Very excited about what we're building at OpenAI. The next few years will be transformative.",
            "created_at": "Mar 17, 2026 08:30 UTC",
            "likes": 32100,
            "retweets": 5400,
            "profile_image": "",
            "url": "https://twitter.com/sama",
        },
        {
            "id": "mock3",
            "author": "Elon Musk",
            "username": "elonmusk",
            "text": "Grok 3 is the most powerful AI model in the world right now. The progress at xAI has been extraordinary. AI will fundamentally change every industry.",
            "created_at": "Mar 17, 2026 06:15 UTC",
            "likes": 89000,
            "retweets": 12000,
            "profile_image": "",
            "url": "https://twitter.com/elonmusk",
        },
        {
            "id": "mock4",
            "author": "Yann LeCun",
            "username": "ylecun",
            "text": "LLMs are not the path to AGI. We need world models and self-supervised learning that truly understands physical reality. The current paradigm has fundamental limitations.",
            "created_at": "Mar 16, 2026 22:00 UTC",
            "likes": 8700,
            "retweets": 1200,
            "profile_image": "",
            "url": "https://twitter.com/ylecun",
        },
        {
            "id": "mock5",
            "author": "Francois Chollet",
            "username": "fchollet",
            "text": "The ARC-AGI benchmark results are in. Current models still struggle with novel reasoning tasks that humans find trivial. True general intelligence remains elusive.",
            "created_at": "Mar 16, 2026 18:45 UTC",
            "likes": 5300,
            "retweets": 890,
            "profile_image": "",
            "url": "https://twitter.com/fchollet",
        },
        {
            "id": "mock6",
            "author": "Demis Hassabis",
            "username": "demishassabis",
            "text": "AlphaFold 3 has now predicted structures for virtually every known protein. This is accelerating drug discovery at an unprecedented pace. AI for science is just beginning.",
            "created_at": "Mar 16, 2026 15:30 UTC",
            "likes": 21000,
            "retweets": 3800,
            "profile_image": "",
            "url": "https://twitter.com/demishassabis",
        },
    ]


def get_news(country=None, category=None, query=None, page_size=10):
    """Fetch top news from NewsAPI."""
    if not NEWS_API_KEY or NEWS_API_KEY == "your_newsapi_key_here":
        return _mock_news(country, category)

    try:
        if query:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "language": "en",
                "apiKey": NEWS_API_KEY,
            }
        else:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "pageSize": page_size,
                "apiKey": NEWS_API_KEY,
            }
            if country:
                params["country"] = country
            if category:
                params["category"] = category

        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for a in data.get("articles", []):
            articles.append({
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "source": a.get("source", {}).get("name", ""),
                "url": a.get("url", ""),
                "published_at": _format_date(a.get("publishedAt", "")),
                "image": a.get("urlToImage", ""),
            })
        return articles

    except Exception as e:
        return _mock_news(country, category)


def _format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M UTC")
    except Exception:
        return iso_str


def _mock_news(country=None, category=None):
    world_news = [
        {"title": "US-China Trade Talks Resume in Geneva", "description": "High-level delegations from the US and China met in Geneva for a new round of trade negotiations amid ongoing tariff disputes.", "source": "Reuters", "url": "#", "published_at": "Mar 17, 2026 09:00 UTC", "image": ""},
        {"title": "Ukraine Peace Talks: New Proposal on the Table", "description": "A coalition of European nations has put forward a revised ceasefire proposal for the Russia-Ukraine conflict.", "source": "BBC News", "url": "#", "published_at": "Mar 17, 2026 08:00 UTC", "image": ""},
        {"title": "Global Carbon Emissions Hit Record Low in 2025", "description": "The IEA reports that renewable energy adoption pushed global emissions to their lowest level in 20 years.", "source": "The Guardian", "url": "#", "published_at": "Mar 17, 2026 07:30 UTC", "image": ""},
        {"title": "FIFA World Cup 2026: Venues Confirmed", "description": "FIFA announced all 16 host cities for the 2026 World Cup across the USA, Canada, and Mexico.", "source": "ESPN", "url": "#", "published_at": "Mar 17, 2026 06:00 UTC", "image": ""},
        {"title": "Scientists Discover New Exoplanet in Habitable Zone", "description": "NASA's James Webb telescope identified a rocky exoplanet with potential liquid water 40 light-years away.", "source": "Science Daily", "url": "#", "published_at": "Mar 16, 2026 22:00 UTC", "image": ""},
        {"title": "WHO Declares End of Latest Mpox Outbreak", "description": "The World Health Organization confirmed the end of the latest mpox outbreak after 3 months of containment.", "source": "WHO", "url": "#", "published_at": "Mar 16, 2026 20:00 UTC", "image": ""},
        {"title": "Global Markets Rally on Fed Rate Cut Signals", "description": "Stock markets worldwide surged after the Federal Reserve hinted at potential rate cuts in Q2 2026.", "source": "Financial Times", "url": "#", "published_at": "Mar 16, 2026 18:00 UTC", "image": ""},
        {"title": "Real Madrid Win Champions League 2026", "description": "Real Madrid clinched their 16th Champions League title with a 2-1 win over Manchester City in the final.", "source": "UEFA", "url": "#", "published_at": "Mar 16, 2026 23:30 UTC", "image": ""},
        {"title": "OpenAI Launches GPT-5 to General Public", "description": "OpenAI released GPT-5 with major improvements in reasoning, multimodal capabilities, and reduced hallucinations.", "source": "TechCrunch", "url": "#", "published_at": "Mar 16, 2026 16:00 UTC", "image": ""},
        {"title": "SpaceX Starship Completes First Mars Mission Simulation", "description": "SpaceX successfully completed a 500-day Mars mission simulation in Earth orbit, a milestone for future crewed missions.", "source": "Space.com", "url": "#", "published_at": "Mar 16, 2026 14:00 UTC", "image": ""},
    ]

    india_news = [
        {"title": "India's GDP Growth Forecast Raised to 7.8% for FY2026", "description": "The IMF revised India's GDP growth forecast upward citing strong domestic consumption and manufacturing expansion.", "source": "Economic Times", "url": "#", "published_at": "Mar 17, 2026 09:30 UTC", "image": ""},
        {"title": "PM Modi Inaugurates New High-Speed Rail Corridor", "description": "Prime Minister inaugurated the Mumbai-Pune bullet train corridor, India's second high-speed rail line.", "source": "NDTV", "url": "#", "published_at": "Mar 17, 2026 08:00 UTC", "image": ""},
        {"title": "India vs Australia: Virat Kohli Scores Milestone Century", "description": "Virat Kohli scored his 55th Test century as India dominated the 3rd Test match against Australia in Sydney.", "source": "ESPNcricinfo", "url": "#", "published_at": "Mar 17, 2026 07:00 UTC", "image": ""},
        {"title": "Lok Sabha Passes New Digital India Act 2026", "description": "Parliament approved the landmark Digital India Act bringing major reforms to data privacy and AI regulation.", "source": "The Hindu", "url": "#", "published_at": "Mar 16, 2026 21:00 UTC", "image": ""},
        {"title": "ISRO Successfully Launches Chandrayaan-4", "description": "India's Chandrayaan-4 mission launches successfully from Sriharikota, targeting the Moon's south pole for sample return.", "source": "Times of India", "url": "#", "published_at": "Mar 16, 2026 18:00 UTC", "image": ""},
        {"title": "Indian Premier League 2026 Season Kicks Off in Mumbai", "description": "IPL 2026 begins with defending champions Mumbai Indians hosting Chennai Super Kings at Wankhede Stadium.", "source": "Cricbuzz", "url": "#", "published_at": "Mar 16, 2026 15:00 UTC", "image": ""},
        {"title": "India-Pakistan Diplomatic Talks Resume After 3 Years", "description": "Foreign ministers of India and Pakistan held their first bilateral meeting in three years in Dubai.", "source": "Hindustan Times", "url": "#", "published_at": "Mar 16, 2026 12:00 UTC", "image": ""},
        {"title": "Bengaluru Ranked Asia's Top Tech Hub 2026", "description": "Bengaluru surpassed Singapore and Tokyo to be named Asia's leading technology and startup hub.", "source": "Business Standard", "url": "#", "published_at": "Mar 16, 2026 10:00 UTC", "image": ""},
        {"title": "India Achieves 100% Renewable Energy Target in 5 States", "description": "Five Indian states now run entirely on renewable energy, ahead of the 2030 national target.", "source": "Down To Earth", "url": "#", "published_at": "Mar 15, 2026 22:00 UTC", "image": ""},
        {"title": "Neeraj Chopra Breaks World Record at Diamond League", "description": "Olympic champion Neeraj Chopra set a new javelin world record of 91.5m at the Doha Diamond League meet.", "source": "Sports Tak", "url": "#", "published_at": "Mar 15, 2026 20:00 UTC", "image": ""},
    ]

    if country == "in":
        return india_news
    return world_news


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tweets")
def api_tweets():
    tweets = get_ai_tweets()
    if isinstance(tweets, dict) and "error" in tweets:
        return jsonify({"tweets": tweets.get("tweets", []), "error": tweets["error"]})
    return jsonify({"tweets": tweets})


@app.route("/api/news/world")
def api_news_world():
    articles = get_news(country="us", page_size=10)
    return jsonify({"articles": articles})


@app.route("/api/news/india")
def api_news_india():
    articles = get_news(country="in", page_size=10)
    return jsonify({"articles": articles})


@app.route("/api/all")
def api_all():
    tweets = get_ai_tweets()
    world = get_news(country="us", page_size=10)
    india = get_news(country="in", page_size=10)

    if isinstance(tweets, dict) and "error" in tweets:
        tweets = tweets.get("tweets", [])

    return jsonify({
        "tweets": tweets,
        "world_news": world,
        "india_news": india,
        "last_updated": datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M UTC"),
    })


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
