using System.Collections.Generic;

namespace Tidewatch.Core
{
    /// <summary>One phase in a level's repeating tide schedule.</summary>
    public struct TidePhaseDuration
    {
        public TidePhase Phase;
        public float Seconds;
        public TidePhaseDuration(TidePhase phase, float seconds) { Phase = phase; Seconds = seconds; }
    }

    /// <summary>
    /// The tide state machine. Cycles Low → Rising → High → Ebbing on a per-level schedule.
    /// Emits an event on every phase turn so the sim can re-path enemies and apply Beached.
    /// Pure C#; the Game layer drives the clock and renders the water animation.
    /// </summary>
    public sealed class TideSystem
    {
        private readonly List<TidePhaseDuration> _schedule;
        private readonly float _cadenceMult;
        private int _index;
        private float _phaseClock; // seconds elapsed in the current phase

        public TidePhase CurrentPhase => _schedule.Count > 0 ? _schedule[_index].Phase : TidePhase.Low;
        public float PhaseClock => _phaseClock;
        public float CurrentPhaseDuration => _schedule.Count > 0 ? _schedule[_index].Seconds * _cadenceMult : 0f;
        public float TimeToNextTurn => CurrentPhaseDuration - _phaseClock;
        public int ScheduleLength => _schedule.Count;

        /// <summary>Fired when the phase turns. Passes the new phase.</summary>
        public event System.Action<TidePhase> OnPhaseTurn;

        public TideSystem(IList<TidePhaseDuration> schedule, float cadenceMult)
        {
            _schedule = new List<TidePhaseDuration>(schedule ?? new List<TidePhaseDuration>());
            _cadenceMult = cadenceMult <= 0f ? 1f : cadenceMult;
            _index = 0;
            _phaseClock = 0f;
        }

        /// <summary>Advance the clock. Returns true if the phase turned this tick.</summary>
        public bool Tick(float dt)
        {
            if (_schedule.Count == 0) return false;
            _phaseClock += dt;
            float dur = CurrentPhaseDuration;
            if (_phaseClock >= dur)
            {
                _phaseClock -= dur;
                _index = (_index + 1) % _schedule.Count;
                OnPhaseTurn?.Invoke(CurrentPhase);
                return true;
            }
            return false;
        }

        /// <summary>Force an immediate surge to the next phase (Drowned Bell Tidecall).</summary>
        public void ForceSurge()
        {
            if (_schedule.Count == 0) return;
            _phaseClock = 0f;
            _index = (_index + 1) % _schedule.Count;
            OnPhaseTurn?.Invoke(CurrentPhase);
        }

        /// <summary>Peek the phase after N turns (for the HUD preview / warning).</summary>
        public TidePhase PeekPhase(int turnsAhead)
        {
            if (_schedule.Count == 0) return TidePhase.Low;
            return _schedule[(_index + turnsAhead) % _schedule.Count].Phase;
        }

        public int CurrentIndex => _index;

        /// <summary>Restore from a save.</summary>
        public void SetState(int index, float phaseClock)
        {
            if (_schedule.Count == 0) return;
            _index = ((index % _schedule.Count) + _schedule.Count) % _schedule.Count;
            _phaseClock = phaseClock;
        }
    }
}
