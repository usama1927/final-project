/* global fetch */

const AudioModule = (() => {
    let mediaRecorder;
    let recordedChunks = [];
    let statusRegion;
    let activeEndpoint;
    let activeTextarea;

    const init = () => {
        statusRegion = document.querySelector('[data-audio-status]');
        document.querySelectorAll('[data-audio-control]').forEach((button) => {
            button.addEventListener('click', handleAction);
        });
        document.querySelectorAll('.assessment-card').forEach((card) => {
            card.addEventListener('focusin', () => setEndpoint(card));
            card.addEventListener('mouseenter', () => setEndpoint(card));
        });
        if (!activeEndpoint) {
            const first = document.querySelector('.assessment-card');
            setEndpoint(first);
        }
        document.addEventListener('asr-result', handleAsrResult);
    };

    const handleAction = async (event) => {
        const button = event.currentTarget;
        const action = button.dataset.audioControl;
        
        // Set endpoint based on the button's parent question card
        const questionCard = button.closest('[data-asr-endpoint]');
        if (questionCard) {
            setEndpoint(questionCard);
        }
        
        if (action === 'start') {
            await startRecording();
        } else if (action === 'stop') {
            stopRecording();
        } else {
            updateStatus(`Command received: ${action}`);
        }
    };

    const startRecording = async () => {
        if (!navigator.mediaDevices) {
            updateStatus('Microphone access is not supported in this browser.');
            return;
        }
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = [];
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        mediaRecorder.onstop = uploadRecording;
        mediaRecorder.start();
        updateStatus('Recording in progress. Press Stop when finished.');
    };

    const stopRecording = () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            updateStatus('Processing response…');
        }
    };

    const uploadRecording = async () => {
        const audioBlob = new Blob(recordedChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'response.webm');
        if (!activeEndpoint) {
            return;
        }
        const response = await fetch(activeEndpoint.dataset.asrEndpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: formData,
        });
        const data = await response.json();
        handleAsrResult({ detail: data });
        updateStatus('Transcription complete.');
    };

    const updateStatus = (message) => {
        if (statusRegion) {
            statusRegion.textContent = message;
        }
    };

    const setEndpoint = (element) => {
        if (element?.dataset.asrEndpoint) {
            activeEndpoint = element;
            // Find textarea - could be in form or directly in element
            activeTextarea = element.querySelector('textarea') || 
                           element.querySelector('form textarea') ||
                           element.querySelector('[data-question-form] textarea');
        }
    };

    const handleAsrResult = (event) => {
        if (!event.detail || !activeTextarea) {
            return;
        }
        activeTextarea.value = event.detail.transcription || '';
    };

    const getCsrfToken = () => {
        const value = document.cookie
            .split('; ')
            .find((row) => row.startsWith('csrftoken='));
        return value ? value.split('=')[1] : '';
    };

    if (typeof document !== 'undefined') {
        document.addEventListener('DOMContentLoaded', init);
    }

    return {
        init,
        setEndpoint,
        startRecording,
        stopRecording
    };
})();

if (typeof window !== 'undefined') {
    window.AudioModule = AudioModule;
}

