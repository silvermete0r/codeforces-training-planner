from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import requests, time, os, hashlib
import google.generativeai as genai
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

from src.config import Config
from src.services.codeforces import CodeforcesService
from src.services.analyzer import SubmissionAnalyzer

# Setup Flask app
load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = os.urandom(24)

cache = Cache(config={
    'CACHE_TYPE': Config.CACHE_TYPE,
    'CACHE_DEFAULT_TIMEOUT': Config.CACHE_DEFAULT_TIMEOUT
})
cache.init_app(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.RATELIMIT_DEFAULT],
    storage_uri=Config.RATELIMIT_STORAGE_URL
)

# Initialize services
codeforces_service = CodeforcesService()
submission_analyzer = SubmissionAnalyzer()

# Configure Google Gemini AI
genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Serve static files through Flask routes
@app.route('/static/<path:path>')
def send_static(path):
    # Obfuscate JavaScript files
    if path.endswith('.js'):
        return send_from_directory('static', path, mimetype='text/plain')
    return send_from_directory('static', path)

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
        if topic.lower() == '*special problems':
            continue
        success_rate = stats['solved'] / (stats['solved'] + stats['attempted']) if stats['solved'] + stats['attempted'] > 0 else 0
        topic_difficulty = topic_difficulties.get(topic.lower(), 3)
        weighted_topics.append((topic, success_rate, topic_difficulty))
    
    # Sort by topic difficulty and then by success rate
    weighted_topics.sort(key=lambda x: (x[2], x[1]))
    path = []
    
    for topic, rate, difficulty in weighted_topics[:5]:
        suggested_problems = get_problem_suggestions(topic, user_rating)
        cp_resources = CodeforcesService.get_cp_resources(topic)
        
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

# Routes
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
        if cached_result:
            return jsonify(cached_result)
        
        cf_data = CodeforcesService.get_user_data(username)
        if not cf_data:
            return jsonify({'error': 'Invalid Codeforces username'}), 400
        
        user_rating = cf_data['user_info'].get('rating', 0)
        topics = SubmissionAnalyzer.analyze_submissions(cf_data['submissions'])
        monthly_activity = SubmissionAnalyzer.analyze_monthly_activity(cf_data['submissions'])
        statistics = SubmissionAnalyzer.calculate_statistics(cf_data['submissions'])
        # NEW: catch gemini overload from training path generation
        try:
            training_path = generate_training_path(topics, user_rating)
        except requests.exceptions.JSONDecodeError:
            return jsonify({"error": "gemini ai api is too loaded and try again later"}), 503
        recommendations = SubmissionAnalyzer.generate_recommendations(topics)
        
        result = {
            'user_info': cf_data['user_info'],
            'topics': topics,
            'monthly_activity': monthly_activity,
            'statistics': statistics,
            'training_path': training_path,
            'recommendations': recommendations
        }
        cache.set(cache_key, result)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Download analysis as JSON
@app.route('/download', methods=['GET'])
@limiter.limit("30 per hour")
@cache.cached(timeout=3600) # Cache for 1 hour
def download_analysis():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username query parameter is required'}), 400
    cf = CodeforcesService.get_user_data(username)
    if not cf:
        return jsonify({'error': 'Invalid Codeforces username'}), 400
    rating = cf['user_info'].get('rating', 0)
    topics = SubmissionAnalyzer.analyze_submissions(cf['submissions'])
    stats = SubmissionAnalyzer.calculate_statistics(cf['submissions'])
    path = generate_training_path(topics, rating)
    recs = SubmissionAnalyzer.generate_recommendations(topics)
    result = {
        'user_info': cf['user_info'],
        'topics': topics,
        'statistics': stats,
        'training_path': path,
        'recommendations': recs
    }
    response = make_response(jsonify(result))
    response.headers['Content-Disposition'] = 'attachment; filename=analysis.json'
    response.mimetype = 'application/json'
    return response

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=()'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))