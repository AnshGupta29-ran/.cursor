/**
 * Input Module for the Game Engine
 * Handles keyboard and mouse input
 */

class InputModule {
  constructor() {
    this.name = 'input';
    this.keys = new Set();
    this.mouse = { x: 0, y: 0, pressed: false };
    this.keyHandlers = new Map();
  }

  init(engine) {
    console.log('Input module initialized');

    // Setup keyboard event listeners
    window.addEventListener('keydown', (e) => {
      this.keys.add(e.key.toLowerCase());
      this.handleKey(e.key.toLowerCase(), 'down');
    });

    window.addEventListener('keyup', (e) => {
      this.keys.delete(e.key.toLowerCase());
      this.handleKey(e.key.toLowerCase(), 'up');
    });

    // Setup mouse event listeners
    window.addEventListener('mousemove', (e) => {
      const rect = e.target.getBoundingClientRect();
      this.mouse.x = e.clientX - rect.left;
      this.mouse.y = e.clientY - rect.top;
    });

    window.addEventListener('mousedown', (e) => {
      this.mouse.pressed = true;
    });

    window.addEventListener('mouseup', (e) => {
      this.mouse.pressed = false;
    });
  }

  update(deltaTime, engine) {
    // Update input state if needed
  }

  /**
   * Check if a key is currently pressed
   */
  isPressed(key) {
    return this.keys.has(key.toLowerCase());
  }

  /**
   * Register a handler for a specific key
   */
  onKey(key, handler, eventType = 'down') {
    const keyEvent = `${key.toLowerCase()}:${eventType}`;
    if (!this.keyHandlers.has(keyEvent)) {
      this.keyHandlers.set(keyEvent, []);
    }
    this.keyHandlers.get(keyEvent).push(handler);
  }

  /**
   * Handle key events
   */
  handleKey(key, eventType) {
    const keyEvent = `${key}:${eventType}`;
    const handlers = this.keyHandlers.get(keyEvent);
    if (handlers) {
      handlers.forEach(handler => handler());
    }
  }

  /**
   * Get mouse position
   */
  getMousePosition() {
    return { ...this.mouse };
  }
}

module.exports = InputModule;