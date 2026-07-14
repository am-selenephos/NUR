// Types shared between the FastAPI contract and the web client.
// Type-only: no runtime code crosses the boundary.
export interface ProfileOut {
  chosen_name: string;
  timezone: string | null;
  locale: string | null;
  writing_preference: string;
  sound_enabled: boolean;
  reduced_effects: boolean;
}
export interface OrbitOut {
  id: string;
  current_arrival_state: string | null;
  active_focus_area: string | null;
}
export interface MeResponse {
  id: string;
  email: string;
  email_verified: boolean;
  profile: ProfileOut;
  orbit: OrbitOut;
}
export interface RegisterRequest {
  chosen_name: string;
  email: string;
  password: string;
  consent: boolean;
}
export interface LoginRequest { email: string; password: string; }
export interface ApiErrorBody { detail: string; }
