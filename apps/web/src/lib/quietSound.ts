type QuietEvent = "talk_send" | "model_response" | "capsule_created" | "outcome_kept";

const FREQUENCY: Record<QuietEvent, number> = {
  talk_send: 392,
  model_response: 528,
  capsule_created: 660,
  outcome_kept: 594,
};

let ctx: AudioContext | null = null;

export function playQuietEvent(kind: QuietEvent, enabled: boolean): void {
  if (!enabled) return;
  try {
    ctx ??= new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = FREQUENCY[kind];
    osc.type = "sine";
    gain.gain.value = 0.0001;
    osc.connect(gain);
    gain.connect(ctx.destination);
    const now = ctx.currentTime;
    gain.gain.exponentialRampToValueAtTime(0.025, now + 0.025);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18);
    osc.start(now);
    osc.stop(now + 0.2);
  } catch {
    // Sound is decorative and opt-in; failure must not affect the workflow.
  }
}
