using System;
using UnityEngine;

namespace Bedsit
{
    /// <summary>
    /// Routes Windows mouse clicks, touch taps and (for convenience) keyboard keys to exactly three actions.
    /// Touches arrive through Unity's touch-to-mouse simulation, so one code path serves both platforms.
    /// Gameplay listens to the event and never reads the Input API itself.
    /// </summary>
    public class InputRouter : MonoBehaviour
    {
        public event Action<PlayerAction> ActionTriggered;

        /// <summary>When true all input is ignored (e.g. during the wake-up sequence).</summary>
        public bool Locked { get; set; }

        /// <summary>Last action raised; the HUD uses it to flash a cue.</summary>
        public PlayerAction LastAction { get; private set; }

        public bool KeyboardEnabled = true;

        void Update()
        {
            if (Locked) return;
            if (Input.GetMouseButtonDown(0))
            {
                var action = InputRegions.ClassifyScreen(Input.mousePosition, Screen.width, Screen.height);
                if (action != PlayerAction.None) Raise(action);
            }
            if (!KeyboardEnabled) return;
            if (Input.GetKeyDown(KeyCode.LeftArrow) || Input.GetKeyDown(KeyCode.A)) Raise(PlayerAction.TurnLeft);
            else if (Input.GetKeyDown(KeyCode.RightArrow) || Input.GetKeyDown(KeyCode.D)) Raise(PlayerAction.TurnRight);
            else if (Input.GetKeyDown(KeyCode.UpArrow) || Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.Space)) Raise(PlayerAction.Interact);
        }

        /// <summary>Raise an action programmatically (tests and automation).</summary>
        public void Raise(PlayerAction action)
        {
            if (Locked || action == PlayerAction.None) return;
            LastAction = action;
            ActionTriggered?.Invoke(action);
        }
    }
}
