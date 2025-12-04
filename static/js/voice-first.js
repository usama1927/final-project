/* global fetch */

/**
 * Voice-First Interface for Blind Users
 * Minimal buttons - everything controlled by voice commands
 */

const VoiceFirstInterface = (() => {
    let synth = window.speechSynthesis;
    let recognition = null;
    let isListening = false;
    let isSpeaking = false;
    let currentState = 'idle'; // 'idle', 'listening', 'processing'
    let currentQuestionIndex = 0;
    let assessments = [];
    let questions = [];
    let totalQuestions = 0;

    // Initialize
    const init = () => {
        if (!synth) {
            console.warn('Speech synthesis not supported');
            return;
        }

        // Initialize speech recognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onresult = handleVoiceCommand;
            recognition.onerror = handleRecognitionError;
            recognition.onend = () => {
                isListening = false;
            };
        } else {
            console.warn('Speech recognition not supported');
        }

        // Initialize based on page
        if (document.querySelector('[data-voice-dashboard]')) {
            initDashboard();
        } else if (document.querySelector('[data-voice-assessment]')) {
            initAssessment();
        }

        // Main button handlers
        setupMainButtons();
    };

    // Speak text
    const speak = (text, callback) => {
        if (!synth) return;
        
        stopSpeaking();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.85;
        utterance.pitch = 1;
        utterance.volume = 1;
        
        utterance.onend = () => {
            isSpeaking = false;
            if (callback) callback();
        };

        utterance.onerror = () => {
            isSpeaking = false;
            if (callback) callback();
        };

        isSpeaking = true;
        synth.speak(utterance);
    };

    // Stop speaking
    const stopSpeaking = () => {
        if (synth && isSpeaking) {
            synth.cancel();
            isSpeaking = false;
        }
    };

    // Start listening for voice commands
    const startListening = () => {
        if (!recognition) {
            speak('Voice commands are not supported in this browser. Please use buttons.');
            return;
        }

        if (isListening) {
            stopListening();
            return;
        }

        if (isSpeaking) {
            stopSpeaking();
            setTimeout(() => startListening(), 500);
            return;
        }

        try {
            isListening = true;
            currentState = 'listening';
            
            // Update button text
            const mainBtn = document.querySelector('[data-voice-main-button]');
            const btnText = document.getElementById('main-button-text');
            if (btnText) {
                btnText.textContent = 'Listening... (Say "Stop" to cancel)';
            }
            if (mainBtn) {
                mainBtn.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
            }
            
            recognition.start();
            speak('Listening for your command...', () => {
                // Keep listening indicator
            });
        } catch (e) {
            isListening = false;
            speak('Could not start listening. Please try again.');
            updateButtonState();
        }
    };

    // Stop listening
    const stopListening = () => {
        if (recognition && isListening) {
            recognition.stop();
        }
        isListening = false;
        currentState = 'idle';
        updateButtonState();
    };

    // Update button visual state
    const updateButtonState = () => {
        const mainBtn = document.querySelector('[data-voice-main-button]');
        const btnText = document.getElementById('main-button-text');
        if (mainBtn && btnText) {
            if (isListening) {
                btnText.textContent = 'Listening... (Say "Stop" to cancel)';
                mainBtn.style.background = 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)';
            } else {
                btnText.textContent = 'Press to Start Voice Commands';
                mainBtn.style.background = 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)';
            }
        }
    };

    // Handle voice command
    const handleVoiceCommand = (event) => {
        const command = event.results[0][0].transcript.toLowerCase().trim();
        isListening = false;
        currentState = 'idle';
        updateButtonState();

        // Don't repeat what user said, just process
        processCommand(command);
    };

    // Handle recognition errors
    const handleRecognitionError = (event) => {
        isListening = false;
        currentState = 'idle';
        updateButtonState();
        
        if (event.error === 'no-speech') {
            speak('No speech detected. Please try again.');
        } else if (event.error === 'audio-capture') {
            speak('Microphone not found. Please check your microphone.');
        } else if (event.error !== 'aborted') {
            speak('Error listening. Please try again.');
        }
    };

    // Process voice commands
    const processCommand = (command) => {
        // Dashboard commands
        if (document.querySelector('[data-voice-dashboard]')) {
            processDashboardCommand(command);
        }
        // Assessment commands
        else if (document.querySelector('[data-voice-assessment]')) {
            processAssessmentCommand(command);
        }
    };

    // Dashboard commands
    const processDashboardCommand = (command) => {
        // "List assessments" or "Show assessments" or "What assessments"
        if (command.includes('list') || command.includes('show') || command.includes('what') || command.includes('assessments')) {
            listAssessments();
        }
        // "Open assessment [number]" or "Start assessment [number]"
        else if (command.includes('open') || command.includes('start')) {
            const match = command.match(/(\d+)/);
            if (match) {
                const num = parseInt(match[1]) - 1;
                openAssessment(num);
            } else {
                speak('Please say the assessment number. For example, say "open assessment one" or "open assessment two".');
            }
        }
        // "Assessment [number]"
        else if (command.match(/assessment\s+(\d+)/)) {
            const match = command.match(/assessment\s+(\d+)/);
            const num = parseInt(match[1]) - 1;
            openAssessment(num);
        }
        // Just a number
        else if (command.match(/^\d+$/)) {
            const num = parseInt(command) - 1;
            openAssessment(num);
        }
        else {
            speak('I did not understand. Say "list assessments" to hear available assessments, or say "open assessment" followed by the number.');
        }
    };

    // Assessment commands
    const processAssessmentCommand = (command) => {
        // Question commands
        if (command.includes('question count') || command.includes('how many questions')) {
            speak(`This assessment has ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}.`);
        }
        else if (command.includes('listen') || command.includes('hear') || command.includes('question')) {
            listenToQuestion();
        }
        else if (command.includes('repeat')) {
            listenToQuestion();
        }
        else if (command.includes('next')) {
            nextQuestion();
        }
        else if (command.includes('previous') || command.includes('back')) {
            previousQuestion();
        }
        // Answer commands
        else if (command.includes('answer') || command.includes('start recording') || command.includes('record')) {
            startAnswering();
        }
        else if (command.includes('stop') || command.includes('finish') || command.includes('done')) {
            stopAnswering();
        }
        else if (command.includes('submit')) {
            submitAnswer();
        }
        // Navigation
        else if (command.match(/question\s+(\d+)/)) {
            const match = command.match(/question\s+(\d+)/);
            const num = parseInt(match[1]) - 1;
            goToQuestion(num);
        }
        // Just a number - go to question
        else if (command.match(/^\d+$/)) {
            const num = parseInt(command) - 1;
            goToQuestion(num);
        }
        else {
            speak('I did not understand. Available commands: "listen to question", "next question", "start answering", "stop recording", "submit answer".');
        }
    };

    // Dashboard functions
    const listAssessments = () => {
        const dashboard = document.querySelector('[data-voice-dashboard]');
        assessments = Array.from(dashboard.querySelectorAll('[data-assessment-item]'));
        
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
        text += 'Say "open assessment" followed by the number to start. For example, say "open assessment one".';
        speak(text);
    };

    const openAssessment = (index) => {
        const dashboard = document.querySelector('[data-voice-dashboard]');
        assessments = Array.from(dashboard.querySelectorAll('[data-assessment-item]'));
        
        if (index >= 0 && index < assessments.length) {
            const button = assessments[index].querySelector('[data-assessment-link]');
            if (button) {
                const title = assessments[index].querySelector('[data-assessment-title]')?.textContent || 'Assessment';
                speak(`Opening ${title}. Please wait.`, () => {
                    window.location.href = button.href;
                });
            }
        } else {
            speak(`Assessment ${index + 1} not found. Please say a number between 1 and ${assessments.length}.`);
        }
    };

    // Assessment functions
    const initAssessment = () => {
        const assessment = document.querySelector('[data-voice-assessment]');
        questions = Array.from(assessment.querySelectorAll('[data-question-item]'));
        totalQuestions = questions.length;

        // Auto-announce on load
        setTimeout(() => {
            const title = assessment.querySelector('[data-assessment-title]')?.textContent || 'Assessment';
            speak(`Welcome to ${title}. This assessment has ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}. Say "listen to question" to hear the first question, or say "question count" for more information.`);
        }, 1000);
    };

    const listenToQuestion = () => {
        if (questions.length === 0) {
            speak('No questions available.');
            return;
        }

        const question = questions[currentQuestionIndex];
        if (!question) {
            speak('Question not found.');
            return;
        }

        const questionText = question.querySelector('[data-question-text]')?.textContent || '';
        const questionNum = currentQuestionIndex + 1;
        speak(`Question ${questionNum} of ${totalQuestions}. ${questionText}. Say "start answering" to record your answer.`);
    };

    const nextQuestion = () => {
        if (currentQuestionIndex < totalQuestions - 1) {
            currentQuestionIndex++;
            const question = questions[currentQuestionIndex];
            if (question) {
                question.scrollIntoView({ behavior: 'smooth', block: 'center' });
                question.focus();
                setTimeout(() => listenToQuestion(), 300);
            }
        } else {
            speak('This is the last question. You have completed all questions.');
        }
    };

    const previousQuestion = () => {
        if (currentQuestionIndex > 0) {
            currentQuestionIndex--;
            const question = questions[currentQuestionIndex];
            if (question) {
                question.scrollIntoView({ behavior: 'smooth', block: 'center' });
                question.focus();
                setTimeout(() => listenToQuestion(), 300);
            }
        } else {
            speak('This is the first question.');
        }
    };

    const goToQuestion = (index) => {
        if (index >= 0 && index < totalQuestions) {
            currentQuestionIndex = index;
            const question = questions[currentQuestionIndex];
            if (question) {
                question.scrollIntoView({ behavior: 'smooth', block: 'center' });
                question.focus();
                setTimeout(() => listenToQuestion(), 300);
            }
        } else {
            speak(`Question ${index + 1} not found. Please say a number between 1 and ${totalQuestions}.`);
        }
    };

    const startAnswering = () => {
        const question = questions[currentQuestionIndex];
        if (!question) {
            speak('No question available.');
            return;
        }

        // Set active endpoint for audio module
        const endpoint = question.getAttribute('data-asr-endpoint');
        if (endpoint && window.AudioModule && window.AudioModule.setEndpoint) {
            // Set the question element as active endpoint
            window.AudioModule.setEndpoint(question);
            window.currentQuestionEndpoint = question;
        }

        speak('Starting recording. Speak your answer clearly. Say "stop recording" when you are finished.');
        
        // Start recording after a short delay
        setTimeout(() => {
            const startBtn = document.querySelector('[data-audio-control="start"]');
            if (startBtn) {
                startBtn.click();
            } else {
                // Fallback: start recording directly
                if (window.AudioModule && window.AudioModule.startRecording) {
                    window.AudioModule.startRecording();
                }
            }
        }, 800);
    };

    const stopAnswering = () => {
        speak('Stopping recording. Processing your answer.');
        
        const stopBtn = document.querySelector('[data-audio-control="stop"]');
        if (stopBtn) {
            stopBtn.click();
        }
    };

    const submitAnswer = () => {
        const question = questions[currentQuestionIndex];
        if (!question) {
            speak('No question available.');
            return;
        }

        const form = question.querySelector('[data-question-form]');
        if (form) {
            const textarea = form.querySelector('textarea');
            if (!textarea || !textarea.value.trim()) {
                speak('No answer to submit. Please record an answer first by saying "start answering".');
                return;
            }

            speak('Submitting your answer. Please wait.');
            
            // Submit form
            const formData = new FormData(form);
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            }).then((response) => {
                if (response.ok) {
                    speak('Answer submitted successfully. Say "next question" to continue, or "listen to question" to hear the next question.');
                    // Reload page to show updated state
                    setTimeout(() => window.location.reload(), 2000);
                } else {
                    speak('Error submitting answer. Please try again.');
                }
            }).catch(() => {
                speak('Error submitting answer. Please try again.');
            });
        } else {
            speak('Could not find answer form.');
        }
    };

    // Get CSRF token
    const getCsrfToken = () => {
        const value = document.cookie
            .split('; ')
            .find((row) => row.startsWith('csrftoken='));
        return value ? value.split('=')[1] : '';
    };

    // Setup main buttons
    const setupMainButtons = () => {
        // Main action button (Listen/Start)
        const mainBtn = document.querySelector('[data-voice-main-button]');
        if (mainBtn) {
            mainBtn.addEventListener('click', () => {
                if (isListening) {
                    stopListening();
                } else {
                    startListening();
                }
            });
        }

        // Stop/Cancel button
        const stopBtn = document.querySelector('[data-voice-stop-button]');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                stopListening();
                stopSpeaking();
            });
        }
    };

    // Listen for ASR results
    document.addEventListener('asr-result', (event) => {
        if (event.detail && event.detail.transcription) {
            const transcription = event.detail.transcription;
            if (transcription.trim()) {
                speak(`Your answer has been transcribed: ${transcription.substring(0, 100)}${transcription.length > 100 ? '...' : ''}. Say "submit answer" to save it, or say "start answering" to record again.`);
            } else {
                speak('Recording processed, but no text was detected. Say "start answering" to try again.');
            }
        }
    });

    // Public API
    return {
        init,
        speak,
        startListening,
        stopListening
    };
})();

// Initialize
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        VoiceFirstInterface.init();
    });
}

if (typeof window !== 'undefined') {
    window.VoiceFirstInterface = VoiceFirstInterface;
}

