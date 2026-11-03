import { useEffect, useRef, useState } from "react";
import type { RetrieveResponse } from "../types/backend";
import { claimNarration } from "../lib/narration";
import { splitNarration } from "../lib/narration";
import { generationLabel } from "./SharedEvidencePanel";

type SpeechState = "idle" | "starting" | "speaking" | "paused" | "finished" | "error";
export function DigitalNarrator({ response }: { response: RetrieveResponse }) {
  const supported = typeof window !== "undefined" && typeof window.speechSynthesis?.speak === "function"
    && typeof window.SpeechSynthesisUtterance === "function";
  const [state, setState] = useState<SpeechState>("idle");
  const [error, setError] = useState(""), [imageFailed, setImageFailed] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]), [voiceId, setVoiceId] = useState("");
  const [progress, setProgress] = useState(0);
  const [segmentCount, setSegmentCount] = useState(0);
  const [speechBeat, setSpeechBeat] = useState(0);
  const portrait = useRef<HTMLElement | null>(null);
  const gesture = useRef<Animation | null>(null);
  const active = useRef(false), session = useRef(0), release = useRef<(() => void) | null>(null);
  const utterance = useRef<SpeechSynthesisUtterance | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fallback = response.generator_mode === "template"
    || (response.generator_mode === "llm" && response.used_fallback === true);
  const online = response.generator_mode === "llm" && response.provider_status === "success" && response.used_fallback === false;
  const allowed = response.final_decision.status === "approved" && response.final_decision.can_output
    && !response.final_decision.review_required;
  const canSpeak = allowed && (fallback || online) && response.generator_mode !== "mock"
    && response.citations_used.length > 0 && response.answer.trim().length > 0;
  const firstEvidence = response.answer.match(/^- 证据 \d+：(.+)$/m)?.[1];
  const preview = firstEvidence?.match(/^[^。！？]{1,120}[。！？]/)?.[0];
  function clearTimer() { if (timer.current) clearTimeout(timer.current); timer.current = null; }
  function stop() {
    gesture.current?.cancel();
    session.current++; active.current = false; utterance.current = null; clearTimer();
    release.current?.(); release.current = null;
    if (supported) { try { window.speechSynthesis.cancel(); } catch { /* 停止时不遮挡正文。 */ } }
    setState("idle"); setProgress(0);
  }
  useEffect(() => {
    setState("idle"); setError(""); setProgress(0);
    return () => {
      gesture.current?.cancel();
      session.current++; clearTimer();
      if (active.current && supported) { try { window.speechSynthesis.cancel(); } catch { /* 清理不阻断卸载。 */ } }
      active.current = false; utterance.current = null; release.current?.(); release.current = null;
    };
  }, [response, supported]);
  useEffect(() => {
    if (!supported) return;
    const synthesis = window.speechSynthesis;
    function refresh() {
      try { setVoices(synthesis.getVoices().filter(v => /^zh([_-]|$)/i.test(v.lang))); }
      catch { setVoices([]); }
    }
    refresh();
    synthesis.addEventListener("voiceschanged", refresh);
    const leave = () => { if (active.current) stop(); };
    window.addEventListener("pagehide", leave);
    return () => {
      synthesis.removeEventListener("voiceschanged", refresh);
      window.removeEventListener("pagehide", leave);
    };
  }, [supported]);
  if (!allowed) return null;

  function play(text: string) {
    if (!supported || !canSpeak) return;
    const chunks = splitNarration(text);
    stop();
    setSegmentCount(chunks.length);
    setError(""); setState("starting");
    active.current = true; release.current = claimNarration(stop);
    // claim会停止旧会话；新的会话编号必须在取得播放权后确定。
    const token = ++session.current;
    function fail(message: string) {
      if (session.current !== token || !active.current) return;
      gesture.current?.cancel();
      active.current = false; utterance.current = null; clearTimer();
      release.current?.(); release.current = null;
      try { window.speechSynthesis.cancel(); } catch { /* 原文仍可阅读。 */ }
      setError(message); setState("error");
    }
    function speak(index: number) {
      if (session.current !== token || !active.current) return;
      if (index >= chunks.length) {
        gesture.current?.cancel();
        active.current = false; utterance.current = null; clearTimer();
        release.current?.(); release.current = null; setState("finished"); return;
      }
      const u = new window.SpeechSynthesisUtterance(chunks[index]);
      utterance.current = u; u.lang = "zh-CN"; u.rate = 1;
      const voice = voices.find(v => v.voiceURI === voiceId) ?? voices.find(v => v.localService) ?? voices[0];
      if (voice) u.voice = voice;
      setProgress(index + 1);
      u.onstart = () => {
        if (session.current !== token || utterance.current !== u || !active.current) return;
        clearTimer();
        setSpeechBeat(0);
        setState("speaking");
        if (!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
          gesture.current?.cancel();
          gesture.current = portrait.current?.animate?.(
            [
              { transform: "rotate(0deg)" },
              { transform: "translateY(5px) rotate(4deg)", offset: 0.45 },
              { transform: "rotate(0deg)" },
            ],
            { duration: 520, easing: "ease-in-out" },
          ) ?? null;
        }
      };
      u.onboundary = () => {
        if (session.current === token && utterance.current === u && active.current) {
          setSpeechBeat(beat => beat + 1);
        }
      };
      u.onend = () => { if (session.current === token && utterance.current === u) { clearTimer(); speak(index + 1); } };
      u.onerror = () => { if (utterance.current === u) fail("语音服务未完成朗读，可重试或直接阅读原文。"); };
      clearTimer();
      timer.current = setTimeout(() => fail("语音服务未开始播放，请检查系统语音或更换音色后重试。"), 10000);
      try { window.speechSynthesis.resume(); window.speechSynthesis.speak(u); }
      catch { fail("浏览器语音调用失败，仍可阅读回答与证据。"); }
    }
    speak(0);
  }
  function pauseOrResume() {
    try {
      if (state === "speaking") { window.speechSynthesis.pause(); gesture.current?.cancel(); setState("paused"); }
      else if (state === "paused") { window.speechSynthesis.resume(); setState("speaking"); }
    } catch { stop(); setError("浏览器未能切换播放状态，请重新播放。"); setState("error"); }
  }
  const playing = state === "starting" || state === "speaking" || state === "paused";
  const labels: Record<SpeechState, string> = {
    idle: "待播放", starting: "正在启动语音", speaking: "正在朗读", paused: "已暂停", finished: "朗读结束", error: "朗读失败",
  };
  return <section className={`digital-narrator ${state === "speaking" ? "is-speaking" : ""}`} aria-label="小红军数字讲解员">
    <figure className="narrator-portrait" ref={portrait}>
      {!imageFailed ? <div className="narrator-character">
        <img src={`${import.meta.env.BASE_URL}images/xiaohongjun.png`} alt="小红军数字讲解员形象" onError={() => setImageFailed(true)} />
        <svg className="narrator-face" viewBox="0 0 722 1282" aria-hidden="true">
          <g className="narrator-blink" fill="#d68b5f" stroke="#70351f" strokeWidth="3">
            <path d="M243 321 Q248 252 283 260 Q321 258 320 327 Q287 340 243 321Z" />
            <path d="M386 324 Q384 252 424 252 Q467 254 469 322 Q429 340 386 324Z" />
          </g>
          <g key={speechBeat} className={speechBeat ? "narrator-mouth narrator-mouth-beat" : "narrator-mouth"}>
            <path d="M300 416 Q347 425 408 400 Q385 451 341 448 Q314 445 300 416Z" fill="#652b23" />
            <path d="M309 419 Q353 426 396 408 Q372 432 327 431Z" fill="#ffe4cc" />
            <path d="M330 441 Q352 426 376 436 Q351 450 330 441Z" fill="#df8276" />
          </g>
        </svg>
      </div>
        : <div className="narrator-image-fallback">小红军 · 图片暂不可用</div>}
    </figure>
    <div className="narrator-controls">
      <p className="section-label">数字讲解员</p><h3>小红军 · 证据导读</h3>
      <p>{generationLabel(response)}。{fallback ? "可播放证据节选或全文。" : "可朗读当前回答。"}</p>
      {!supported ? <p role="status">当前浏览器不支持语音朗读，仍可阅读回答和证据。</p> : <>
        <label>讲解音色<select value={voiceId} onChange={e => { stop(); setVoiceId(e.target.value); }}>
          <option value="">自动选择中文音色</option>
          {voices.map((v, i) => <option key={v.voiceURI + i} value={v.voiceURI}>{v.name}{v.localService ? "（设备音色）" : ""}</option>)}
        </select></label>
        <div className="narrator-buttons">
          {fallback && preview ? <button type="button" disabled={!canSpeak || playing}
            onClick={() => play("以下是证据节选。" + preview)}>播放证据节选</button> : null}
          <button type="button" disabled={!canSpeak || playing} onClick={() => play(response.answer)}>{fallback ? "播放证据摘要" : "播放讲解"}</button>
          <button type="button" disabled={state !== "speaking" && state !== "paused"} onClick={pauseOrResume}>{state === "paused" ? "继续讲解" : "暂停讲解"}</button>
          <button type="button" disabled={!playing} onClick={stop}>停止讲解</button>
        </div>
        <p role="status" aria-label="讲解播放状态">{labels[state]}{playing || state === "finished" ? ` · 第${progress}/${segmentCount}段` : ""}</p>
        {!canSpeak ? <p>当前结果为模拟、状态未确认或缺少引用，不能作为正式讲解播放。</p> : null}
        {error ? <p role="alert">{error}</p> : null}
      </>}
    </div>
  </section>;
}
