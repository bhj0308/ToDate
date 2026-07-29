import createClient from "openapi-fetch";

import { clearTokens, getTokens, setTokens } from "../auth/tokenStore";
import type { paths } from "./schema";

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

/** Redeems the refresh token directly (bypassing the client below to avoid middleware recursion). */
async function refreshTokens(refreshToken: string) {
  const response = await fetch(`${API_BASE_URL}/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) return null;
  const body = (await response.json()) as { access_token: string; refresh_token: string };
  return { accessToken: body.access_token, refreshToken: body.refresh_token };
}

export const api = createClient<paths>({ baseUrl: API_BASE_URL });

api.use({
  onRequest({ request }) {
    const tokens = getTokens();
    if (tokens) {
      request.headers.set("Authorization", `Bearer ${tokens.accessToken}`);
    }
    return request;
  },
  async onResponse({ request, response }) {
    // Returning nothing here leaves the original response untouched — only
    // return a value from this callback when actually replacing it (the
    // retry below), per openapi-fetch's middleware contract.
    if (response.status !== 401) return;

    // No token to refresh (e.g. an anonymous request like registration) — nothing to retry.
    const tokens = getTokens();
    if (!tokens) return;

    const refreshed = await refreshTokens(tokens.refreshToken);
    if (!refreshed) {
      await clearTokens();
      return;
    }
    await setTokens(refreshed);

    const retryRequest = request.clone();
    retryRequest.headers.set("Authorization", `Bearer ${refreshed.accessToken}`);
    return fetch(retryRequest);
  },
});
