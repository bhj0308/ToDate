import Constants from "expo-constants";
import createClient from "openapi-fetch";

import { clearTokens, getTokens, setTokens } from "../auth/tokenStore";
import type { paths } from "./schema";

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

/** Sent on every request so the API can refuse builds it no longer supports. */
export const APP_VERSION = Constants.expoConfig?.version ?? "0.0.0";

// The API answers 426 once this build is below its minimum version. Screens
// subscribe (see useUpgradeRequired) and swap in an "update the app" screen.
let upgradeRequired = false;
const upgradeListeners = new Set<() => void>();

export const upgradeRequiredStore = {
  get: () => upgradeRequired,
  subscribe: (listener: () => void) => {
    upgradeListeners.add(listener);
    return () => upgradeListeners.delete(listener);
  },
};

function markUpgradeRequired() {
  if (upgradeRequired) return;
  upgradeRequired = true;
  upgradeListeners.forEach((listener) => listener());
}

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
    request.headers.set("X-App-Version", APP_VERSION);
    const tokens = getTokens();
    if (tokens) {
      request.headers.set("Authorization", `Bearer ${tokens.accessToken}`);
    }
    return request;
  },
  async onResponse({ request, response }) {
    if (response.status === 426) {
      markUpgradeRequired();
      return;
    }
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
