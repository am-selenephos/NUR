/* Source global composer: routes what you say into Talk, honestly. */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useOrbit } from "../../../lib/orbitState";
import { V197_PROMPT_ACTIONS } from "../../../v197/contract";

type PromptAction = typeof V197_PROMPT_ACTIONS[number]["key"];

export default function GlobalComposer() {
  const orbit = useOrbit();
  const nav = useNavigate();
  const [v, setV] = useState("");
  const [voiceHint, setVoiceHint] = useState(false);

  function send() {
    const t = v.trim();
    if (!t) return;
    orbit.setDraft(t);
    setV("");
    setVoiceHint(false);
    nav("/talk");
  }

  function prompt(action: PromptAction) {
    if (action === "plan") {
      void orbit.beginRoute();
      nav("/plan");
      return;
    }
    if (action === "explore") {
      orbit.setDraft(v.trim() || "Explore this signal with me.");
      setV("");
      nav("/talk");
      return;
    }
    const prefix: Record<Exclude<PromptAction, "plan" | "explore">, string> = {
      reflect: "Reflect on this: ",
      ask: "",
      challenge: "Challenge this honestly: ",
      summarize: "Summarize the signal here: ",
    };
    orbit.setDraft(`${prefix[action]}${v.trim()}`.trim());
    setV("");
    nav("/talk");
  }

  return (
    <section className="global-composer universe-composer-shell universe-composer-shell--v173" aria-label="Speak with NUR">
      <div className="universe-composer-label">
        <span>✦</span> Speak with NUR <small>Private by default · you control the scope.</small>
      </div>
      <div className={`universe-composer universe-composer--v173${voiceHint ? " is-listening" : ""}`}>
        <input id="universe-composer-input" data-testid="universe-composer-input"
               placeholder={voiceHint ? "Voice capture is not connected yet. Type the note here." : "Ask anything. Reflect deeply. Design your becoming."}
               value={v}
               onChange={e => setV(e.target.value)}
               onKeyDown={e => e.key === "Enter" && send()} />
        <div className="composer-actions" aria-label="Composer actions">
          <button aria-label="Start voice note" aria-pressed={voiceHint}
                  className="voice-button composer-action composer-action--voice" type="button"
                  title="Voice capture is not connected in this local beta; type the note instead."
                  onClick={() => setVoiceHint(x => !x)}>
            <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
              <rect height="12" rx="3.75" width="7.5" x="8.25" y="3" />
              <path d="M5.5 11.25a6.5 6.5 0 0 0 13 0M12 17.75v3.25M8.75 21h6.5" />
            </svg>
            <span aria-hidden="true" className="composer-action__glint" />
          </button>
          <button aria-label="Send to NUR" className="send-button send-holo-pill universe-send composer-action composer-action--send"
                  type="button" onClick={send}>
            <span className="send-holo-pill__label">Send</span>
            <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
              <path d="M4.5 12h14.5M13.5 5.5 20 12l-6.5 6.5" />
            </svg>
            <span aria-hidden="true" className="composer-action__glint" />
          </button>
        </div>
      </div>
      <div className="universe-prompt-row">
        {V197_PROMPT_ACTIONS.map(action => (
          <button key={action.key} type="button" data-action={action.key}
                  className="nur-star-prefix-row"
                  onClick={() => prompt(action.key)}>
            {action.glyph} {action.label}
          </button>
        ))}
      </div>
    </section>
  );
}
