document.addEventListener('DOMContentLoaded', function() {
    const startForm = document.getElementById('start-form');
    const startScreen = document.getElementById('start-screen');
    const introScreen = document.getElementById('intro-screen');
    const interviewScreen = document.getElementById('interview-screen');
    const reportScreen = document.getElementById('report-screen');
    
    let currentQuestion = null;
    
    const video = document.getElementById('intro-video');

    // Video error handling
    video.addEventListener('error', function(e) {
        console.error('Error loading video:', e);
        console.error('Video source:', video.getElementsByTagName('source')[0].src);
        showAlert('Error loading introduction video. Please refresh the page.');
    });

    // Video loaded successfully
    video.addEventListener('loadeddata', function() {
        console.log('Video loaded successfully');
    });
    
    // Add these functions at the top of your existing JavaScript
    function startTimer(duration, display) {
        let timer = duration;
        const countdown = setInterval(function () {
            const minutes = parseInt(timer / 60, 10);
            const seconds = parseInt(timer % 60, 10);

            display.textContent = minutes.toString().padStart(2, '0') + ':' + 
                                seconds.toString().padStart(2, '0');

            if (--timer < 0) {
                clearInterval(countdown);
                document.getElementById('start-interview-btn').click();
            }
        }, 1000);
        return countdown;
    }

    // Update the form submission handler
    startForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const candidateName = document.getElementById('candidate-name').value;
        const candidateEmail = document.getElementById('candidate-email').value;
        
        if (!candidateName.trim() || !candidateEmail.trim()) {
            showAlert('Please enter both name and email to continue.');
            return;
        }
        
        // Show introduction screen
        startScreen.classList.add('hidden');
        introScreen.classList.remove('hidden');
        
        // Set welcome message with candidate's name
        document.getElementById('welcome-message').textContent = 
            `Welcome to BEI Interview, ${candidateName}`;
        
        // Start 10-minute timer
        const tenMinutes = 60 * 10;
        const timerDisplay = document.getElementById('timer');
        const countdown = startTimer(tenMinutes, timerDisplay);
        
        // Try to play video
        try {
            await video.play();
        } catch (err) {
            console.log('Auto-play prevented:', err);
        }
        
        // Store countdown to clear it if user clicks start before timeout
        window.interviewCountdown = countdown;
    });
    
    // Update the start interview button handler
    document.getElementById('start-interview-btn').addEventListener('click', async function() {
        // Clear the countdown if it exists
        if (window.interviewCountdown) {
            clearInterval(window.interviewCountdown);
        }
        
        const candidateName = document.getElementById('candidate-name').value;
        const candidateEmail = document.getElementById('candidate-email').value;
        
        try {
            const response = await fetch('/start_interview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    candidate_name: candidateName,
                    candidate_email: candidateEmail
                })
            });
            
            const data = await response.json();
            if (data.error) {
                showAlert(data.error);
                return;
            }
            
            introScreen.classList.add('hidden');
            interviewScreen.classList.remove('hidden');
            displayQuestion(data);
        } catch (error) {
            showAlert('Failed to start interview. Please try again.');
        }
    });
    
    document.getElementById('submit-answer').addEventListener('click', async function() {
        const answerText = document.getElementById('answer').value.trim();
        if (!answerText) {
            showAlert('Please provide an answer before continuing.');
            return;
        }
        
        try {
            const response = await fetch('/submit_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ answer: answerText })
            });
            
            const data = await response.json();
            
            // Check if interview is complete
            if (data.complete) {
                // Hide feedback box and show loading message
                document.getElementById('feedback-box').classList.add('hidden');
                showAlert('Generating your interview report...');
                
                // Generate and show report
                await showReport();
                return;
            }
            
            // Show feedback for current answer
            const feedbackBox = document.getElementById('feedback-box');
            const feedbackText = document.getElementById('feedback-text');
            
            feedbackBox.classList.remove('hidden');
            feedbackText.innerHTML = `
                <div class="space-y-2">
                    <p class="font-medium">Feedback on your response:</p>
                    <p>${data.feedback}</p>
                </div>
            `;
            
            // Store next question data
            currentQuestion = data;
            
            // Update progress
            document.getElementById('question-counter').textContent = 
                `Question ${data.current_number} of ${data.total_questions}`;
            
            const progress = (data.current_number / data.total_questions) * 100;
            document.getElementById('progress').style.width = `${progress}%`;
            
        } catch (error) {
            console.error('Error:', error);
            showAlert('Failed to submit answer. Please try again.');
        }
    });
    
    document.getElementById('next-question').addEventListener('click', function() {
        document.getElementById('feedback-box').classList.add('hidden');
        document.getElementById('answer').value = '';
        displayQuestion(currentQuestion);
    });
    
    function displayQuestion(data) {
        document.getElementById('current-question').textContent = data.question;
        document.getElementById('question-counter').textContent = 
            `Question ${data.current_number} of ${data.total_questions}`;
        
        const progress = (data.current_number / data.total_questions) * 100;
        document.getElementById('progress').style.width = `${progress}%`;
    }
    
    async function showReport() {
        try {
            // Show loading state
            const loadingHtml = `
                <div class="text-center py-8">
                    <p class="text-lg text-gray-600">Generating your report...</p>
                </div>
            `;
            document.getElementById('report-screen').innerHTML = loadingHtml;
            document.getElementById('report-screen').classList.remove('hidden');
            document.getElementById('interview-screen').classList.add('hidden');

            const response = await fetch('/generate_report', {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const report = await response.json();
            
            if (report.error) {
                throw new Error(report.error);
            }

            // Create report HTML
            const reportHtml = `
                <div class="bg-white rounded-xl shadow-lg p-8">
                    <div class="mb-8 text-center">
                        <h2 class="text-3xl font-bold text-gray-800 mb-2">Interview Assessment Report</h2>
                        <p class="text-gray-600">
                            ${report.candidate_info.name} | ${report.candidate_info.interview_date}
                        </p>
                    </div>

                    <!-- Overall Performance Section -->
                    <div class="bg-blue-50 rounded-lg p-6 mb-6">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-xl font-semibold">Overall Performance</h3>
                            <div class="text-right">
                                <span class="text-2xl font-bold ${getScoreColorClass(report.overall_score)}">
                                    ${report.overall_score}/4.0
                                </span>
                                <p class="text-lg font-medium">${report.rating}</p>
                            </div>
                        </div>
                    </div>

                    <!-- Competency Visualization Section -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <!-- Spider Chart -->
                        <div class="bg-gray-50 rounded-lg p-6">
                            <h3 class="text-lg font-semibold mb-4">Core Competencies</h3>
                            <canvas id="spiderChart"></canvas>
                        </div>
                        
                        <!-- Scores Table -->
                        <div class="bg-gray-50 rounded-lg p-6">
                            <h3 class="text-lg font-semibold mb-4">Competency Scores</h3>
                            ${Object.entries(report.competency_scores)
                                .map(([competency, score]) => `
                                    <div class="flex justify-between items-center mb-2">
                                        <span class="text-gray-700">${formatMetricName(competency)}</span>
                                        <span class="font-medium ${getScoreColorClass(score)}">${score}/4.0</span>
                                    </div>
                                `).join('')}
                        </div>
                    </div>

                    <!-- Question Performance Charts -->
                    <div class="mb-8">
                        <h3 class="text-lg font-semibold mb-4">Question Performance</h3>
                        <div class="grid grid-cols-1 gap-4">
                            ${report.responses.map((response, index) => `
                                <div class="bg-gray-50 rounded-lg p-4">
                                    <h4 class="font-medium mb-2">Question ${index + 1}</h4>
                                    <canvas id="questionChart${index}"></canvas>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Conversation Summary -->
                    <div class="mb-8">
                        <h3 class="text-lg font-semibold mb-4">Conversation Summary</h3>
                        ${report.responses.map((response, index) => `
                            <div class="bg-gray-50 rounded-lg p-4 mb-4">
                                <div class="mb-3">
                                    <span class="font-medium">Q${index + 1}:</span>
                                    <span class="text-gray-700">${response.question}</span>
                                </div>
                                <div class="pl-4 border-l-4 border-blue-200">
                                    <span class="font-medium">A:</span>
                                    <span class="text-gray-600">${response.answer}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Download Button -->
                    <div class="flex justify-center">
                        <button onclick="downloadReport(${JSON.stringify(report)})" 
                                class="bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700 transition duration-200">
                            Download Report
                        </button>
                    </div>
                </div>
            `;

            document.getElementById('report-screen').innerHTML = reportHtml;

            // Create visualizations after HTML is inserted
            createSpiderChart(report.competency_scores);
            report.responses.forEach((response, index) => {
                createQuestionChart(index, response.scores);
            });

        } catch (error) {
            console.error('Error generating report:', error);
            document.getElementById('report-screen').innerHTML = `
                <div class="bg-white rounded-xl shadow-lg p-8 text-center">
                    <h2 class="text-2xl font-bold text-red-600 mb-4">Error Generating Report</h2>
                    <p class="text-gray-700 mb-4">There was an error generating your report. Please try again.</p>
                    <p class="text-sm text-gray-500 mb-4">Error details: ${error.message}</p>
                    <button onclick="location.reload()" 
                            class="bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700 transition duration-200">
                        Restart Interview
                    </button>
                </div>
            `;
        }
    }

    function getScoreColorClass(score) {
        if (score >= 3.5) return 'text-green-600';
        if (score >= 2.5) return 'text-blue-600';
        return 'text-red-600';
    }

    function getPerformanceLabel(score) {
        if (score >= 3.5) return 'Excellent';
        if (score >= 3.0) return 'Very Good';
        if (score >= 2.0) return 'Good';
        return 'Needs Improvement';
    }

    function createSpiderChart(scores) {
        const ctx = document.getElementById('spiderChart').getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Communicate Clearly', 'Engage Discussion', 'Engage Actively'],
                datasets: [{
                    label: 'Competency Scores',
                    data: [
                        scores.communicate_clearly || 0,
                        scores.engage_discussion || 0,
                        scores.engage_actively || 0
                    ],
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(59, 130, 246, 1)'
                }]
            },
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 4,
                        stepSize: 1
                    }
                }
            }
        });
    }

    function createQuestionChart(index, scores) {
        const ctx = document.getElementById(`questionChart${index}`).getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Communicate Clearly', 'Engage Discussion', 'Engage Actively'],
                datasets: [{
                    label: 'Metric Scores',
                    data: [
                        scores.communicate_clearly || 0,
                        scores.engage_discussion || 0,
                        scores.engage_actively || 0
                    ],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.5)',
                        'rgba(16, 185, 129, 0.5)',
                        'rgba(245, 158, 11, 0.5)'
                    ],
                    borderColor: [
                        'rgba(59, 130, 246, 1)',
                        'rgba(16, 185, 129, 1)',
                        'rgba(245, 158, 11, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 4,
                        stepSize: 1,
                        title: {
                            display: true,
                            text: 'Score (out of 4)'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Metric Scores for Question ' + (index + 1)
                    }
                }
            }
        });
    }

    function downloadReport(report) {
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `interview_report_${report.candidate_info.name.replace(' ', '_')}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
    
    function showAlert(message) {
        // You can replace this with a better alert UI
        alert(message);
    }

    // Add source error handling
    video.getElementsByTagName('source')[0].addEventListener('error', function(e) {
        console.error('Error loading video source:', e);
    });

    // Add this helper function
    function formatMetricName(metric) {
        return metric.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
}); 