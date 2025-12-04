/* global fetch */

/**
 * Keyboard-First Interface for Blind Users
 * All navigation via keyboard shortcuts - no UI buttons needed
 * Voice commands also available as alternative
 */

// Prevent double-loading
if (typeof window.KeyboardFirstInterface !== 'undefined') {
    console.warn('KeyboardFirstInterface already loaded');
} else {

var KeyboardFirstInterface = (() => {
    let synth = window.speechSynthesis;
    let recognition = null;
    let isListening = false;
    let isSpeaking = false;
    let currentQuestionIndex = 0;
    let assessments = [];
    let questions = [];
    let totalQuestions = 0;
    let hasAnnounced = false; // Track if we've announced on this page

    // Initialize
    const init = () => {
        if (!synth) {
            console.warn('Speech synthesis not supported');
            return;
        }

        // Initialize speech recognition (optional, for voice commands)
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            recognition.onresult = handleVoiceCommand;
            recognition.onerror = handleRecognitionError;
            recognition.onend = () => { isListening = false; };
        }

        // Initialize based on page
        if (document.querySelector('[data-keyboard-dashboard]')) {
            initDashboard();
        } else if (document.querySelector('[data-keyboard-assessment]')) {
            initAssessment();
        }

        // Setup keyboard shortcuts
        setupKeyboardShortcuts();

        // Browsers block speech synthesis until user interaction
        // Set up handlers for first user interaction to announce
        const announceOnInteraction = () => {
            if (!hasAnnounced && !isSpeaking) {
                try {
                    announcePageLoad();
                    hasAnnounced = true;
                } catch (e) {
                    console.warn('Announcement failed:', e);
                }
            }
        };
        
        // Listen for any user interaction (browser security requirement)
        // Only announce on first interaction, not automatically
        document.addEventListener('click', announceOnInteraction, { once: true });
        document.addEventListener('keydown', announceOnInteraction, { once: true });
        document.addEventListener('touchstart', announceOnInteraction, { once: true });
    };

    // Speak text
    const speak = (text, callback) => {
        if (!synth) {
            console.warn('Speech synthesis not available');
            return;
        }
        
        // Stop any current speech
        stopSpeaking();
        
        try {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.85;
            utterance.pitch = 1;
            utterance.volume = 1;
            
            utterance.onend = () => {
                isSpeaking = false;
                if (callback) callback();
            };

            utterance.onerror = (e) => {
                // Don't log 'not-allowed' errors as they're expected before user interaction
                if (e.error !== 'not-allowed') {
                    console.error('Speech synthesis error:', e.error);
                }
                isSpeaking = false;
                if (callback) callback();
            };

            isSpeaking = true;
            synth.speak(utterance);
        } catch (e) {
            console.error('Failed to speak:', e);
            isSpeaking = false;
            if (callback) callback();
        }
    };

    // Stop speaking
    const stopSpeaking = () => {
        if (synth && isSpeaking) {
            synth.cancel();
            isSpeaking = false;
        }
    };

    // Start voice listening (optional)
    const startVoiceListening = () => {
        if (!recognition) {
            speak('Voice commands not available. Use keyboard shortcuts instead.');
            return;
        }

        if (isListening) {
            stopVoiceListening();
            return;
        }

        if (isSpeaking) {
            stopSpeaking();
            setTimeout(() => startVoiceListening(), 500);
            return;
        }

        try {
            isListening = true;
            recognition.start();
            speak('Listening for voice command. Say your command now.');
        } catch (e) {
            isListening = false;
            speak('Could not start listening.');
        }
    };

    // Stop voice listening
    const stopVoiceListening = () => {
        if (recognition && isListening) {
            recognition.stop();
        }
        isListening = false;
    };

    // Handle voice command (optional feature)
    const handleVoiceCommand = (event) => {
        const command = event.results[0][0].transcript.toLowerCase().trim();
        isListening = false;
        processCommand(command);
    };

    const handleRecognitionError = (event) => {
        isListening = false;
        if (event.error !== 'aborted' && event.error !== 'no-speech') {
            speak('Voice recognition error. Use keyboard shortcuts instead.');
        }
    };

    // Process commands (works for both keyboard and voice)
    const processCommand = (command) => {
        if (document.querySelector('[data-keyboard-dashboard]')) {
            processDashboardCommand(command);
        } else if (document.querySelector('[data-keyboard-assessment]')) {
            processAssessmentCommand(command);
        }
    };

    // Dashboard commands
    const processDashboardCommand = (command) => {
        if (command.includes('list') || command.includes('show') || command.includes('assessments')) {
            listAssessments();
        } else if (command.includes('open') || command.includes('start')) {
            const match = command.match(/(\d+)/);
            if (match) openAssessment(parseInt(match[1]) - 1);
            else speak('Say the assessment number. For example, "open assessment one".');
        } else if (command.match(/assessment\s+(\d+)/)) {
            const match = command.match(/assessment\s+(\d+)/);
            openAssessment(parseInt(match[1]) - 1);
        } else if (command.match(/^\d+$/)) {
            openAssessment(parseInt(command) - 1);
        } else {
            speak('Available commands: Press L to list assessments, or press number keys 1-9 to open an assessment.');
        }
    };

    // Assessment commands
    const processAssessmentCommand = (command) => {
        if (command.includes('question count') || command.includes('how many')) {
            speak(`This assessment has ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}.`);
        } else if (command.includes('listen') || command.includes('hear') || command.includes('question')) {
            listenToQuestion();
        } else if (command.includes('repeat')) {
            listenToQuestion();
        } else if (command.includes('next')) {
            nextQuestion();
        } else if (command.includes('previous') || command.includes('back')) {
            previousQuestion();
        } else if (command.includes('answer') || command.includes('record')) {
            startAnswering();
        } else if (command.includes('stop') || command.includes('finish')) {
            stopAnswering();
        } else if (command.includes('submit')) {
            submitAnswer();
        } else if (command.match(/question\s+(\d+)/)) {
            const match = command.match(/question\s+(\d+)/);
            goToQuestion(parseInt(match[1]) - 1);
        } else if (command.match(/^\d+$/)) {
            goToQuestion(parseInt(command) - 1);
        } else {
            speak('Available commands: Press Q to hear question, N for next, P for previous, R to record, S to stop, Enter to submit.');
        }
    };

    // Setup keyboard shortcuts
    const setupKeyboardShortcuts = () => {
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in input/textarea
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            // Stop speaking with Escape
            if (e.key === 'Escape') {
                if (isSpeaking) {
                    e.preventDefault();
                    stopSpeaking();
                }
                if (isListening) {
                    e.preventDefault();
                    stopVoiceListening();
                }
                return;
            }

            // Dashboard shortcuts
            if (document.querySelector('[data-keyboard-dashboard]')) {
                handleDashboardShortcuts(e);
            }
            // Assessment shortcuts
            else if (document.querySelector('[data-keyboard-assessment]')) {
                handleAssessmentShortcuts(e);
            }
        });
    };

    // Dashboard keyboard shortcuts
    const handleDashboardShortcuts = (e) => {
        // Ensure we've announced (in case auto-announce was blocked)
        if (!hasAnnounced) {
            announcePageLoad();
            hasAnnounced = true;
        }
        
        // L - List assessments
        if (e.key === 'L' || e.key === 'l') {
            e.preventDefault();
            listAssessments();
        }
        // Number keys 1-9 - Open assessment
        else if (e.key >= '1' && e.key <= '9') {
            e.preventDefault();
            openAssessment(parseInt(e.key) - 1);
        }
        // V - Voice mode (optional)
        else if (e.key === 'V' || e.key === 'v') {
            e.preventDefault();
            startVoiceListening();
        }
        // H - Help
        else if (e.key === 'H' || e.key === 'h') {
            e.preventDefault();
            // Test speech synthesis first
            if (!synth) {
                console.error('Speech synthesis not available');
                alert('Speech synthesis is not supported in this browser.');
                return;
            }
            speak('Keyboard shortcuts: Press L to list assessments, press number keys 1 through 9 to open an assessment, press V for voice commands, press Escape to stop speaking.');
        }
    };

    // Assessment keyboard shortcuts
    const handleAssessmentShortcuts = (e) => {
        // Ensure we've announced (in case auto-announce was blocked)
        if (!hasAnnounced) {
            announcePageLoad();
            hasAnnounced = true;
        }
        
        // Q - Listen to question
        if (e.key === 'Q' || e.key === 'q') {
            e.preventDefault();
            listenToQuestion();
        }
        // N - Next question
        else if (e.key === 'N' || e.key === 'n') {
            e.preventDefault();
            nextQuestion();
        }
        // P - Previous question
        else if (e.key === 'P' || e.key === 'p') {
            e.preventDefault();
            previousQuestion();
        }
        // R - Record answer
        else if (e.key === 'R' || e.key === 'r') {
            e.preventDefault();
            startAnswering();
        }
        // S - Stop recording
        else if (e.key === 'S' || e.key === 's') {
            e.preventDefault();
            stopAnswering();
        }
        // Enter - Submit answer
        else if (e.key === 'Enter') {
            e.preventDefault();
            submitAnswer();
        }
        // Number keys 1-9 - Go to question
        else if (e.key >= '1' && e.key <= '9') {
            e.preventDefault();
            goToQuestion(parseInt(e.key) - 1);
        }
        // C - Question count
        else if (e.key === 'C' || e.key === 'c') {
            e.preventDefault();
            speak(`This assessment has ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}.`);
        }
        // V - Voice mode (optional)
        else if (e.key === 'V' || e.key === 'v') {
            e.preventDefault();
            startVoiceListening();
        }
        // F - Finalize/Submit assessment
        else if (e.key === 'F' || e.key === 'f') {
            e.preventDefault();
            submitAssessment();
        }
        // H - Help
        else if (e.key === 'H' || e.key === 'h') {
            e.preventDefault();
            // Test speech synthesis first
            if (!synth) {
                console.error('Speech synthesis not available');
                alert('Speech synthesis is not supported in this browser.');
                return;
            }
            speak('Keyboard shortcuts: Q to hear question, N for next, P for previous, R to record answer, S to stop recording, Enter to submit answer, F to finalize assessment, number keys 1-9 to jump to question, C for question count, V for voice commands, Escape to stop speaking.');
        }
    };

    // Dashboard functions
    const listAssessments = () => {
        const dashboard = document.querySelector('[data-keyboard-dashboard]');
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
        text += `Press number keys 1 through ${Math.min(assessments.length, 9)} to open an assessment.`;
        speak(text);
    };

    const openAssessment = (index) => {
        const dashboard = document.querySelector('[data-keyboard-dashboard]');
        assessments = Array.from(dashboard.querySelectorAll('[data-assessment-item]'));
        
        if (index >= 0 && index < assessments.length) {
            const link = assessments[index].querySelector('[data-assessment-link]');
            if (link) {
                const title = assessments[index].querySelector('[data-assessment-title]')?.textContent || 'Assessment';
                speak(`Opening ${title}. Please wait.`, () => {
                    window.location.href = link.href;
                });
            }
        } else {
            speak(`Assessment ${index + 1} not found. Press L to list available assessments.`);
        }
    };

    // Dashboard initialization
    const initDashboard = () => {
        // Dashboard-specific initialization if needed
        // Currently handled by keyboard shortcuts
    };

    // Assessment initialization
    const initAssessment = () => {
        // Questions can be anywhere in the document, not just in data-keyboard-assessment
        // They're in a separate section with data-question-item attribute
        questions = Array.from(document.querySelectorAll('[data-question-item]'));
        totalQuestions = questions.length;
        
        // Debug logging
        if (totalQuestions === 0) {
            console.warn('No questions found in DOM. Check if response_forms is empty in template.');
        } else {
            console.log(`Found ${totalQuestions} question(s) in DOM`);
        }
    };

    const announcePageLoad = () => {
        // Check if speech synthesis is available and not already speaking
        if (!synth || isSpeaking || hasAnnounced) {
            return;
        }
        
        // Re-initialize questions count in case DOM wasn't ready when initAssessment ran
        if (document.querySelector('[data-keyboard-assessment]')) {
            questions = Array.from(document.querySelectorAll('[data-question-item]'));
            totalQuestions = questions.length;
            console.log(`Announce: Found ${totalQuestions} question(s) in DOM`);
        }
        
        if (document.querySelector('[data-keyboard-dashboard]')) {
            speak('Dashboard loaded. Press L to list assessments, or press H for help with keyboard shortcuts.');
        } else if (document.querySelector('[data-keyboard-assessment]')) {
            const assessment = document.querySelector('[data-keyboard-assessment]');
            const title = assessment.querySelector('[data-assessment-title]')?.textContent || 'Assessment';
            if (totalQuestions === 0) {
                speak(`${title} loaded. No questions found. Please contact your teacher.`);
            } else {
                speak(`${title} loaded. This assessment has ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}. Press Q to hear the first question, or press H for help with keyboard shortcuts.`);
            }
        }
        
        hasAnnounced = true;
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
        speak(`Question ${questionNum} of ${totalQuestions}. ${questionText}. Press R to start recording your answer.`);
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
            speak(`Question ${index + 1} not found. This assessment has ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}.`);
        }
    };

    const startAnswering = () => {
        const question = questions[currentQuestionIndex];
        if (!question) {
            speak('No question available.');
            return;
        }

        // Set active endpoint
        const endpoint = question.getAttribute('data-asr-endpoint');
        if (endpoint && window.AudioModule && window.AudioModule.setEndpoint) {
            window.AudioModule.setEndpoint(question);
        }

        speak('Starting recording. Speak your answer clearly. Press S to stop recording when finished.');
        
        setTimeout(() => {
            const startBtn = document.querySelector('[data-audio-control="start"]');
            if (startBtn) {
                startBtn.click();
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
                speak('No answer to submit. Press R to record an answer first.');
                return;
            }

            speak('Submitting your answer. Please wait.');
            
            const formData = new FormData(form);
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            }).then((response) => {
                if (response.ok) {
                    speak('Answer submitted successfully. Press N for next question, or press Q to hear the current question again.');
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

    const submitAssessment = () => {
        // Find the submit assessment form
        const submitForm = document.querySelector('form[action*="submit"]');
        if (!submitForm) {
            speak('Submit assessment form not found. Make sure you have answered all questions.');
            return;
        }

        speak('Finalizing and submitting your assessment. Please wait.');
        
        const formData = new FormData(submitForm);
        fetch(submitForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        }).then((response) => {
            if (response.ok) {
                speak('Assessment submitted successfully! You will be redirected to your dashboard.');
                setTimeout(() => {
                    window.location.href = '/assessments/student/dashboard/';
                }, 2000);
            } else {
                speak('Error submitting assessment. Please try again.');
            }
        }).catch(() => {
            speak('Error submitting assessment. Please try again.');
        });
    };

    // Get CSRF token
    const getCsrfToken = () => {
        const value = document.cookie
            .split('; ')
            .find((row) => row.startsWith('csrftoken='));
        return value ? value.split('=')[1] : '';
    };

    // Listen for ASR results
    document.addEventListener('asr-result', (event) => {
        if (event.detail && event.detail.transcription) {
            const transcription = event.detail.transcription;
            if (transcription.trim()) {
                const preview = transcription.substring(0, 100);
                speak(`Your answer has been transcribed: ${preview}${transcription.length > 100 ? '...' : ''}. Press Enter to submit, or press R to record again.`);
            } else {
                speak('Recording processed, but no text was detected. Press R to try again.');
            }
        }
    });

    // Public API
    return {
        init,
        speak,
        stopSpeaking
    };
})();

// Initialize
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            KeyboardFirstInterface.init();
        });
    } else {
        // DOM already loaded
        KeyboardFirstInterface.init();
    }
}

if (typeof window !== 'undefined') {
    window.KeyboardFirstInterface = KeyboardFirstInterface;
    
    // Debug helper - test speech synthesis
    window.testSpeech = () => {
        if (window.KeyboardFirstInterface) {
            window.KeyboardFirstInterface.speak('Speech synthesis test. If you can hear this, speech is working correctly.');
        } else {
            console.error('KeyboardFirstInterface not available');
        }
    };
}

} // End of double-loading prevention check

