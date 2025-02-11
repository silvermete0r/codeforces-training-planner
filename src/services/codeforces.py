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
    def get_difficulty_level(rating):
        if rating < 1200:
            return 'easy'
        elif rating < 1900:
            return 'medium'
        else:
            return 'hard'
        
    @staticmethod
    def get_cp_resources(topic):
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

    
