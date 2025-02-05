from collections import defaultdict
from datetime import datetime, timedelta

class SubmissionAnalyzer:
    @staticmethod
    def analyze_topics(submissions):
        topics = defaultdict(lambda: {'solved': 0, 'attempted': 0})
        
        for sub in submissions:
            if 'problem' not in sub or 'tags' not in sub['problem']:
                continue
                
            for tag in sub['problem']['tags']:
                if sub['verdict'] == 'OK':
                    topics[tag]['solved'] += 1
                topics[tag]['attempted'] += 1
                
        return dict(topics)

    @staticmethod
    def analyze_monthly_activity(submissions):
        today = datetime.today()
        start_date = today - timedelta(days=90)
        
        daily_counts = defaultdict(int)
        
        for sub in submissions:
            sub_date = datetime.fromtimestamp(sub['creationTimeSeconds'])
            if sub_date >= start_date and sub['verdict'] == 'OK':
                daily_counts[sub_date.strftime('%Y-%m-%d')] += 1
        
        dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') 
                for x in range(91)]
                
        return {
            'labels': dates,
            'values': [daily_counts.get(date, 0) for date in dates],
            'total_solved': sum(daily_counts.values())
        }
