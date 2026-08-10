/**
 * Audio Module for the Game Engine
 * Handles sound effects and music
 */

class AudioModule {
  constructor() {
    this.name = 'audio';
    this.sounds = new Map();
    this.music = null;
    this.masterVolume = 1.0;
  }

  init(engine) {
    console.log('Audio module initialized');
  }

  update(deltaTime, engine) {
    // Update audio if needed
  }

  /**
   * Load a sound effect
   */
  loadSound(name, url) {
    const audio = new Audio(url);
    this.sounds.set(name, audio);
  }

  /**
   * Play a sound effect
   */
  playSound(name, volume = 1.0) {
    const sound = this.sounds.get(name);
    if (sound) {
      sound.volume = volume * this.masterVolume;
      sound.currentTime = 0; // Reset to beginning
      sound.play().catch(e => console.log('Audio play error:', e));
    }
  }

  /**
   * Stop a sound effect
   */
  stopSound(name) {
    const sound = this.sounds.get(name);
    if (sound) {
      sound.pause();
      sound.currentTime = 0;
    }
  }

  /**
   * Load background music
   */
  loadMusic(url) {
    this.music = new Audio(url);
    this.music.loop = true;
  }

  /**
   * Play background music
   */
  playMusic(volume = 1.0) {
    if (this.music) {
      this.music.volume = volume * this.masterVolume;
      this.music.play().catch(e => console.log('Music play error:', e));
    }
  }

  /**
   * Stop background music
   */
  stopMusic() {
    if (this.music) {
      this.music.pause();
      this.music.currentTime = 0;
    }
  }

  /**
   * Set master volume
   */
  setMasterVolume(volume) {
    this.masterVolume = Math.max(0, Math.min(1, volume));
  }
}

module.exports = AudioModule;