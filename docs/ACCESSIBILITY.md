# Keyboard-First Interface for Blind Users

This document describes the keyboard-first interface designed specifically for blind and visually impaired users. The interface uses **NO UI buttons** - everything is controlled by **keyboard shortcuts**. Voice commands are available as an optional alternative.

## Design Philosophy

**Zero UI Buttons, Full Keyboard Control**

- **NO buttons** on screen - everything via keyboard
- All navigation through **keyboard shortcuts**
- Voice commands available as optional alternative
- No need to find or click any UI elements
- Perfect for blind users who use keyboards naturally

## Features

### Dashboard (Assessment List)

**Keyboard Shortcuts:**
- **L** - List all assessments (hears all available assessments)
- **1-9** - Open assessment by number (e.g., press 1 for first assessment)
- **V** - Voice commands mode (optional alternative)
- **H** - Help (hears all available shortcuts)
- **Escape** - Stop speaking

**No Buttons Required!** Just press keys on your keyboard.

### Assessment Session

**Keyboard Shortcuts:**
- **Q** - Listen to current question
- **N** - Next question (automatically speaks the question)
- **P** - Previous question (automatically speaks the question)
- **1-9** - Jump to question number (e.g., press 3 for question 3)
- **R** - Start recording answer
- **S** - Stop recording (processes answer)
- **Enter** - Submit answer
- **C** - Question count (hears total number of questions)
- **V** - Voice commands mode (optional alternative)
- **H** - Help (hears all available shortcuts)
- **Escape** - Stop speaking

**No Buttons Required!** Everything controlled by keyboard.

## Why Keyboard-Only?

**No Buttons Needed:**
- Blind users naturally use keyboards
- Keyboard shortcuts are faster than finding buttons
- No visual navigation required
- Standard keyboard layout - no learning curve
- Works with all screen readers
- No mouse/touch required

**Keyboard Advantages:**
- **Instant access** - no searching for buttons
- **Muscle memory** - shortcuts become automatic
- **Universal** - works on any device with keyboard
- **Reliable** - no UI changes break functionality
- **Efficient** - single key press vs. multiple clicks

## Complete Keyboard Shortcut Reference

### Dashboard Shortcuts
- **L** - List all assessments
- **1-9** - Open assessment by number
- **V** - Voice commands (optional)
- **H** - Help (hear all shortcuts)
- **Escape** - Stop speaking

### Assessment Shortcuts
- **Q** - Listen to current question
- **N** - Next question
- **P** - Previous question
- **1-9** - Jump to question number
- **R** - Start recording answer
- **S** - Stop recording
- **Enter** - Submit answer
- **C** - Question count
- **V** - Voice commands (optional)
- **H** - Help (hear all shortcuts)
- **Escape** - Stop speaking

**Note:** All shortcuts work when not typing in input fields. Shortcuts are ignored when cursor is in text areas.

## Technical Implementation

### JavaScript Module: `accessible.js`

- Uses Web Speech API for text-to-speech
- Automatically detects dashboard vs assessment pages
- Integrates with existing audio recording functionality
- Provides audio feedback for all interactions

### CSS Enhancements

- Large button sizes (min-height: 80px)
- High contrast focus states
- Touch-friendly on mobile devices
- Supports reduced motion preferences
- Supports high contrast mode

## Usage Flow

### Starting an Assessment

1. User lands on dashboard
2. System auto-announces: "Dashboard loaded. Press L to list assessments, or press H for help."
3. User presses **L** key
4. System speaks all available assessments
5. User presses **1** (or 2, 3, etc.) to open an assessment
6. Assessment opens automatically

### Answering Questions

1. System auto-announces: "[Assessment] loaded. This assessment has X questions. Press Q to hear the first question."
2. User presses **Q** - Hears current question
3. User presses **R** - Starts recording answer
4. User speaks answer clearly
5. User presses **S** - Stops recording and processes answer
6. System transcribes and reads back answer
7. User presses **Enter** - Submits answer
8. User presses **N** - Moves to next question (auto-speaks it)
9. Repeat steps 3-8 for all questions

**Key Advantage:** No buttons to find - just press keys! Works perfectly with screen readers and keyboard navigation.

## Browser Compatibility

- **Chrome/Edge**: Full support (Web Speech API)
- **Firefox**: Full support (Web Speech API)
- **Safari**: Full support (Web Speech API)
- **Mobile Browsers**: Full support with larger touch targets

## Accessibility Standards

- **WCAG 2.1 AA Compliant**
- **Keyboard Navigation**: Full support
- **Screen Readers**: Compatible with NVDA, JAWS, VoiceOver
- **High Contrast**: Supported
- **Reduced Motion**: Respected

## Customization

### Button Sizes

Buttons can be customized in `static/css/app.css`:

```css
[data-accessible-dashboard] button,
[data-accessible-assessment] button {
    min-height: 80px; /* Adjust as needed */
    font-size: 1.2rem; /* Adjust as needed */
}
```

### Speech Rate

Speech rate can be adjusted in `static/js/accessible.js`:

```javascript
utterance.rate = 0.9; // Adjust between 0.1 and 10
```

### Button Text

All button text can be customized in the templates:
- `templates/student/dashboard.html`
- `templates/student/assessment_session.html`

## Testing

To test the accessible interface:

1. Use a screen reader (NVDA, JAWS, or VoiceOver)
2. Navigate using only keyboard (Tab, Enter, Space)
3. Verify all buttons speak their function
4. Test on mobile device for touch targets
5. Test with high contrast mode enabled

## Future Enhancements

Potential improvements:
- Customizable speech rate per user
- Voice commands for navigation
- Audio cues for different actions
- Haptic feedback on mobile devices
- Braille display support

