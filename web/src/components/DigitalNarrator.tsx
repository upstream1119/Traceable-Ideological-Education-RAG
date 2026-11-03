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
    session.current++; active.current = false; utterance.current = null; clearTimer();
    release.current?.(); release.current = null;
    if (supported) { try { window.speechSynthesis.cancel(); } catch { /* 停止时不遮挡正文。 */ } }
    setState("idle"); setProgress(0);
  }
  useEffect(() => {
    setState("idle"); setError(""); setProgress(0);
    return () => {
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
      active.current = false; utterance.current = null; clearTimer();
      release.current?.(); release.current = null;
      try { window.speechSynthesis.cancel(); } catch { /* 原文仍可阅读。 */ }
      setError(message); setState("error");
    }
    function speak(index: number) {
      if (session.current !== token || !active.current) return;
      if (index >= chunks.length) {
        active.current = false; utterance.current = null; clearTimer();
        release.current?.(); release.current = null; setState("finished"); return;
      }
      const u = new window.SpeechSynthesisUtterance(chunks[index]);
      utterance.current = u; u.lang = "zh-CN"; u.rate = 1;
      const voice = voices.find(v => v.voiceURI === voiceId) ?? voices.find(v => v.localService) ?? voices[0];
      if (voice) u.voice = voice;
      setProgress(index + 1);
      u.onstart = () => { if (session.current === token && utterance.current === u && active.current) { clearTimer(); setState("speaking"); } };
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
      if (state === "speaking") { window.speechSynthesis.pause(); setState("paused"); }
      else if (state === "paused") { window.speechSynthesis.resume(); setState("speaking"); }
    } catch { stop(); setError("浏览器未能切换播放状态，请重新播放。"); setState("error"); }
  }
  const playing = state === "starting" || state === "speaking" || state === "paused";
  const labels: Record<SpeechState, string> = {
    idle: "待播放", starting: "正在启动语音", speaking: "正在朗读", paused: "已暂停", finished: "朗读结束", error: "朗读失败",
  };
  return <section className={`digital-narrator ${state === "speaking" ? "is-speaking" : ""}`} aria-label="小红军数字讲解员">
    <figure className="narrator-portrait">
      {!imageFailed ? <img src={`${import.meta.env.BASE_URL}images/xiaohongjun.png`} alt="小红军数字讲解员形象" onError={() => setImageFailed(true)} />
        : <div className="narrator-image-fallback">小红军 · 图片暂不可用</div>}
      <figcaption>二维静态形象 · 讲话状态提示，不含口型动画</figcaption>
    </figure>
    <div className="narrator-controls">
      <p className="section-label">数字讲解员</p><h3>小红军 · 证据导读</h3>
      <p>{generationLabel(response)}。{fallback ? "当前朗读证据摘要，不作为完整人物讲解。" : "朗读当前回答，不另写历史事实。"}</p>
      <p className="guardrail-note">浏览器系统语音，非历史人物原声；音色及可用性由设备提供，部分音色可能需要网络。不会自动播放。</p>
      {!supported ? <p role="status">当前浏览器不支持语音朗读，仍可阅读回答和证据。</p> : <>
        <label>讲解音色<select value={voiceId} onChange={e => { stop(); setVoiceId(e.target.value); }}>
          <option value="">自动选择中文音色</option>
          {voices.map((v, i) => <option key={v.voiceURI + i} value={v.voiceURI}>{v.name}{v.localService ? "（设备音色）" : "（可能需联网）"}</option>)}
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
