(function() {
    let activityChart = null;
    let topicsChart = null;

    const elements = {
        usernameForm: document.getElementById('usernameForm'),
        usernameInput: document.getElementById('username'),
        handleSuggestion: document.querySelector('.handle-suggestion'),
        loadingContainer: document.getElementById('loadingContainer'),
        results: document.getElementById('results'),
        error: document.getElementById('error'),
        userProfile: document.getElementById('userProfile'),
        userStatus: document.getElementById('userStatus'),
        totalSolved: document.getElementById('totalSolved'),
        monthSolved: document.getElementById('monthSolved'),
        avgAttempts: document.getElementById('avgAttempts'),
        successRate: document.getElementById('successRate'),
        activityChartCanvas: document.getElementById('activityChart'),
        topicsChartCanvas: document.getElementById('topicsChart'),
        recommendations: document.getElementById('recommendations'),
        trainingPath: document.getElementById('trainingPath')
    };

    const apiEndpoints = {
        analyze: '/analyze'
    };

    const ui = {
        showLoading: () => {
            elements.loadingContainer.classList.remove('hidden');
            elements.results.classList.add('hidden');
            elements.error.classList.add('hidden');
        },
        hideLoading: () => {
            elements.loadingContainer.classList.add('hidden');
        },
        showResults: () => {
            elements.results.classList.remove('hidden');
        },
        showError: (message) => {
            elements.error.querySelector('span').textContent = message;
            elements.error.classList.remove('hidden');
        },
        updateElement: (element, content) => {
            if (element) {
                element.innerHTML = content;
            } else {
                console.warn(`Element not found`);
            }
        }
    };

    const chartConfig = {
        activityChart: {
            type: 'line',
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: { duration: 2000, easing: 'easeInOutQuart' },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(0, 0, 0, 0.1)' } },
                    x: { grid: { display: false } }
                },
                plugins: { legend: { display: true, position: 'top' }, tooltip: { mode: 'index', intersect: false } }
            }
        },
        topicsChart: {
            type: 'radar',
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { r: { beginAtZero: true, ticks: { display: false } } },
                plugins: { legend: { position: 'top' } }
            }
        }
    };

    const render = {
        userInfo: (data) => {
            ui.updateElement(elements.userProfile, `
                <div class="space-y-2">
                    <div class="flex items-center gap-2">
                        <img src="${data.avatar}" class="w-12 h-12 rounded-full">
                        <div>
                            <h4 class="font-medium">${data.handle}</h4>
                            <p class="text-sm text-gray-500">Rank: ${data.rank || 'Unrated'}</p>
                        </div>
                    </div>
                </div>
            `);
        },
        userStatus: (data) => {
            ui.updateElement(elements.userStatus, `
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-sm text-gray-500">Current Rating</p>
                        <p class="text-xl font-semibold">${data.rating || 'Unrated'}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">Max Rating</p>
                        <p class="text-xl font-semibold">${data.maxRating || 'N/A'}</p>
                    </div>
                </div>
            `);
        },
        statistics: (data) => {
            ui.updateElement(elements.totalSolved, data.total_solved);
            ui.updateElement(elements.monthSolved, data.total_solved);
            ui.updateElement(elements.avgAttempts, data.avg_attempts);
            ui.updateElement(elements.successRate, `${data.success_rate}%`);
        },
        activityChart: (labels, values) => {
            if (activityChart) activityChart.destroy();
            activityChart = new Chart(elements.activityChartCanvas, {
                ...chartConfig.activityChart,
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Problems Solved',
                        data: values,
                        borderColor: '#3b82f6',
                        tension: 0.3,
                        fill: true,
                        backgroundColor: 'rgba(59, 130, 246, 0.1)'
                    }]
                }
            });
        },
        topicsChart: (topics) => {
            if (topicsChart) topicsChart.destroy();
            elements.topicsChartCanvas.parentNode.style.height = '600px';
            topicsChart = new Chart(elements.topicsChartCanvas, {
                type: 'radar',
                data: {
                    labels: Object.keys(topics),
                    datasets: [{
                        label: 'Solved Problems',
                        data: Object.values(topics).map(t => t.solved),
                        backgroundColor: 'rgba(59, 130, 246, 0.2)',
                        borderColor: '#3b82f6',
                        pointBackgroundColor: '#3b82f6',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#3b82f6'
                    }]
                },
                options: chartConfig.topicsChart.options
            });
        },
        recommendations: (recs) => {
            if (elements.recommendations) {
                elements.recommendations.innerHTML = recs.map(rec => `
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
                        <div class="flex items-center gap-3">
                            <span class="text-2xl">📊</span>
                            <p class="text-gray-800">${rec}</p>
                        </div>
                    </div>
                `).join('');
            }
        },
        trainingPath: (path) => {
            if (elements.trainingPath) {
                elements.trainingPath.innerHTML = path.map((step, index) => `
                    <div class="roadmap-card relative ${index === 0 ? 'first-card' : ''} ${index === path.length - 1 ? 'last-card' : ''}">
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
        }
    };

    const dataHandlers = {
        analyzeUser: async (username) => {
            ui.showLoading();
            try {
                const response = await fetch(apiEndpoints.analyze, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error);

                render.userInfo(data.user_info);
                render.userStatus(data.user_info);
                render.statistics(data.statistics);
                render.activityChart(data.monthly_activity.labels, data.monthly_activity.values);
                render.topicsChart(data.topics);
                render.recommendations(data.recommendations);
                render.trainingPath(data.training_path);

                ui.showResults();
            } catch (err) {
                ui.showError(err.message);
            } finally {
                ui.hideLoading();
            }
        }
    };

    const eventListeners = {
        setupFormSubmit: () => {
            elements.usernameForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = elements.usernameInput.value;
                await dataHandlers.analyzeUser(username);
            });
        },
        setupHandleSuggestion: () => {
            elements.usernameInput.addEventListener('focus', () => {
                elements.handleSuggestion.style.display = 'block';
            });

            elements.usernameInput.addEventListener('blur', () => {
                setTimeout(() => {
                    elements.handleSuggestion.style.display = 'none';
                }, 200);
            });
        },
        setupUserBadgeClick: () => {
            document.querySelector('.flex.justify-center').addEventListener('click', function(e) {
                const userBadge = e.target.closest('.user-badge');
                if (userBadge) {
                    const handle = userBadge.dataset.handle;
                    if (handle) {
                        fillUsername(handle);
                    }
                }
            });
        }
    };

    function fillUsername(handle) {
        elements.usernameInput.value = handle;
        const clickedBadge = document.querySelector(`[data-handle="${handle}"]`);
        if (clickedBadge) {
            clickedBadge.style.transform = 'scale(0.95)';
            setTimeout(() => {
                clickedBadge.style.transform = '';
                elements.usernameForm.dispatchEvent(new Event('submit', { cancelable: true }));
            }, 200);
        }
    }

    function downloadTrainingJSON() {
        const trainingPath = elements.trainingPath;
        if (!trainingPath) return;

        const username = elements.usernameInput.value;
        const trainingPlan = {
            username: username,
            generated_at: new Date().toISOString(),
            training_path: Array.from(trainingPath.children).map(card => {
                const topic = card.querySelector('h4').textContent;
                const description = card.querySelector('p').textContent;
                const difficulty = card.querySelector('.rounded-full').textContent;
                const successRate = card.querySelector('.progress-bar-fill').style.width;
                const problems = Array.from(card.querySelectorAll('.problem-card')).map(problem => ({
                    name: problem.querySelector('.font-medium').textContent,
                    difficulty: problem.querySelector('.text-sm').textContent.replace('Difficulty: ', ''),
                    url: problem.href
                }));
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
        const jsonString = JSON.stringify(trainingPlan, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `codeforces_training_plan_${username}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    const init = () => {
        eventListeners.setupFormSubmit();
        eventListeners.setupHandleSuggestion();
        eventListeners.setupUserBadgeClick();
    };

    document.addEventListener('DOMContentLoaded', init);

    console.log(`
        /\\___/\\
       (  o o  )
       (  =^=  ) 
        (--m--)  Nothing to see here! 
    `);
})();