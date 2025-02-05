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
            'submissions': submissions['result'][:100]
        }

    @staticmethod
    @cache.memoize(timeout=3600)
    def get_problems(topic, min_rating, max_rating):
        response = requests.get('https://codeforces.com/api/problemset.problems').json()
        if response['status'] != 'OK':
            return []
            
        return [p for p in response['result']['problems']
                if 'rating' in p and min_rating <= p['rating'] <= max_rating]
