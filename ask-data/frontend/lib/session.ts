const SESSION_STORAGE_KEY = "ask-data-session-id";

export function getCurrentSessionId(): string | null {
  return window.localStorage.getItem(SESSION_STORAGE_KEY);
}

export function setCurrentSessionId(sessionId: string): void {
  window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

export function getOrCreateSessionId(): string {
  const existingSessionId = getCurrentSessionId();
  if (existingSessionId) {
    return existingSessionId;
  }

  const nextSessionId = crypto.randomUUID();
  setCurrentSessionId(nextSessionId);
  return nextSessionId;
}

export function createNewSessionId(): string {
  const nextSessionId = crypto.randomUUID();
  setCurrentSessionId(nextSessionId);
  return nextSessionId;
}
