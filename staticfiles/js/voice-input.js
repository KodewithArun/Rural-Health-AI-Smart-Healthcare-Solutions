// Voice Input Handler
class VoiceInputHandler {
  constructor(inputElement, buttonElement) {
    if (!inputElement || !buttonElement) {
      console.error('VoiceInputHandler: Missing required elements');
      return;
    }
    
    this.input = inputElement;
    this.button = buttonElement;
    this.recognition = null;
    this.isListening = false;
    this.isInitialized = false;
    
    this.init();
    if (this.isInitialized) {
      this.setupEventListeners();
    }
  }

  init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('Speech Recognition API not supported');
      this.button.style.display = 'none';
      return;
    }
    
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';
    this.recognition.maxAlternatives = 1;
    
    this.recognition.onstart = this.handleStart.bind(this);
    this.recognition.onresult = this.handleResult.bind(this);
    this.recognition.onend = this.handleEnd.bind(this);
    this.recognition.onerror = this.handleError.bind(this);
    
    this.isInitialized = true;
  }

  handleStart() {
    this.isListening = true;
    this.button.classList.add('listening');
    this.button.setAttribute('aria-label', 'Listening... Release to stop');
    this.input.placeholder = '🎤 Listening...';
  }

  handleResult(event) {
    if (event.results && event.results.length > 0) {
      const transcript = event.results[0][0].transcript.trim();
      if (transcript) {
        this.input.value = transcript;
        this.input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  }

  handleEnd() {
    this.isListening = false;
    this.button.classList.remove('listening');
    this.button.setAttribute('aria-label', 'Hold to speak');
    this.input.placeholder = 'Type your message or hold the microphone...';
  }

  handleError(event) {
    console.error('Speech recognition error:', event.error);
    
    this.isListening = false;
    this.button.classList.remove('listening');
    this.button.setAttribute('aria-label', 'Hold to speak');
    this.input.placeholder = 'Type your message or hold the microphone...';
    
    // User-friendly error messages
    const errorMessages = {
      'not-allowed': 'Microphone access denied. Please enable it in your browser settings.',
      'no-speech': 'No speech detected. Please try again.',
      'network': 'Network error. Please check your connection.',
      'aborted': 'Speech recognition aborted.'
    };
    
    if (errorMessages[event.error] && event.error !== 'aborted' && event.error !== 'no-speech') {
      this.showError(errorMessages[event.error]);
    }
  }

  showError(message) {
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.className = 'voice-error-toast';
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      bottom: 100px;
      left: 50%;
      transform: translateX(-50%);
      background: #ef4444;
      color: white;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 14px;
      z-index: 9999;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      animation: slideUp 0.3s ease-out;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  setupEventListeners() {
    // Prevent double-initialization
    if (this.button.dataset.voiceInitialized) return;
    this.button.dataset.voiceInitialized = 'true';
    
    // Mouse events
    this.button.addEventListener('mousedown', this.handleMouseDown.bind(this));
    this.button.addEventListener('mouseup', this.handleMouseUp.bind(this));
    this.button.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
    
    // Touch events for mobile
    this.button.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
    this.button.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
    this.button.addEventListener('touchcancel', this.handleTouchCancel.bind(this));
  }

  handleMouseDown(e) {
    e.preventDefault();
    this.start();
  }

  handleMouseUp(e) {
    e.preventDefault();
    this.stop();
  }

  handleMouseLeave() {
    if (this.isListening) {
      this.stop();
    }
  }

  handleTouchStart(e) {
    e.preventDefault();
    this.start();
  }

  handleTouchEnd(e) {
    e.preventDefault();
    this.stop();
  }

  handleTouchCancel() {
    if (this.isListening) {
      this.stop();
    }
  }

  start() {
    if (!this.recognition || this.isListening) return;
    
    try {
      this.recognition.start();
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      // Recognition might already be running
      if (error.name !== 'InvalidStateError') {
        this.handleEnd();
      }
    }
  }

  stop() {
    if (!this.recognition || !this.isListening) return;
    
    try {
      this.recognition.stop();
    } catch (error) {
      console.error('Failed to stop speech recognition:', error);
      this.handleEnd();
    }
  }

  destroy() {
    if (this.recognition) {
      this.stop();
      this.recognition.onstart = null;
      this.recognition.onresult = null;
      this.recognition.onend = null;
      this.recognition.onerror = null;
      this.recognition = null;
    }
    
    if (this.button) {
      delete this.button.dataset.voiceInitialized;
    }
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const messageInput = document.getElementById('message-input');
  const voiceBtn = document.getElementById('voice-btn');
  
  if (messageInput && voiceBtn) {
    const voiceHandler = new VoiceInputHandler(messageInput, voiceBtn);
    
    // Store instance for potential cleanup
    window.voiceInputHandler = voiceHandler;
  }
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports = VoiceInputHandler;
}
