from collections import defaultdict
from datetime import datetime, timedelta

class SubmissionAnalyzer:
    @staticmethod
    def analyze_submissions(submissions):
        topics = {}
        for sub in submissions:
            try:
                if 'problem' in sub and 'tags' in sub['problem']:
                    for tag in sub['problem']['tags']:
                        if tag not in topics:
                            topics[tag] = {'solved': 0, 'attempted': 0}
                        if 'verdict' in sub and sub['verdict'] == 'OK':
                            topics[tag]['solved'] += 1
                        else:
                            topics[tag]['attempted'] += 1
            except Exception as e:
                print(f"Error processing submission tags: {e}")
                continue
        
        return topics

    @staticmethod
    def analyze_monthly_activity(submissions):
        today = datetime.today()
        start_date = today - timedelta(days=90)
        
        daily_counts = defaultdict(int)
        filtered_submissions = [
            sub for sub in submissions 
            if datetime.fromtimestamp(sub['creationTimeSeconds']) >= start_date
        ]
        
        for sub in filtered_submissions:
            sub_date = datetime.fromtimestamp(sub['creationTimeSeconds'])
            if 'verdict' in sub and sub['verdict'] == 'OK':
                daily_counts[sub_date.strftime('%Y-%m-%d')] += 1
        
        dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') 
                for x in range(91)]
        values = [daily_counts.get(date, 0) for date in dates]
        
        return {
            'labels': dates,
            'values': values,
            'total_solved': sum(values)
        }

    @staticmethod
    def generate_recommendations(topics):
        weak_topics = []
        for topic, stats in topics.items():
            if topic.lower() == 'special problems':
                continue
            success_rate = stats['solved'] / (stats['solved'] + stats['attempted']) if stats['solved'] + stats['attempted'] > 0 else 0
            if success_rate < 0.5:
                weak_topics.append((topic, success_rate))
        
        weak_topics.sort(key=lambda x: x[1])
        recommendations = []
        
        if weak_topics:
            recommendations.extend([
                f"Focus on {topic} problems (current success rate: {rate*100:.1f}%)"
                for topic, rate in weak_topics[:5]
            ])
        else:
            recommendations.append("Great job! You're doing well across all topics.")
        
        return recommendations

    @staticmethod
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
            if 'verdict' in sub and sub['verdict'] == 'OK':
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