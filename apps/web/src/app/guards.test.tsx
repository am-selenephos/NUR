import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "./AuthProvider";
import { ProtectedRoute, PublicOnlyRoute } from "./guards";

function harness(initial: string) {
  return (
    <MemoryRouter initialEntries={[initial]}>
      <AuthProvider>
        <Routes>
          <Route element={<PublicOnlyRoute />}>
            <Route path="/" element={<div>AUTH SCREEN</div>} />
            <Route path="/auth" element={<div>AUTH SCREEN</div>} />
          </Route>
          <Route element={<ProtectedRoute />}>
            <Route path="/today" element={<div>TODAY SCREEN</div>} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

function fetchReturning(status: number, body: unknown) {
  return vi.fn(async () => ({
    status, ok: status >= 200 && status < 300,
    text: async () => JSON.stringify(body),
  } as Response));
}

afterEach(() => vi.restoreAllMocks());

describe("route guards", () => {
  it("redirects anonymous user from /today to /auth", async () => {
    vi.stubGlobal("fetch", fetchReturning(401, { detail: "Not authenticated." }));
    render(harness("/today"));
    expect(await screen.findByText("AUTH SCREEN")).toBeInTheDocument();
  });

  it("redirects authenticated user away from /auth to /today", async () => {
    vi.stubGlobal("fetch", fetchReturning(200, {
      id: "u1", email: "a@nurapp.dev", email_verified: false,
      profile: { chosen_name: "Star", timezone: null, locale: null, sound_enabled: true, reduced_effects: false },
      orbit: { id: "o1", current_arrival_state: null, active_focus_area: null },
    }));
    render(harness("/auth"));
    expect(await screen.findByText("TODAY SCREEN")).toBeInTheDocument();
  });

  it("keeps anonymous user on /auth", async () => {
    vi.stubGlobal("fetch", fetchReturning(401, { detail: "Not authenticated." }));
    render(harness("/auth"));
    await waitFor(() => expect(screen.getByText("AUTH SCREEN")).toBeInTheDocument());
  });
});
