/**
 * Physics Module for the Game Engine
 * Handles collision detection and physics simulation
 */

class PhysicsModule {
  constructor() {
    this.name = 'physics';
    this.gravity = { x: 0, y: 9.81 };
    this.bodies = new Map();
  }

  init(engine) {
    console.log('Physics module initialized');
    // Register with engine if needed
  }

  update(deltaTime, engine) {
    // Update physics simulation
    this.updateBodies(deltaTime);
  }

  /**
   * Add a body to the physics simulation
   */
  addBody(id, body) {
    this.bodies.set(id, body);
  }

  /**
   * Remove a body from the physics simulation
   */
  removeBody(id) {
    this.bodies.delete(id);
  }

  /**
   * Update all bodies in the simulation
   */
  updateBodies(deltaTime) {
    for (const [id, body] of this.bodies.entries()) {
      // Apply gravity
      body.velocity.x += this.gravity.x * deltaTime;
      body.velocity.y += this.gravity.y * deltaTime;

      // Update position based on velocity
      body.position.x += body.velocity.x * deltaTime;
      body.position.y += body.velocity.y * deltaTime;

      // Simple ground collision
      if (body.position.y > 400) {
        body.position.y = 400;
        body.velocity.y = -body.velocity.y * 0.7; // Bounce with damping
      }
    }
  }

  /**
   * Check for collisions between two bodies
   */
  checkCollision(bodyA, bodyB) {
    const dx = bodyA.position.x - bodyB.position.x;
    const dy = bodyA.position.y - bodyB.position.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    return distance < (bodyA.radius + bodyB.radius);
  }

  /**
   * Handle collision response
   */
  handleCollision(bodyA, bodyB) {
    // Simple elastic collision response
    const dx = bodyB.position.x - bodyA.position.x;
    const dy = bodyB.position.y - bodyA.position.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance === 0) return; // Avoid division by zero

    // Normalize collision vector
    const nx = dx / distance;
    const ny = dy / distance;

    // Relative velocity
    const dvx = bodyB.velocity.x - bodyA.velocity.x;
    const dvy = bodyB.velocity.y - bodyA.velocity.y;

    // Velocity along the normal
    const velocityAlongNormal = dvx * nx + dvy * ny;

    // Do not resolve if velocities are separating
    if (velocityAlongNormal > 0) return;

    // Calculate impulse scalar
    const e = 0.8; // Coefficient of restitution
    const j = -(1 + e) * velocityAlongNormal;

    // Apply impulse
    bodyA.velocity.x -= j * nx;
    bodyA.velocity.y -= j * ny;
    bodyB.velocity.x += j * nx;
    bodyB.velocity.y += j * ny;
  }
}

module.exports = PhysicsModule;