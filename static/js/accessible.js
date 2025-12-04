/* global fetch */

/**
 * Accessible Audio-First Interface for Blind Users
 * Provides button-based navigation with text-to-speech feedback
 */

const AccessibleInterface = (() => {
    let synth = window.speechSynthesis;
    let currentUtterance = null;
    let isSpeaking = false;

    // Initialize the accessible interface
    const init = () => {
        // Check if browser supports speech synthesis
        if (!synth) {
            console.warn('Speech synthesis not supported');
            return;
        }

        // Initialize dashboard if on dashboard page
        if (document.querySelector('[data-accessible-dashboard]')) {
            initDashboard();
        }

        // Initialize assessment session if on assessment page
        if (document.querySelector('[data-accessible-assessment]')) {
            initAssessment();
        }

        // Add keyboard shortcuts
        setupKeyboardShortcuts();
    };

    // Speak text using Web Speech API
    const speak = (text, priority = 'polite') => {
        if (!synth) return;

        // Stop any current speech
        stopSpeaking();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9; // Slightly slower for clarity
        utterance.pitch = 1;
        utterance.volume = 1;
        
        utterance.onend = () => {
            isSpeaking = false;
        };

        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event);
            isSpeaking = false;
        };

        currentUtterance = utterance;
        isSpeaking = true;
        synth.speak(utterance);
    };

    // Stop current speech
    const stopSpeaking = () => {
        if (synth && isSpeaking) {
            synth.cancel();
            isSpeaking = false;
        }
    };

    // Initialize dashboard functionality
    const initDashboard = () => {
        const dashboard = document.querySelector('[data-accessible-dashboard]');
        if (!dashboard) return;

        // Button to list all assessments
        const listAssessmentsBtn = document.querySelector('[data-action="list-assessments"]');
        if (listAssessmentsBtn) {
            listAssessmentsBtn.addEventListener('click', () => {
                const assessments = dashboard.querySelectorAll('[data-assessment-item]');
                if (assessments.length === 0) {
                    speak('No assessments available at this time.');
                    return;
                }

                let text = `You have ${assessments.length} assessment${assessments.length > 1 ? 's' : ''} available. `;
                assessments.forEach((item, index) => {
                    const title = item.querySelector('[data-assessment-title]')?.textContent || 'Untitled';
                    const subject = item.querySelector('[data-assessment-subject]')?.textContent || '';
                    text += `Assessment ${index + 1}: ${title}. ${subject ? 'Subject: ' + subject + '. ' : ''}`;
                });
                text += 'Press the button next to any assessment to open it.';
                speak(text);
            });
        }

        // Make assessment buttons speak when focused
        dashboard.querySelectorAll('[data-assessment-item]').forEach((item, index) => {
            const button = item.querySelector('[data-action="open-assessment"]');
            const title = item.querySelector('[data-assessment-title]')?.textContent || 'Untitled';
            const subject = item.querySelector('[data-assessment-subject]')?.textContent || '';

            if (button) {
                // Speak on focus
                button.addEventListener('focus', () => {
                    speak(`Assessment ${index + 1}: ${title}. ${subject ? 'Subject: ' + subject : ''}`);
                });

                // Speak on click before navigation
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    speak(`Opening ${title}. Please wait.`);
                    setTimeout(() => {
                        window.location.href = button.href;
                    }, 1000);
                });
            }
        });
    };

    // Initialize assessment session functionality
    const initAssessment = () => {
        const assessment = document.querySelector('[data-accessible-assessment]');
        if (!assessment) return;

        const questions = assessment.querySelectorAll('[data-question-item]');
        const totalQuestions = questions.length;
        let currentQuestionIndex = 0;

        // Button to hear question count
        const questionCountBtn = document.querySelector('[data-action="question-count"]');
        if (questionCountBtn) {
            questionCountBtn.addEventListener('click', () => {
                speak(`This assessment has ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}.`);
            });
        }

        // Button to listen to current question
        const listenQuestionBtn = document.querySelector('[data-action="listen-question"]');
        if (listenQuestionBtn) {
            listenQuestionBtn.addEventListener('click', () => {
                const currentQuestion = questions[currentQuestionIndex];
                if (!currentQuestion) {
                    speak('No question available.');
                    return;
                }

                const questionText = currentQuestion.querySelector('[data-question-text]')?.textContent || '';
                const questionNum = currentQuestionIndex + 1;
                speak(`Question ${questionNum} of ${totalQuestions}. ${questionText}`);
            });
        }

        // Button to answer (start recording)
        const answerBtn = document.querySelector('[data-action="answer-question"]');
        if (answerBtn) {
            answerBtn.addEventListener('click', () => {
                // Find the current question's card
                const currentQuestion = questions[currentQuestionIndex];
                if (currentQuestion) {
                    // Set the active endpoint for the current question
                    const endpoint = currentQuestion.getAttribute('data-asr-endpoint');
                    if (endpoint) {
                        // Update the active endpoint in the audio module if it exists
                        if (window.AudioModule && window.AudioModule.setActiveEndpoint) {
                            window.AudioModule.setActiveEndpoint(currentQuestion);
                        }
                    }
                }
                
                speak('Starting recording. Speak your answer clearly, then press the stop recording button when finished.');
                // Trigger the existing audio recording
                const startBtn = document.querySelector('[data-audio-control="start"]');
                if (startBtn) {
                    startBtn.click();
                }
            });
        }

        // Button to stop recording
        const stopBtn = document.querySelector('[data-action="stop-recording"]');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                speak('Stopping recording. Processing your answer.');
                const stopAudioBtn = document.querySelector('[data-audio-control="stop"]');
                if (stopAudioBtn) {
                    stopAudioBtn.click();
                }
            });
        }

        // Button for next question
        const nextBtn = document.querySelector('[data-action="next-question"]');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (currentQuestionIndex < totalQuestions - 1) {
                    currentQuestionIndex++;
                    const currentQuestion = questions[currentQuestionIndex];
                    if (currentQuestion) {
                        // Scroll to question
                        currentQuestion.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        currentQuestion.focus();
                        
                        const questionText = currentQuestion.querySelector('[data-question-text]')?.textContent || '';
                        const questionNum = currentQuestionIndex + 1;
                        speak(`Question ${questionNum} of ${totalQuestions}. ${questionText}`);
                    }
                } else {
                    speak('This is the last question. You have completed all questions.');
                }
            });
        }

        // Button for previous question
        const prevBtn = document.querySelector('[data-action="prev-question"]');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (currentQuestionIndex > 0) {
                    currentQuestionIndex--;
                    const currentQuestion = questions[currentQuestionIndex];
                    if (currentQuestion) {
                        currentQuestion.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        currentQuestion.focus();
                        
                        const questionText = currentQuestion.querySelector('[data-question-text]')?.textContent || '';
                        const questionNum = currentQuestionIndex + 1;
                        speak(`Question ${questionNum} of ${totalQuestions}. ${questionText}`);
                    }
                } else {
                    speak('This is the first question.');
                }
            });
        }

        // Button to repeat current question
        const repeatBtn = document.querySelector('[data-action="repeat-question"]');
        if (repeatBtn) {
            repeatBtn.addEventListener('click', () => {
                const currentQuestion = questions[currentQuestionIndex];
                if (currentQuestion) {
                    const questionText = currentQuestion.querySelector('[data-question-text]')?.textContent || '';
                    const questionNum = currentQuestionIndex + 1;
                    speak(`Question ${questionNum}. ${questionText}`);
                }
            });
        }

        // Button to submit answer
        const submitBtn = document.querySelector('[data-action="submit-answer"]');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                speak('Submitting your answer. Please wait.');
            });
        }

        // Listen for ASR results to provide feedback
        document.addEventListener('asr-result', (event) => {
            if (event.detail && event.detail.transcription) {
                const transcription = event.detail.transcription;
                if (transcription.trim()) {
                    speak(`Your answer has been transcribed: ${transcription}. Press submit to save your answer.`);
                } else {
                    speak('Recording processed, but no text was detected. Please try again.');
                }
            }
        });

        // Listen for form submissions
        assessment.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', () => {
                speak('Submitting answer. Please wait for confirmation.');
            });
        });

        // Auto-announce when page loads
        setTimeout(() => {
            const assessmentTitle = assessment.querySelector('[data-assessment-title]')?.textContent || 'Assessment';
            speak(`Welcome to ${assessmentTitle}. This assessment has ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}. Press the question count button to hear the total, or press listen to question to hear the first question.`);
        }, 500);
    };

    // Setup keyboard shortcuts
    const setupKeyboardShortcuts = () => {
        document.addEventListener('keydown', (e) => {
            // Space to stop speaking
            if (e.key === ' ' && e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                if (isSpeaking) {
                    e.preventDefault();
                    stopSpeaking();
                }
            }
        });
    };

    // Public API
    return {
        init,
        speak,
        stopSpeaking
    };
})();

// Initialize when DOM is ready
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        AccessibleInterface.init();
    });
}

if (typeof window !== 'undefined') {
    window.AccessibleInterface = AccessibleInterface;
}

