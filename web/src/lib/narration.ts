let activeStop: (() => void) | null = null;

export function stopActiveNarration() { activeStop?.(); }
export function claimNarration(stop: () => void) {
  activeStop?.();
  activeStop = stop;
  return () => { if (activeStop === stop) activeStop = null; };
}

// 限制单个utterance长度；只分段，不删改事实、来源或证据不足提示。
export function splitNarration(text: string): string[] {
  const parts: string[] = [];
  let remaining = text.trim();
  while (remaining.length > 220) {
    const window = remaining.slice(0, 220);
    const candidates = [...window.matchAll(/[。！？；\n]/g)];
    const cut = candidates.length ? candidates[candidates.length - 1].index! + 1 : 220;
    parts.push(remaining.slice(0, cut));
    remaining = remaining.slice(cut);
  }
  if (remaining) parts.push(remaining);
  return parts;
}
