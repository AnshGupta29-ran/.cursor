/**
 * Client-side engine loader for the gaming platform
 */

// Load the core engine and modules
(function() {
    // This would normally be a build process that bundles all the modules
    // For this prototype, we'll just include the core engine and modules directly

    // Core Engine
    class EventBus {
        constructor() {
            this.listeners = new Map();
        }
        on(event, fn) {
            if (!this.listeners.has(event)) this.listeners.set(event, new Set());
            this.listeners.get(event).add(fn);
        }
        emit(event, payload) {
            for (const fn of this.listeners.get(event) || []) fn(payload);
        }
    }

    class Entity {
        constructor(id) {
            this.id = id;
            this.components = new Map();
        }
        addComponent(name, data) {
            this.components.set(name, data);
            return this;
        }
        getComponent(name) {
            return this.components.get(name);
        }
    }

    class Engine {
        constructor() {
            this.running = false;
            this.entities = new Map();
            this.modules = [];
            this.eventBus = new EventBus();
            this._raf = null;
            this._last = 0;
            this._nextId = 1;
        }

        registerModule(module) {
            this.modules.push(module);
            if (typeof module.init === 'function') module.init(this);
        }

        createEntity() {
            const id = String(this._nextId++);
            const entity = new Entity(id);
            this.entities.set(id, entity);
            return entity;
        }

        start() {
            if (this.running) return;
            this.running = true;
            this._last = performance.now();
            const tick = (now) => {
                if (!this.running) return;
                const dt = (now - this._last) / 1000;
                this._last = now;
                for (const m of this.modules) {
                    if (typeof m.update === 'function') m.update(dt, this);
                }
                this.eventBus.emit('tick', { dt });
                this._raf = requestAnimationFrame(tick);
            };
            this._raf = requestAnimationFrame(tick);
        }

        stop() {
            this.running = false;
            if (this._raf) cancelAnimationFrame(this._raf);
        }

        update(deltaTime) {
            // Update all systems
            for (const module of this.modules) {
                if (typeof module.update === 'function') {
                    module.update(deltaTime, this);
                }
            }
        }
    }

    // Export to global scope
    window.GamingEngine = { Engine, Entity, EventBus };
})();