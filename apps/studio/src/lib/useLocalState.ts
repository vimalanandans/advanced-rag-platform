import { useEffect, useState } from "react";

export function useLocalState<T>(key: string, fallback: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const saved = window.localStorage.getItem(key);
      return saved ? JSON.parse(saved) as T : fallback;
    } catch { return fallback; }
  });
  useEffect(() => {
    try { window.localStorage.setItem(key, JSON.stringify(value)); } catch { /* local persistence is best effort */ }
  }, [key, value]);
  return [value, setValue] as const;
}
