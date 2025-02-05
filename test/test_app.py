import pytest
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_analyze_endpoint_success(client):
    with patch('app.get_codeforces_data') as mock_cf_data, \
         patch('app.analyze_submissions') as mock_analyze, \
         patch('app.analyze_monthly_activity') as mock_monthly, \
         patch('app.generate_training_path') as mock_training, \
         patch('app.generate_recommendations') as mock_recommendations:
        
        # Setup mocks
        mock_cf_data.return_value = {
            'user_info': {'handle': 'testuser', 'rating': 1500},
            'submissions': []
        }
        mock_analyze.return_value = {'math': {'solved': 1, 'attempted': 1}}
        mock_monthly.return_value = {'labels': [], 'values': [], 'total_solved': 0}
        mock_training.return_value = []
        mock_recommendations.return_value = []

        # Make request
        response = client.post('/analyze', json={'username': 'testuser'})

        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert data['user_info']['handle'] == 'testuser'

def test_analyze_endpoint_no_username(client):
    response = client.post('/analyze', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Username is required'