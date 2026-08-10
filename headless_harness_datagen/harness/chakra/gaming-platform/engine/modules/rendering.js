/**
 * Rendering Module for the Game Engine
 * Handles drawing entities to canvas
 */

class RenderingModule {
  constructor(canvasId = 'gameCanvas') {
    this.name = 'rendering';
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.entities = new Map();
  }

  init(engine) {
    console.log('Rendering module initialized');
    // Set up canvas dimensions
    this.canvas.width = 800;
    this.canvas.height = 600;
  }

  update(deltaTime, engine) {
    // Update rendering logic if needed
  }

  render(deltaTime, engine) {
    // Clear canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Draw all entities with render component
    for (const [id, entity] of engine.entities.entries()) {
      const renderComponent = entity.getComponent('render');
      if (renderComponent) {
        this.drawEntity(entity, renderComponent);
      }
    }
  }

  /**
   * Draw an individual entity
   */
  drawEntity(entity, renderComponent) {
    const position = entity.getComponent('position');
    const size = entity.getComponent('size');

    if (!position || !size) return;

    // Draw based on type
    switch (renderComponent.type) {
      case 'rectangle':
        this.ctx.fillStyle = renderComponent.color || '#ffffff';
        this.ctx.fillRect(
          position.x - size.width / 2,
          position.y - size.height / 2,
          size.width,
          size.height
        );
        break;

      case 'circle':
        this.ctx.beginPath();
        this.ctx.arc(position.x, position.y, size.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = renderComponent.color || '#ffffff';
        this.ctx.fill();
        break;

      default:
        // Default to rectangle
        this.ctx.fillStyle = renderComponent.color || '#ffffff';
        this.ctx.fillRect(
          position.x - size.width / 2,
          position.y - size.height / 2,
          size.width,
          size.height
        );
    }
  }

  /**
   * Add an entity to be rendered
   */
  addEntity(id, entity) {
    this.entities.set(id, entity);
  }

  /**
   * Remove an entity from rendering
   */
  removeEntity(id) {
    this.entities.delete(id);
  }
}

module.exports = RenderingModule;