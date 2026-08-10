/**
 * Core Game Engine
 * Implements Entity Component System (ECS) and game loop
 */

class Engine {
  constructor() {
    this.entities = new Map();
    this.components = new Map();
    this.systems = [];
    this.eventBus = new EventBus();
    this.running = false;
    this.lastTime = 0;
  }

  /**
   * Start the game engine
   */
  start() {
    if (this.running) return;
    this.running = true;
    this.lastTime = performance.now();
    this.gameLoop();
  }

  /**
   * Stop the game engine
   */
  stop() {
    this.running = false;
  }

  /**
   * Main game loop
   */
  gameLoop() {
    if (!this.running) return;

    const currentTime = performance.now();
    const deltaTime = (currentTime - this.lastTime) / 1000; // in seconds
    this.lastTime = currentTime;

    // Update all systems
    this.systems.forEach(system => {
      if (typeof system.update === 'function') {
        system.update(deltaTime);
      }
    });

    // Render all systems
    this.systems.forEach(system => {
      if (typeof system.render === 'function') {
        system.render(deltaTime);
      }
    });

    requestAnimationFrame(() => this.gameLoop());
  }

  /**
   * Create a new entity
   */
  createEntity() {
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
    this.entities.set(id, new Entity(id));
    return id;
  }

  /**
   * Get an entity by ID
   */
  getEntity(id) {
    return this.entities.get(id);
  }

  /**
   * Remove an entity
   */
  removeEntity(id) {
    this.entities.delete(id);
  }

  /**
   * Register a component type
   */
  registerComponent(name, componentClass) {
    this.components.set(name, componentClass);
  }

  /**
   * Add a system to the engine
   */
  addSystem(system) {
    this.systems.push(system);
  }

  /**
   * Emit an event
   */
  emitEvent(event) {
    this.eventBus.emit(event);
  }

  /**
   * Subscribe to an event
   */
  onEvent(type, callback) {
    this.eventBus.on(type, callback);
  }
}

/**
 * Entity class
 */
class Entity {
  constructor(id) {
    this.id = id;
    this.components = new Map();
  }

  /**
   * Add a component to the entity
   */
  addComponent(componentName, componentData) {
    // This is a simplified version - in practice you'd want to validate component types
    this.components.set(componentName, componentData);
  }

  /**
   * Get a component from the entity
   */
  getComponent(componentName) {
    return this.components.get(componentName);
  }

  /**
   * Remove a component from the entity
   */
  removeComponent(componentName) {
    this.components.delete(componentName);
  }
}

/**
 * Event Bus for communication between components
 */
class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  /**
   * Emit an event
   */
  emit(event) {
    const listeners = this.listeners.get(event.type);
    if (listeners) {
      listeners.forEach(callback => callback(event));
    }
  }

  /**
   * Subscribe to an event type
   */
  on(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type).push(callback);
  }
}

// Export the engine
module.exports = { Engine, Entity, EventBus };