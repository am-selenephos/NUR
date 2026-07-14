import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "./api";

function mockFetch(status: number, body: unknown, capture?: (init: RequestInit) => void) {
  return vi.fn(async (_url: string, init: RequestInit) => {
    capture?.(init);
    return {
      status,
      ok: status >= 200 && status < 300,
      text: async () => (body === undefined ? "" : JSON.stringify(body)),
    } as Response;
  });
}

afterEach(() => vi.restoreAllMocks());

describe("api client", () => {
  it("sends credentials and X-CSRF-Token from cookie on POST", async () => {
    document.cookie = "nur_csrf=csrf-abc";
    let seen: RequestInit = {};
    vi.stubGlobal("fetch", mockFetch(200, { ok: true }, (init) => (seen = init)));
    await api.login({ email: "a@nurapp.dev", password: "secret12" });
    expect(seen.credentials).toBe("include");
    expect(new Headers(seen.headers).get("X-CSRF-Token")).toBe("csrf-abc");
  });

  it("does NOT attach CSRF header on GET", async () => {
    let seen: RequestInit = {};
    vi.stubGlobal("fetch", mockFetch(200, { id: "1" }, (init) => (seen = init)));
    await api.me();
    expect(new Headers(seen.headers).get("X-CSRF-Token")).toBeNull();
  });

  it("throws ApiError carrying status + detail on failure", async () => {
    vi.stubGlobal("fetch", mockFetch(401, { detail: "Not authenticated." }));
    await expect(api.me()).rejects.toMatchObject({ status: 401, message: "Not authenticated." });
    await expect(api.me()).rejects.toBeInstanceOf(ApiError);
  });

  it("treats 204 as empty success (logout)", async () => {
    document.cookie = "nur_csrf=x";
    vi.stubGlobal("fetch", mockFetch(204, undefined));
    await expect(api.logout()).resolves.toBeUndefined();
  });
});
