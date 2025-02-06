let currentUsername = '';
let activityChart = null;
let topicsChart = null;

document.getElementById('usernameForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    await analyzeUser(username);
});

async function analyzeUser(username) {
    const loadingContainer = document.getElementById('loadingContainer');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    
    loadingContainer.classList.remove('hidden');
    results.classList.add('hidden');
    error.classList.add('hidden');
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username }),
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);

        // Destroy existing charts
        if (activityChart) activityChart.destroy();
        if (topicsChart) topicsChart.destroy();

        // Helper function to safely update element content
        const updateElement = (id, content) => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = content;
            } else {
                console.warn(`Element with id '${id}' not found`);
            }
        };

        // Update elements with safety checks
        updateElement('userProfile', `
            <div class="space-y-2">
                <div class="flex items-center gap-2">
                    <img src="${data.user_info.avatar}" class="w-12 h-12 rounded-full">
                    <div>
                        <h4 class="font-medium">${data.user_info.handle}</h4>
                        <p class="text-sm text-gray-500">Rank: ${data.user_info.rank || 'Unrated'}</p>
                    </div>
                </div>
            </div>
        `);

        updateElement('userStatus', `
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="text-sm text-gray-500">Current Rating</p>
                    <p class="text-xl font-semibold">${data.user_info.rating || 'Unrated'}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-500">Max Rating</p>
                    <p class="text-xl font-semibold">${data.user_info.maxRating || 'N/A'}</p>
                </div>
            </div>
        `);

        // Update statistics with safety checks
        ['totalSolved', 'monthSolved', 'avgAttempts', 'successRate'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                switch(id) {
                    case 'totalSolved':
                        element.textContent = data.statistics.total_solved;
                        break;
                    case 'monthSolved':
                        element.textContent = data.statistics.total_solved;
                        break;
                    case 'avgAttempts':
                        element.textContent = data.statistics.avg_attempts;
                        break;
                    case 'successRate':
                        element.textContent = `${data.statistics.success_rate}%`;
                        break;
                }
            }
        });

        // Render monthly activity chart
        activityChart = new Chart(document.getElementById('activityChart'), {
            type: 'line',
            data: {
                labels: data.monthly_activity.labels,
                datasets: [{
                    label: 'Problems Solved',
                    data: data.monthly_activity.values,
                    borderColor: '#3b82f6',
                    tension: 0.3,
                    fill: true,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });

        // Dynamically set the radar chart container height to make the graph bigger.
        document.getElementById('topicsChart').parentNode.style.height = '600px';

        // Render topics performance chart
        topicsChart = new Chart(document.getElementById('topicsChart'), {
            type: 'radar',
            data: {
                labels: Object.keys(data.topics),
                datasets: [{
                    label: 'Solved Problems',
                    data: Object.values(data.topics).map(t => t.solved),
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: '#3b82f6',
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#3b82f6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Changed to allow bigger chart
                scales: {
                    r: {
                        beginAtZero: true,
                        ticks: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });

        // Show recommendations under the radar chart
        const recommendations = document.getElementById('recommendations');
        if (recommendations) {
            recommendations.innerHTML = data.recommendations.map(rec => `
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
                    <div class="flex items-center gap-3">
                        <span class="text-2xl">📊</span>
                        <p class="text-gray-800">${rec}</p>
                    </div>
                </div>
            `).join('');
        }

        // Render training path with improved visualization
        const trainingPath = document.getElementById('trainingPath');
        if (trainingPath) {
            trainingPath.innerHTML = data.training_path.map((step, index) => `
                <div class="roadmap-card relative ${index === 0 ? 'first-card' : ''} ${index === data.training_path.length - 1 ? 'last-card' : ''}">
                    <div class="step-number">${index + 1}</div>
                    <div class="flex justify-between items-start mb-6">
                        <div class="flex-grow">
                            <h4 class="font-medium text-gray-800 text-xl mb-2">${step.topic}</h4>
                            <p class="text-gray-600">${step.description}</p>
                            <div class="mt-3 flex items-center">
                                <span class="text-sm font-medium text-gray-600">Difficulty:</span>
                                <span class="ml-2 px-3 py-1 rounded-full text-sm font-medium
                                    ${step.difficulty === 'basic' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                    ${step.difficulty.charAt(0).toUpperCase() + step.difficulty.slice(1)}
                                </span>
                                <span class="ml-4 text-sm font-medium text-gray-600">Estimated time:</span>
                                <span class="ml-2 text-sm text-gray-800">${step.estimated_time}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-6">
                        <div class="flex justify-between text-sm mb-2">
                            <span class="font-medium text-gray-600">Mastery Progress</span>
                            <span class="font-medium text-gray-800">${step.success_rate}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-bar-fill" style="width: ${step.success_rate}"></div>
                        </div>
                    </div>

                    <div class="space-y-4">
                        <div>
                            <h5 class="font-medium text-gray-800 mb-3">📝 Practice Problems</h5>
                            <div class="grid grid-cols-1 gap-3">
                                ${step.recommended_problems.map(problem => `
                                    <a href="${problem.url}" 
                                       target="_blank" 
                                       class="problem-card">
                                        <div class="flex items-center space-x-3">
                                            <img src="https://img.icons8.com/?size=160&id=jldAN67IAsrW&format=png" 
                                                 alt="Codeforces" 
                                                 class="w-6 h-6">
                                            <div>
                                                <div class="font-medium text-gray-800">${problem.name}</div>
                                                <div class="text-sm text-gray-600">
                                                    Difficulty: ${problem.difficulty}
                                                </div>
                                            </div>
                                        </div>
                                    </a>
                                `).join('')}
                            </div>
                        </div>

                        <div>
                            <h5 class="font-medium text-gray-800 mb-3">📚 Learning Resources</h5>
                            <div class="grid grid-cols-1 gap-3">
                                ${step.learning_resources.map(resource => `
                                    <a href="${resource.url}" 
                                       target="_blank" 
                                       class="resource-card hover:bg-blue-50">
                                        <div class="flex items-center">
                                            <div class="flex-1">
                                                <span class="font-medium">${resource.name}</span>
                                            </div>
                                            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                            </svg>
                                        </div>
                                    </a>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        results.classList.remove('hidden');
    } catch (err) {
        error.querySelector('span').textContent = err.message;
        error.classList.remove('hidden');
    } finally {
        loadingContainer.classList.add('hidden');
    }
}

// Interactive handle suggestion
const usernameInput = document.getElementById('username');
const handleSuggestion = document.querySelector('.handle-suggestion');

usernameInput.addEventListener('focus', () => {
    handleSuggestion.style.display = 'block';
});

usernameInput.addEventListener('blur', () => {
    setTimeout(() => {
        handleSuggestion.style.display = 'none';
    }, 200);
});

// Simulate dynamic star count
function updateStarCount() {
    const starCount = document.getElementById('starCount');
    const currentCount = parseInt(starCount.textContent.replace('★ ', ''));
    const newCount = currentCount + Math.floor(Math.random() * 3); // Random increment
    starCount.textContent = `★ ${newCount}`;
}

setInterval(updateStarCount, 30000); // Update every 30 seconds

// Replace downloadTrainingPDF with downloadTrainingJSON
function downloadTrainingJSON() {
    const trainingPath = document.getElementById('trainingPath');
    if (!trainingPath) return;

    // Get current username from the input
    const username = document.getElementById('username').value;
    
    // Create training plan object
    const trainingPlan = {
        username: username,
        generated_at: new Date().toISOString(),
        training_path: Array.from(trainingPath.children).map(card => {
            const topic = card.querySelector('h4').textContent;
            const description = card.querySelector('p').textContent;
            const difficulty = card.querySelector('.rounded-full').textContent;
            const successRate = card.querySelector('.progress-bar-fill').style.width;
            
            // Get recommended problems
            const problems = Array.from(card.querySelectorAll('.problem-card')).map(problem => ({
                name: problem.querySelector('.font-medium').textContent,
                difficulty: problem.querySelector('.text-sm').textContent.replace('Difficulty: ', ''),
                url: problem.href
            }));
            
            // Get learning resources
            const resources = Array.from(card.querySelectorAll('.resource-card')).map(resource => ({
                name: resource.querySelector('.font-medium').textContent,
                url: resource.href
            }));
            
            return {
                topic,
                description,
                difficulty,
                success_rate: successRate,
                recommended_problems: problems,
                learning_resources: resources
            };
        })
    };
    
    // Convert to JSON string
    const jsonString = JSON.stringify(trainingPlan, null, 2);
    
    // Create download link
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `codeforces_training_plan_${username}.json`;
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Event delegation for user badges
document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('.flex.justify-center').addEventListener('click', function(e) {
        const userBadge = e.target.closest('.user-badge');
        if (userBadge) {
            const handle = userBadge.dataset.handle;
            if (handle) {
                fillUsername(handle);
            }
        }
    });
});

// Update fillUsername function
function fillUsername(handle) {
    const input = document.getElementById('username');
    input.value = handle;
    
    // Animate clicked badge
    const clickedBadge = document.querySelector(`[data-handle="${handle}"]`);
    if (clickedBadge) {
        clickedBadge.style.transform = 'scale(0.95)';
        setTimeout(() => {
            clickedBadge.style.transform = '';
            // Submit form after animation
            document.getElementById('usernameForm').dispatchEvent(
                new Event('submit', { cancelable: true })
            );
        }, 200);
    }
}