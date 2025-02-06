from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
import os
from collections import defaultdict
from functools import wraps
import hashlib
import time

from app.services.analyzer import SubmissionAnalyzer
from app.services.codeforces import CodeforcesService
from app.config import Config

# Initialize Flask app with static folder configuration
app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Initialize cache properly
cache = Cache(config={
    'CACHE_TYPE': Config.CACHE_TYPE,
    'CACHE_DEFAULT_TIMEOUT': Config.CACHE_DEFAULT_TIMEOUT
})
cache.init_app(app)

# Serve static files through Flask routes
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Configure rate limiting for Vercel
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.RATELIMIT_DEFAULT],
    storage_uri=Config.RATELIMIT_STORAGE_URL
)

# CORS headers for Vercel
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Security middleware
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net; style-src 'self' fonts.googleapis.com 'unsafe-inline'; img-src 'self' data: https:;"
    return response

app.after_request(security_headers)

# Configure Google Gemini AI
genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_roadmap(user_data, topics):
    prompt = f"""
    You are a seasoned programming mentor. Using the following user data:
    
    - Current Rating: {user_data.get('rating', 'Unrated')}
    - Max Rating: {user_data.get('maxRating', 'N/A')}
    
    And the user's performance across various topics:
    {topics}
    
    Generate a detailed, personalized study plan that will help the user improve their programming skills.
    Your study plan should include:
    1. A clear set of learning objectives.
    2. A step-by-step roadmap with specific programming challenges and topics to focus on.
    3. Recommended online resources (courses, tutorials, articles) for each step.
    4. Practical tips to overcome common difficulties in competitive programming.
    5. A motivational closing message to inspire continued improvement.
    
    Present your response with clear formatting, using numbered steps and bullet points where appropriate.
    """
    try:
        response = model.generate_content(prompt)
        final_response = response.text.strip()
        print("Generated roadmap:", final_response)  # Debug output
        return final_response
    except Exception as e:
        print(f"Error generating roadmap: {e}")
        return "An error occurred while generating a personalized study plan. Please try again later."

def calculate_statistics(submissions):
    today = datetime.today()
    start_date = today - timedelta(days=90)
    
    # Filter submissions for the last 90 days
    monthly_submissions = [
        s for s in submissions 
        if datetime.fromtimestamp(s['creationTimeSeconds']) >= start_date
    ]
    
    # Count unique problem attempts and solved status
    problem_attempts = defaultdict(lambda: {'attempts': 0, 'solved': False})
    for sub in monthly_submissions:
        if 'problem' not in sub:
            continue
        problem = sub['problem']
        problem_id = f"{problem.get('contestId', 'unknown')}_{problem.get('index', 'unknown')}"
        problem_attempts[problem_id]['attempts'] += 1
        if sub['verdict'] == 'OK':
            problem_attempts[problem_id]['solved'] = True

    total_problems = len(problem_attempts)
    solved_problems = len([p for p in problem_attempts.values() if p['solved']])
    total_attempts = sum(p['attempts'] for p in problem_attempts.values())
    avg_attempts = round(total_attempts / total_problems, 2) if total_problems else 0
    success_rate = round((solved_problems / total_problems * 100), 1) if total_problems else 0

    response = {
        'total_solved': solved_problems,
        'avg_attempts': avg_attempts,
        'success_rate': success_rate,
        'total_problems_attempted': total_problems,
        'total_attempts': total_attempts
    }

    print(response)

    return response

def get_cp_resources(topic):
    """Get competitive programming resources for a topic"""
    resources = {
        'implementation': [
            ('USACO Guide - Bronze', 'https://usaco.guide/bronze/simulation'),
            ('CSES Problem Set', 'https://cses.fi/problemset/list/'),
            ('USACO Training Gateway', 'https://train.usaco.org/')
        ],
        'math': [
            ('USACO Guide - Math Fundamentals', 'https://usaco.guide/bronze/math-cp'),
            ('Project Euler', 'https://projecteuler.net/archives'),
            ('IMO Training Materials', 'https://www.imo-official.org/problems.aspx')
        ],
        'dp': [
            ('USACO Guide - Gold DP', 'https://usaco.guide/gold/dp-paths'),
            ('AtCoder Educational DP', 'https://atcoder.jp/contests/dp'),
            ('Errichto DP Guide', 'https://github.com/Errichto/youtube/wiki/DP-tutorial')
        ],
        'graphs': [
            ('USACO Guide - Silver Graphs', 'https://usaco.guide/silver/graphs'),
            ('CP Algorithms - Graphs', 'https://cp-algorithms.com/graph/breadth-first-search.html'),
            ('Competitive Programming Handbook', 'https://cses.fi/book/book.pdf#page=119')
        ],
        'data structures': [
            ('USACO Guide - Data Structures', 'https://usaco.guide/silver/binary-search'),
            ('Competitive Programming Handbook', 'https://cses.fi/book/book.pdf#page=87'),
            ('Algorithms for Competitive Programming', 'https://cp-algorithms.com/data_structures/segment_tree.html')
        ],
        'strings': [
            ('USACO Guide - String Processing', 'https://usaco.guide/gold/string-fundamentals'),
            ('CP Algorithms - Strings', 'https://cp-algorithms.com/string/string-hashing.html'),
            ('HackerRank String Problems', 'https://www.hackerrank.com/domains/algorithms?filters%5Bsubdomains%5D%5B%5D=strings')
        ],
        'greedy': [
            ('USACO Guide - Greedy Algorithms', 'https://usaco.guide/silver/greedy'),
            ('Competitive Programming Handbook', 'https://cses.fi/book/book.pdf#page=63'),
            ('Codeforces EDU - Greedy', 'https://codeforces.com/edu/course/2/lesson/2')
        ]
    }
    
    default_resources = [
        ('USACO Training Gateway', 'https://train.usaco.org/'),
        ('Competitive Programming Handbook', 'https://cses.fi/book/book.pdf'),
        ('CP Algorithms', 'https://cp-algorithms.com/'),
        ('CSES Problem Set', 'https://cses.fi/problemset/'),
        ('Codeforces EDU', 'https://codeforces.com/edu/courses')
    ]
    
    return resources.get(topic.lower(), default_resources)

