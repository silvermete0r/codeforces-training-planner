import requests
from flask_caching import Cache

cache = Cache()

class CodeforcesService:
    @staticmethod
    def get_user_data(username):
        user_info = requests.get(f'https://codeforces.com/api/user.info?handles={username}').json()
        submissions = requests.get(f'https://codeforces.com/api/user.status?handle={username}').json()
        
        if user_info['status'] != 'OK' or submissions['status'] != 'OK':
            return None
            
        return {
            'user_info': user_info['result'][0],
            'submissions': submissions['result'][:3000]
        }

    @staticmethod
    @cache.memoize(timeout=3600)
    def get_problems(topic, min_rating, max_rating):
        response = requests.get('https://codeforces.com/api/problemset.problems').json()
        if response['status'] != 'OK':
            return []
            
        return [p for p in response['result']['problems']
                if 'rating' in p and min_rating <= p['rating'] <= max_rating]
    
    @staticmethod
    def get_difficulty_level(rating):
        if rating < 1200:
            return 'easy'
        elif rating < 1900:
            return 'medium'
        else:
            return 'hard'

    @staticmethod
    def analyze_submissions(submissions):
        topics = {}
        for sub in submissions:
            try:
                if 'problem' in sub and 'tags' in sub['problem']:
                    for tag in sub['problem']['tags']:
                        if tag not in topics:
                            topics[tag] = {'solved': 0, 'attempted': 0}
                        if sub['verdict'] == 'OK':
                            topics[tag]['solved'] += 1
                        else:
                            topics[tag]['attempted'] += 1
            except Exception as e:
                print(f"Error processing submission tags: {e}")
                continue
        
        return topics
