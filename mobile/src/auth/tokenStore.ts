import * as SecureStore from "expo-secure-store";

const ACCESS_KEY = "todate.access_token";
const REFRESH_KEY = "todate.refresh_token";

export type Tokens = { accessToken: string; refreshToken: string };

let current: Tokens | null = null;
const listeners = new Set<(tokens: Tokens | null) => void>();

function notify() {
  for (const listener of listeners) listener(current);
}

/** Loads persisted tokens into memory. Call once at app startup. */
export async function hydrateTokens(): Promise<Tokens | null> {
  const [accessToken, refreshToken] = await Promise.all([
    SecureStore.getItemAsync(ACCESS_KEY),
    SecureStore.getItemAsync(REFRESH_KEY),
  ]);
  current = accessToken && refreshToken ? { accessToken, refreshToken } : null;
  return current;
}

export function getTokens(): Tokens | null {
  return current;
}

export async function setTokens(tokens: Tokens): Promise<void> {
  current = tokens;
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_KEY, tokens.accessToken),
    SecureStore.setItemAsync(REFRESH_KEY, tokens.refreshToken),
  ]);
  notify();
}

export async function clearTokens(): Promise<void> {
  current = null;
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_KEY),
    SecureStore.deleteItemAsync(REFRESH_KEY),
  ]);
  notify();
}

/** Subscribe to token changes (login/logout/refresh). Returns an unsubscribe fn. */
export function subscribeTokens(listener: (tokens: Tokens | null) => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
