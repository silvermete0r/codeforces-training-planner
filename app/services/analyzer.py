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
                        if sub['verdict'] == 'OK':
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
        start_date = today - timedelta(days=90)  # <= 90 days (3 months)
        
        daily_counts = defaultdict(int)
        filtered_submissions = [
            sub for sub in submissions 
            if datetime.fromtimestamp(sub['creationTimeSeconds']) >= start_date
        ]
        
        for sub in filtered_submissions:
            sub_date = datetime.fromtimestamp(sub['creationTimeSeconds'])
            if sub['verdict'] == 'OK':
                daily_counts[sub_date.strftime('%Y-%m-%d')] += 1
        
        dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') 
                for x in range(91)]  # < 91 days
        values = [daily_counts.get(date, 0) for date in dates]
        
        return {
            'labels': dates,
            'values': values,
            'total_solved': sum(values)
        }

    def generate_recommendations(topics):
        weak_topics = []
        for topic, stats in topics.items():
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
        
        return recommendations