def get_problem_suggestions(topic, user_rating, count=3):
    try:
        difficulty = CodeforcesService.get_difficulty_level(user_rating)
        rating_ranges = {
            'easy': (800, 1200),
            'medium': (1200, 1900),
            'hard': (1900, 3500)
        }
        min_rating, max_rating = rating_ranges[difficulty]

        problems = cache.get(f'problems_{topic}_{min_rating}_{max_rating}')
        if not problems:
            response = requests.get('https://codeforces.com/api/problemset.problems').json()
            if response['status'] == 'OK':
                problems = [p for p in response['result']['problems']
                          if 'rating' in p and min_rating <= p['rating'] <= max_rating]
                cache.set(f'problems_{topic}_{min_rating}_{max_rating}', problems, timeout=3600)
            else:
                problems = []

        suggested = []
        for problem in problems:
            if ('tags' in problem and topic.lower() in [t.lower() for t in problem.get('tags', [])]):
                suggested.append({
                    'platform': 'Codeforces',
                    'name': problem.get('name', 'Unnamed'),
                    'difficulty': problem.get('rating', 'Unknown'),
                    'url': f"https://codeforces.com/problemset/problem/{problem.get('contestId')}/{problem.get('index')}"
                })
            if len(suggested) >= count:
                break
        
        return suggested
    except Exception as e:
        print(f"Error fetching problems: {e}")
        return []

def generate_training_path(topics, user_rating):
    # Sort topics by success rate and complexity
    topic_difficulties = {
        'implementation': 1,
        'math': 2,
        'greedy': 3,
        'dp': 4,
        'graphs': 5,
        'data structures': 3,
        'binary search': 2,
        'strings': 2,
        'number theory': 4,
        'combinatorics': 4,
        'geometry': 5
    }
    
    weighted_topics = []
    for topic, stats in topics.items():
        success_rate = stats['solved'] / (stats['solved'] + stats['attempted']) if stats['solved'] + stats['attempted'] > 0 else 0
        topic_difficulty = topic_difficulties.get(topic.lower(), 3)
        weighted_topics.append((topic, success_rate, topic_difficulty))
    
    # Sort by topic difficulty and then by success rate
    weighted_topics.sort(key=lambda x: (x[2], x[1]))
    path = []
    
    for topic, rate, difficulty in weighted_topics[:5]:
        suggested_problems = get_problem_suggestions(topic, user_rating)
        cp_resources = get_cp_resources(topic)
        
        path.append({
            'topic': topic,
            'difficulty': CodeforcesService.get_difficulty_level(user_rating),
            'success_rate': f"{rate*100:.1f}%",
            'recommended_problems': suggested_problems,
            'description': f"Master {topic} fundamentals through carefully selected problems",
            'estimated_time': '1-2 weeks',
            'learning_resources': [
                {
                    'type': 'resource',
                    'name': f"{name}",
                    'url': url
                } for name, url in cp_resources
            ]
        })
    
    return path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/analyze', methods=['POST'])
@limiter.limit("30 per hour")
def analyze():
    username = request.json.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    try:
        cache_key = f"user_analysis_{username}_{int(time.time() // 3600)}"
        
        cached_result = cache.get(cache_key)
        if (cached_result):
            return jsonify(cached_result)
        
        cf_data = CodeforcesService.get_user_data(username)
        if not cf_data:
            return jsonify({'error': 'Invalid Codeforces username'}), 400
        
        user_rating = cf_data['user_info'].get('rating', 0)
        topics = SubmissionAnalyzer.analyze_submissions(cf_data['submissions'])
        monthly_activity = SubmissionAnalyzer.analyze_monthly_activity(cf_data['submissions'])
        statistics = calculate_statistics(cf_data['submissions'])
        training_path = generate_training_path(topics, user_rating)
        recommendations = SubmissionAnalyzer.generate_recommendations(topics)
        
        result = {
            'user_info': cf_data['user_info'],
            'topics': topics,
            'monthly_activity': monthly_activity,
            'statistics': statistics,
            'training_path': training_path,
            'recommendations': recommendations
        }
        
        # Cache the results
        cache.set(cache_key, result)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Required for Vercel
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))