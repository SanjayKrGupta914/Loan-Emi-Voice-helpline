import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Mic,
  MicOff,
  PhoneCall,
  PhoneOff,
  RotateCcw,
  Send,
  Volume2,
  VolumeX,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  CheckCircle2,
  Clock,
  Sparkles,
  Bot,
  User,
  Wrench,
  AlertTriangle,
  Lock,
} from 'lucide-react';
import { Waveform } from '../components/Waveform';
import { StatusBadge } from '../components/Badge';
import { useVoice } from '../hooks/useVoice';
import { sendAgentMessage, resetAgentSession } from '../services/api';
import { ConversationStateItem, ChatMessageItem, ToolLogItem } from '../types';

export const VoiceHelplinePage: React.FC = () => {
  const [callActive, setCallActive] = useState<boolean>(false);
  const [callDuration, setCallDuration] = useState<number>(0);
  const [muted, setMuted] = useState<boolean>(false);
  const [inputText, setInputText] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string>(() => `sess_${Date.now()}`);

  const [conversationState, setConversationState] = useState<ConversationStateItem>({
    session_id: sessionId,
    verified: false,
    now_override: '2026-11-10T09:00:00',
    days_overdue: 0,
    verification_attempts: 0,
    clarification_attempts: 0,
    active_agent: 'Root Agent',
    late_fee: 0,
    is_escalated: false,
    awaiting_confirmation: false,
    disclaimer_played: false,
    messages: [
      {
        role: 'agent',
        content: 'Welcome to SteadyHome. How may I help you today?',
        spoken_text: 'Welcome to SteadyHome. How may I help you today?',
        agent_name: 'Root Agent',
        timestamp: new Date().toISOString(),
      },
    ],
    tool_logs: [],
  });

  const [callError, setCallError] = useState<string | null>(null);

  // Refs mirror state so async voice callbacks never read stale values.
  const callActiveRef = useRef<boolean>(false);
  const mutedRef = useRef<boolean>(false);
  const loadingRef = useRef<boolean>(false);
  const sessionIdRef = useRef<string>(sessionId);
  const handleUserMessageRef = useRef<(text: string) => void>(() => {});
  useEffect(() => {
    callActiveRef.current = callActive;
    mutedRef.current = muted;
    sessionIdRef.current = sessionId;
  }, [callActive, muted, sessionId]);

  const {
    isListening,
    isSpeaking,
    transcript,
    isSupported,
    error: voiceError,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  } = useVoice({
    onFinalResult: (text) => {
      if (callActiveRef.current) handleUserMessageRef.current(text);
    },
  });

  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<any>(null);

  // Call duration counter
  useEffect(() => {
    if (callActive) {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      setCallDuration(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [callActive]);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationState.messages, conversationState.tool_logs]);

  const handleStartCall = async () => {
    setCallError(null);
    callActiveRef.current = true;
    setCallActive(true);
    // Fresh backend session for every call so state from a previous call can't leak in.
    const newSession = `sess_${Date.now()}`;
    sessionIdRef.current = newSession;
    setSessionId(newSession);
    let greeting = 'Welcome to SteadyHome. How may I help you today?';
    try {
      const res = await resetAgentSession(newSession);
      if (res && res.session) setConversationState(res.session);
    } catch (_) {
      setCallError('Cannot reach the SteadyHome backend on port 8000. Start it with ./run.sh and retry.');
    }
    if (!callActiveRef.current) return; // hung up while connecting
    // Greeting first; the mic opens only when the greeting finishes, so it never talks over itself.
    if (!mutedRef.current) {
      speak(greeting, () => {
        if (callActiveRef.current && isSupported) startListening();
      });
    } else if (isSupported) {
      startListening();
    }
  };

  const handleEndCall = () => {
    callActiveRef.current = false;
    setCallActive(false);
    stopListening();
    stopSpeaking();
  };

  const handleReset = async () => {
    callActiveRef.current = false;
    stopListening();
    stopSpeaking();
    setCallActive(false);
    setCallError(null);
    const newSession = `sess_${Date.now()}`;
    sessionIdRef.current = newSession;
    setSessionId(newSession);
    try {
      const res = await resetAgentSession(newSession);
      if (res && res.session) {
        setConversationState(res.session);
        return;
      }
    } catch (_) {
      /* fall through to local reset */
    }
    setConversationState({
      session_id: newSession,
      verified: false,
      now_override: '2026-11-10T09:00:00',
      days_overdue: 0,
      verification_attempts: 0,
      clarification_attempts: 0,
      active_agent: 'Root Agent',
      late_fee: 0,
      is_escalated: false,
      awaiting_confirmation: false,
      disclaimer_played: false,
      messages: [
        {
          role: 'agent',
          content: 'Welcome to SteadyHome. How may I help you today?',
          spoken_text: 'Welcome to SteadyHome. How may I help you today?',
          agent_name: 'Root Agent',
          timestamp: new Date().toISOString(),
        },
      ],
      tool_logs: [],
    });
  };

  const handleUserMessage = useCallback(async (text: string) => {
    if (!text.trim() || loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    setInputText('');
    setCallError(null);

    try {
      const turnResult = await sendAgentMessage(sessionIdRef.current, text);
      if (turnResult && turnResult.state) {
        setConversationState(turnResult.state);
        if (callActiveRef.current) {
          if (!mutedRef.current && turnResult.spoken_text) {
            // speak() pauses the mic and resumes it once the agent has finished talking
            speak(turnResult.spoken_text, () => {
              if (turnResult.is_escalated && callActiveRef.current) {
                // Transferred to a human: the AI leg of the call is over
                callActiveRef.current = false;
                setCallActive(false);
                stopListening();
              }
            });
          } else if (turnResult.is_escalated) {
            callActiveRef.current = false;
            setCallActive(false);
            stopListening();
          }
        }
      }
    } catch (err) {
      console.error('Turn execution error:', err);
      setCallError('The helpline backend did not respond. Check that the server is running on port 8000.');
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, [speak, stopListening]);
  handleUserMessageRef.current = handleUserMessage;

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Quick preset queries for demonstration
  const quickActions = [
    { label: "1: Due Date Enquiry", text: "I want to know my EMI due date" },
    { label: "Verify SH-BOR-1001", text: "My Borrower ID is SH-BOR-1001, date of birth is 1985-06-15, and my loan ends in 1001" },
    { label: "2: Part-Payment ₹500", text: "I want to make a part payment of 500 rupees via NetPay" },
    { label: "3: Late Fee Enquiry", text: "What is my late fee charge?" },
    { label: "0: Transfer to Human", text: "Please connect me to a human representative right now" },
    { label: "Crisis Test", text: "I want to end my life because of this loan" },
    { label: "Aadhaar Test", text: "My Aadhaar number is 1234 5678 9012" },
  ];

  return (
    <div className="space-y-4 animate-fadeIn">
      {/* Page Title & Status Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-borderCustom">
        <div>
          <h2 className="text-xl font-semibold text-primaryText tracking-tight">
            AI Voice Helpline – Live Call Center Console
          </h2>
          <p className="text-xs text-secondaryText mt-0.5">
            Real-time interactive voice assistant with verification, tool tracing, and human escalation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1 bg-white border border-borderCustom rounded text-xs text-secondaryText">
            <span className="font-medium text-primaryText">Active Agent:</span>
            <span
              className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                conversationState.active_agent === 'Root Agent'
                  ? 'bg-brand-lightBlue text-brand-blue'
                  : 'bg-brand-lightGreen text-brand-green'
              }`}
            >
              {conversationState.active_agent}
            </span>
          </div>
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-borderCustom rounded text-xs text-secondaryText hover:text-primaryText hover:bg-background-secondary transition-colors"
          >
            <RotateCcw size={13} />
            <span>Reset Call</span>
          </button>
        </div>
      </div>

      {/* 3-Panel Call Center Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 h-[calc(100vh-210px)] min-h-[580px]">
        {/* ================= LEFT PANEL: Conversation Transcript (5 cols) ================= */}
        <div className="lg:col-span-4 bg-white border border-borderCustom rounded-lg flex flex-col shadow-subtle overflow-hidden">
          <div className="px-4 py-3 border-b border-borderCustom bg-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-primaryText">Audit Transcript</span>
              <span className="text-[10px] text-secondaryText font-mono">
                ({conversationState.messages.length} events)
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-brand-green"></span>
              <span className="text-[11px] text-brand-green font-medium">Synced</span>
            </div>
          </div>

          {/* Transcript Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-background-secondary/20">
            {conversationState.messages.map((msg, idx) => {
              const isCustomer = msg.role === 'customer';
              return (
                <div
                  key={idx}
                  className={`flex flex-col ${isCustomer ? 'items-end' : 'items-start'}`}
                >
                  <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] text-secondaryText">
                    {isCustomer ? (
                      <>
                        <span>Customer</span>
                        <User size={11} className="text-brand-blue" />
                      </>
                    ) : (
                      <>
                        <Bot size={11} className="text-brand-green" />
                        <span className="font-medium text-primaryText">{msg.agent_name}</span>
                      </>
                    )}
                    <span className="font-mono text-[10px]">
                      {msg.timestamp ? msg.timestamp.slice(11, 16) : ''}
                    </span>
                  </div>
                  <div
                    className={`max-w-[85%] rounded-lg px-3.5 py-2.5 text-xs leading-relaxed ${
                      isCustomer
                        ? 'bg-brand-blue text-white shadow-subtle'
                        : 'bg-white text-primaryText border border-borderCustom shadow-subtle'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              );
            })}

            {/* Inline Tool Execution Logs in Transcript */}
            {conversationState.tool_logs.map((tool, tIdx) => (
              <div
                key={`t-${tIdx}`}
                className="my-2 p-2 bg-white border border-borderCustom rounded text-[11px] font-mono text-secondaryText shadow-subtle"
              >
                <div className="flex items-center justify-between text-brand-blue font-semibold mb-1">
                  <div className="flex items-center gap-1">
                    <Wrench size={11} />
                    <span>TOOL: {tool.tool_name}()</span>
                  </div>
                  <span className="text-[10px] text-secondaryText">{tool.agent_name}</span>
                </div>
                <div className="text-[10px] text-primaryText truncate">
                  Result: {JSON.stringify(tool.result)}
                </div>
              </div>
            ))}

            <div ref={transcriptEndRef} />
          </div>

          {/* Fallback Text Input */}
          <div className="p-3 border-t border-borderCustom bg-white">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleUserMessage(inputText);
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type customer reply (fallback)..."
                disabled={loading}
                className="flex-1 px-3 py-1.5 text-xs border border-borderCustom rounded bg-background-secondary/40 focus:bg-white focus:outline-none focus:border-brand-blue"
              />
              <button
                type="submit"
                disabled={loading || !inputText.trim()}
                className="p-1.5 bg-brand-blue text-white rounded hover:bg-brand-blue/90 disabled:opacity-40 transition-colors"
              >
                <Send size={14} />
              </button>
            </form>
          </div>
        </div>

        {/* ================= CENTRE PANEL: Call Interface (4 cols) ================= */}
        <div className="lg:col-span-5 bg-white border border-borderCustom rounded-lg flex flex-col justify-between p-6 shadow-subtle">
          {/* Header Status */}
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-borderCustom">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    callActive ? 'bg-brand-green animate-pulse' : 'bg-secondaryText/40'
                  }`}
                />
                <span className="text-xs font-semibold text-primaryText">
                  {callActive ? 'Live Call in Progress' : 'Helpline Ready (On Hook)'}
                </span>
              </div>
              <div className="font-mono text-sm font-semibold text-primaryText bg-background-secondary px-2.5 py-0.5 rounded border border-borderCustom">
                {formatTimer(callDuration)}
              </div>
            </div>

            {/* Audio Waveform & Speech Activity */}
            <div className="mt-5 space-y-3">
              <Waveform
                active={callActive && (isListening || isSpeaking)}
                type={isSpeaking ? 'speaking' : isListening ? 'listening' : 'idle'}
              />

              <div className="text-center">
                <div className="text-xs font-medium text-primaryText">
                  {isSpeaking
                    ? '🔊 Agent is speaking...'
                    : isListening
                    ? '🎙️ Listening to caller...'
                    : callActive
                    ? 'Audio channel idle'
                    : 'Click "Start Call" to open voice session'}
                </div>
                {callActive && transcript && (
                  <div className="text-[11px] italic text-brand-blue mt-1 truncate">“{transcript}”</div>
                )}
                <div className="text-[11px] text-secondaryText mt-0.5">
                  Web Speech Recognition (en-IN) • Browser Text-to-Speech
                </div>
                {(callError || voiceError) && (
                  <div className="mt-2 px-2.5 py-1.5 text-[11px] text-brand-red bg-brand-lightRed border border-brand-red/30 rounded">
                    {callError || voiceError}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Center Call Controls */}
          <div className="py-6 flex flex-col items-center justify-center space-y-4">
            <div className="flex items-center gap-4">
              {/* Mic Toggle */}
              <button
                onClick={() => {
                  if (isListening) stopListening();
                  else startListening();
                }}
                disabled={!callActive}
                className={`p-3.5 rounded-full border transition-all ${
                  isListening
                    ? 'bg-brand-lightGreen text-brand-green border-brand-green shadow-sm'
                    : 'bg-white text-secondaryText border-borderCustom hover:bg-background-secondary disabled:opacity-40'
                }`}
                title={isListening ? 'Mute Microphone' : 'Activate Microphone'}
              >
                {isListening ? <Mic size={20} /> : <MicOff size={20} />}
              </button>

              {/* Big Call Button */}
              {!callActive ? (
                <button
                  onClick={handleStartCall}
                  className="px-6 py-3.5 bg-brand-green text-white font-medium text-sm rounded-full flex items-center gap-2 hover:bg-brand-green/90 shadow-md transition-transform active:scale-95"
                >
                  <PhoneCall size={18} />
                  <span>Start Live Call</span>
                </button>
              ) : (
                <button
                  onClick={handleEndCall}
                  className="px-6 py-3.5 bg-brand-red text-white font-medium text-sm rounded-full flex items-center gap-2 hover:bg-brand-red/90 shadow-md transition-transform active:scale-95"
                >
                  <PhoneOff size={18} />
                  <span>End Call</span>
                </button>
              )}

              {/* TTS Mute */}
              <button
                onClick={() => {
                  if (!muted) stopSpeaking();
                  setMuted(!muted);
                }}
                className={`p-3.5 rounded-full border transition-all ${
                  muted
                    ? 'bg-brand-lightOrange text-brand-orange border-brand-orange shadow-sm'
                    : 'bg-white text-secondaryText border-borderCustom hover:bg-background-secondary'
                }`}
                title={muted ? 'Unmute Audio Speech' : 'Mute Audio Speech'}
              >
                {muted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>
            </div>

            {/* Keypad Stand-in Guide (Section 12, Rule V6) */}
            <div className="w-full bg-background-secondary/60 border border-borderCustom rounded-lg p-3 text-xs">
              <div className="font-semibold text-primaryText text-[11px] uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
                <span>Keypad & Voice Stand-in (Rule V6)</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px] text-secondaryText">
                <div className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-white border border-borderCustom rounded font-mono font-semibold text-primaryText">1</kbd>
                  <span>Due-date enquiry</span>
                </div>
                <div className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-white border border-borderCustom rounded font-mono font-semibold text-primaryText">2</kbd>
                  <span>Part-payment</span>
                </div>
                <div className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-white border border-borderCustom rounded font-mono font-semibold text-primaryText">3</kbd>
                  <span>Late-fee enquiry</span>
                </div>
                <div className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-white border border-borderCustom rounded font-mono font-semibold text-brand-red">0</kbd>
                  <span>Human agent transfer</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Demo Test Injections */}
          <div className="border-t border-borderCustom pt-3">
            <div className="text-[11px] font-medium text-secondaryText mb-2">
              Quick Scenarios (One-Click Testing):
            </div>
            <div className="flex flex-wrap gap-1.5">
              {quickActions.map((qa, i) => (
                <button
                  key={i}
                  onClick={() => handleUserMessage(qa.text)}
                  disabled={loading}
                  className="px-2 py-1 bg-white border border-borderCustom hover:border-brand-blue rounded text-[11px] text-primaryText transition-colors text-left"
                >
                  {qa.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ================= RIGHT PANEL: Customer Information Drawer (3 cols) ================= */}
        <div className="lg:col-span-3 bg-white border border-borderCustom rounded-lg flex flex-col shadow-subtle overflow-hidden">
          <div className="px-4 py-3 border-b border-borderCustom bg-white flex items-center justify-between">
            <span className="text-xs font-semibold text-primaryText">Customer Profile</span>
            {conversationState.verified ? (
              <span className="flex items-center gap-1 text-[11px] font-semibold text-brand-green bg-brand-lightGreen px-2 py-0.5 rounded border border-brand-green/20">
                <ShieldCheck size={12} />
                <span>VERIFIED</span>
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] font-semibold text-secondaryText bg-background-secondary px-2 py-0.5 rounded border border-borderCustom">
                <Lock size={12} />
                <span>UNVERIFIED</span>
              </span>
            )}
          </div>

          <div className="p-4 space-y-4 flex-1 overflow-y-auto text-xs">
            {/* Identity & Account Card */}
            <div className="space-y-2">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-secondaryText">
                Account Details
              </div>
              <div className="p-3 bg-background-secondary/50 border border-borderCustom rounded space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-secondaryText">Borrower ID:</span>
                  <span className="font-mono font-medium text-primaryText">
                    {conversationState.borrower_id || 'Not verified'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondaryText">Borrower Name:</span>
                  <span className="font-medium text-primaryText">
                    {conversationState.borrower_name || '--'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondaryText">Attempts:</span>
                  <span className="font-mono text-secondaryText">
                    {conversationState.verification_attempts} / 3
                  </span>
                </div>
              </div>
            </div>

            {/* Protected Loan Information (Section 5.A: Never reveal before verification!) */}
            <div className="space-y-2">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-secondaryText">
                Loan & EMI Schedule
              </div>
              {!conversationState.verified ? (
                <div className="p-4 bg-background-secondary/30 border border-dashed border-borderCustom rounded text-center text-secondaryText space-y-1">
                  <Lock size={16} className="mx-auto text-secondaryText" />
                  <p className="text-[11px] font-medium text-primaryText">Protected Loan Data</p>
                  <p className="text-[10px]">
                    Identity verification required to unlock EMI amounts and due dates.
                  </p>
                </div>
              ) : (
                <div className="p-3 bg-white border border-borderCustom rounded space-y-2">
                  <div className="flex justify-between">
                    <span className="text-secondaryText">Loan ID:</span>
                    <span className="font-mono font-medium text-brand-blue">
                      {conversationState.loan_id}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondaryText">Loan Status:</span>
                    <StatusBadge status={conversationState.loan_status || 'ACTIVE'} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondaryText">Next EMI Due:</span>
                    <span className="font-mono font-medium text-primaryText">
                      {conversationState.due_date || '--'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondaryText">EMI Amount:</span>
                    <span className="font-semibold text-primaryText">
                      ₹{conversationState.emi_amount ? conversationState.emi_amount.toLocaleString('en-IN') : '--'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondaryText">Days Overdue:</span>
                    <span className={`font-mono font-semibold ${conversationState.days_overdue > 0 ? 'text-brand-orange' : 'text-brand-green'}`}>
                      {conversationState.days_overdue} days
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondaryText">Late Fee:</span>
                    <span className="font-mono font-semibold text-brand-orange">
                      ₹{conversationState.late_fee}
                    </span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-borderCustom">
                    <span className="text-secondaryText">Payment Mode:</span>
                    <span className="font-medium text-primaryText">
                      {conversationState.payment_mode || 'AutoDebit'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Escalation Status */}
            {conversationState.is_escalated && (
              <div className="p-3 bg-brand-lightRed border border-brand-red/30 rounded space-y-1">
                <div className="flex items-center gap-1.5 text-brand-red font-semibold text-xs">
                  <AlertTriangle size={14} />
                  <span>Escalated to Human Desk</span>
                </div>
                <div className="text-[11px] text-primaryText">
                  Ref: <span className="font-mono font-medium">{conversationState.escalation_id}</span>
                </div>
                <div className="text-[11px] text-secondaryText truncate" title={conversationState.transfer_reason || ''}>
                  Reason: {conversationState.transfer_reason}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

