import React, { useState, useEffect } from 'react';
import {
  Network,
  Bot,
  Wrench,
  ShieldCheck,
  Database,
  CloudSun,
  ArrowRight,
  ArrowDown,
  Info,
  CheckCircle2,
  Code2,
  FileCode,
} from 'lucide-react';
import { fetchArchitecture } from '../services/api';

export const AgentArchitecturePage: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<string>('root_agent');
  const [archData, setArchData] = useState<any | null>(null);

  useEffect(() => {
    fetchArchitecture().then(setArchData).catch(console.error);
  }, []);

  const nodeDetails: Record<string, any> = {
    root_agent: {
      title: "Root Agent (Primary Customer Voice Gateway)",
      type: "Primary Conversational Assistant",
      blocks: {
        role: "Primary customer-facing voice assistant for SteadyHome Home Loans.",
        persona: "Courteous, calm, efficient, strictly professional banking officer tone.",
        context: "Helpline intake point operating under simulated clock 10 November 2026, 09:00 AM IST.",
        task: "Greet caller, capture intent (enquiry, part-payment, late fee), execute borrower identity verification with verify_borrower(), listen for keypad stand-ins (1, 2, 3, 0), and hand off verified sessions cleanly to the EMI Service Sub-Agent.",
        constraints: "Never reveal loan balance before verification; never disclose which individual credential failed; enforce max 2 re-attempts; trigger immediate crisis script if self-harm is detected; escalate on explicit agent request without confirmation."
      },
      tools: ["verify_borrower", "build_handoff_details"],
      few_shot: `Customer: "I want to check my EMI due date." -> Root Agent: "Certainly. First, I need to verify your identity. Please provide your Borrower ID, date of birth, and the last four digits of your loan number."`
    },
    emi_sub_agent: {
      title: "EMI Service Sub-Agent (Domain Specialist)",
      type: "Specialist Home Loan EMI Assistant",
      blocks: {
        role: "Specialist assistant dedicated exclusively to home loan EMI schedules, late fees, and part-payments.",
        persona: "Exact, mathematically precise, compliant with Indian banking lending policies.",
        context: "Servicing verified borrowers; enforcing payment mode rules across 2026/2027 transition boundary.",
        task: "Execute lookup_loan() for due-date inquiries; calculate_late_fee() with 2% and 4% tiers; check_loan_status() for part-payment requests; validate part-payment amount >= ₹500; conduct Confirm Before Acting (V4) protocol before payment transfers.",
        constraints: "Never allow part-payment on CLOSED or DEFAULT loans; reject part-payment < ₹500; block online resolution if > 30 days overdue; play payment disclaimer exactly once upon transfer; never play disclaimer for human handoffs."
      },
      tools: ["lookup_loan", "calculate_late_fee", "check_loan_status", "build_handoff_details"],
      few_shot: `Customer: "I want to make a part payment of ₹499." -> EMI Sub-Agent: "Part-payments below ₹500 cannot be processed online. The minimum permitted amount is ₹500. Would you like to pay ₹500 instead?"`
    },
    tool_verify: {
      title: "Tool: verify_borrower()",
      type: "Python Core Verification Engine",
      signature: "verify_borrower(borrower_id: str, date_of_birth: str, loan_last_four: str, db: Session)",
      responsibilities: [
        "Validates 3-tuple credential match against SQLite core borrowers table.",
        "Prevents credential enumeration: returns unified generic failure message.",
        "Checks status: immediately flags BLOCKED accounts for fraud/recovery escalation.",
        "Tracks attempt counts (maximum 2 retries allowed)."
      ]
    },
    tool_lookup: {
      title: "Tool: lookup_loan()",
      type: "Python Loan Registry Tool",
      signature: "lookup_loan(borrower_id: str, db: Session)",
      responsibilities: [
        "Fetches active loan record, tenure, interest rate, and sanctioned amount.",
        "Retrieves latest pending/overdue installment schedule from EMIs table.",
        "Returns next due date and registered default payment mode."
      ]
    },
    tool_status: {
      title: "Tool: check_loan_status()",
      type: "Python Loan Status Gatekeeper",
      signature: "check_loan_status(loan_id: str, db: Session)",
      responsibilities: [
        "Mandatory pre-flight validation executed for PART-PAYMENT ONLY.",
        "Permits ACTIVE loans to proceed.",
        "Escalates CLOSED and DEFAULT accounts to human agents.",
        "Handles UNKNOWN status with a technical error message without claiming default."
      ]
    },
    tool_late_fee: {
      title: "Tool: calculate_late_fee()",
      type: "Python Financial Rule Engine",
      signature: "calculate_late_fee(emi_amount: float, due_date: str, payment_status: str, simulated_current_date: datetime)",
      responsibilities: [
        "Computes elapsed days between due date and simulated clock (2026-11-10).",
        "Applies 2% for 1-5 days (exactly 5 days belongs to 2%).",
        "Applies 4% for 6-30 days (exactly 30 days belongs to 4%).",
        "Enforces hard boundary: > 30 days overdue disallows online processing.",
        "Rounds fee to nearest whole rupee; exempts already-paid EMIs."
      ]
    },
    guardrails: {
      title: "Safety Guardrails & Compliance Filters",
      type: "Institutional Safety Gateway",
      responsibilities: [
        "Guardrail 1: Card & Aadhaar Protection (16-digit card & 12-digit Aadhaar masked and refused).",
        "Guardrail 2: Crisis & Distress Detection (Tele-MANAS 14416 / 112 emergency escalation).",
        "Guardrail 3: Financial Advice Protection (Mandatory refusal of prepayment recommendations).",
        "Guardrail 4: Prompt Injection Protection (Rejection of system overrides and confidential disclosures)."
      ]
    },
    database: {
      title: "SQLite 3 Relational Database",
      type: "Core Banking Data Store",
      responsibilities: [
        "Stores Borrowers, Loans, EMIs, Payments, Escalations, and InteractionLogs.",
        "Modular SQLAlchemy 2.0 ORM architecture ready for PostgreSQL deployment."
      ]
    },
    advisory_api: {
      title: "Payment-Day Advisory Public API",
      type: "External Public HTTPS Service",
      responsibilities: [
        "Free HTTPS JSON integration with Open-Meteo for regional weather and payment settlement telemetry.",
        "Generates non-binding 1-2 sentence contextual remark without affecting loan calculations."
      ]
    }
  };

  const selectedInfo = nodeDetails[selectedNode] || nodeDetails.root_agent;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-borderCustom">
        <div>
          <h2 className="text-xl font-semibold text-primaryText tracking-tight">
            AI Agent Architecture & Orchestration Topology
          </h2>
          <p className="text-xs text-secondaryText mt-0.5">
            Two-tier conversational agent with Root Agent, EMI Sub-Agent, Python tools, and safety guardrails.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Interactive Node Map (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-borderCustom rounded-lg p-5 shadow-subtle space-y-5">
          <div className="flex items-center justify-between pb-2 border-b border-borderCustom">
            <span className="text-xs font-semibold text-primaryText">Interactive Architecture Topology</span>
            <span className="text-[11px] text-secondaryText">Click any component to inspect specifications</span>
          </div>

          {/* Caller / Audio Ingest */}
          <div className="flex justify-center">
            <div className="px-4 py-2 bg-background-secondary border border-borderCustom rounded text-xs text-center font-medium text-secondaryText w-56">
              🎙️ Caller Ingest (Web Speech API / Text)
            </div>
          </div>

          <div className="flex justify-center">
            <ArrowDown size={16} className="text-secondaryText" />
          </div>

          {/* Tier 1: Root Agent + Guardrails */}
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => setSelectedNode('root_agent')}
              className={`p-4 rounded-lg border text-left transition-all ${
                selectedNode === 'root_agent'
                  ? 'border-brand-blue bg-brand-lightBlue/50 shadow-sm'
                  : 'border-borderCustom bg-white hover:border-brand-blue/50'
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5 text-brand-blue font-semibold text-xs">
                <Bot size={16} />
                <span>ROOT AGENT</span>
              </div>
              <p className="text-[11px] text-secondaryText">
                Greets caller, verifies identity, captures intent, detects crisis, handles keypad stand-ins.
              </p>
            </button>

            <button
              onClick={() => setSelectedNode('guardrails')}
              className={`p-4 rounded-lg border text-left transition-all ${
                selectedNode === 'guardrails'
                  ? 'border-brand-red bg-brand-lightRed/50 shadow-sm'
                  : 'border-borderCustom bg-white hover:border-brand-red/50'
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5 text-brand-red font-semibold text-xs">
                <ShieldCheck size={16} />
                <span>SAFETY GUARDRAILS</span>
              </div>
              <p className="text-[11px] text-secondaryText">
                Card/Aadhaar filtering, Crisis Tele-MANAS script, financial advice refusal, prompt injection check.
              </p>
            </button>
          </div>

          <div className="flex justify-center items-center gap-2 text-xs font-mono text-secondaryText">
            <ArrowDown size={16} className="text-secondaryText" />
            <span className="text-[11px] text-brand-green font-semibold">Session Handoff (Verified Caller)</span>
          </div>

          {/* Tier 2: EMI Service Sub-Agent */}
          <div className="flex justify-center">
            <button
              onClick={() => setSelectedNode('emi_sub_agent')}
              className={`w-full p-4 rounded-lg border text-left transition-all ${
                selectedNode === 'emi_sub_agent'
                  ? 'border-brand-green bg-brand-lightGreen/50 shadow-sm'
                  : 'border-borderCustom bg-white hover:border-brand-green/50'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2 text-brand-green font-semibold text-xs">
                  <Bot size={16} />
                  <span>EMI SERVICE SUB-AGENT</span>
                </div>
                <span className="text-[10px] bg-brand-green text-white px-2 py-0.5 rounded font-medium">Specialist</span>
              </div>
              <p className="text-[11px] text-secondaryText">
                Calculates late fees, validates part-payment amounts (≥ ₹500), enforces loan status gates, executes Confirm Before Acting (V4), and transitions NetPay Plus/Cash Desk modes.
              </p>
            </button>
          </div>

          <div className="flex justify-center">
            <ArrowDown size={16} className="text-secondaryText" />
          </div>

          {/* Tier 3: Python Business Tools */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold text-secondaryText uppercase tracking-wider block">
              Python Backend Tools (Stateless Business Rules)
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { id: 'tool_verify', name: 'verify_borrower()' },
                { id: 'tool_lookup', name: 'lookup_loan()' },
                { id: 'tool_status', name: 'check_loan_status()' },
                { id: 'tool_late_fee', name: 'calculate_late_fee()' },
              ].map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => setSelectedNode(tool.id)}
                  className={`p-2.5 rounded border text-left text-xs font-mono transition-all ${
                    selectedNode === tool.id
                      ? 'border-brand-blue bg-brand-lightBlue text-brand-blue font-semibold shadow-sm'
                      : 'border-borderCustom bg-background-secondary/40 text-primaryText hover:border-brand-blue/40'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <Wrench size={11} className="text-secondaryText" />
                    <span className="truncate">{tool.name}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Tier 4: Database & External APIs */}
          <div className="grid grid-cols-2 gap-4 pt-2 border-t border-borderCustom">
            <button
              onClick={() => setSelectedNode('database')}
              className={`p-3 rounded border text-left text-xs transition-all ${
                selectedNode === 'database'
                  ? 'border-brand-blue bg-brand-lightBlue/40'
                  : 'border-borderCustom bg-white hover:border-brand-blue/40'
              }`}
            >
              <div className="flex items-center gap-1.5 text-primaryText font-semibold mb-1">
                <Database size={14} className="text-brand-blue" />
                <span>SQLite 3 Database</span>
              </div>
              <p className="text-[10px] text-secondaryText">Borrowers, Loans, EMIs, Escalations, Logs</p>
            </button>

            <button
              onClick={() => setSelectedNode('advisory_api')}
              className={`p-3 rounded border text-left text-xs transition-all ${
                selectedNode === 'advisory_api'
                  ? 'border-brand-blue bg-brand-lightBlue/40'
                  : 'border-borderCustom bg-white hover:border-brand-blue/40'
              }`}
            >
              <div className="flex items-center gap-1.5 text-primaryText font-semibold mb-1">
                <CloudSun size={14} className="text-brand-orange" />
                <span>Advisory Public API</span>
              </div>
              <p className="text-[10px] text-secondaryText">Open-Meteo HTTPS weather & clearance</p>
            </button>
          </div>
        </div>

        {/* Right Detail Inspector Panel (5 cols) */}
        <div className="lg:col-span-5 bg-white border border-borderCustom rounded-lg p-5 shadow-subtle flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-borderCustom mb-4">
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-secondaryText block">
                  Component Specification
                </span>
                <h3 className="text-sm font-semibold text-primaryText">{selectedInfo.title}</h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-background-secondary text-primaryText border border-borderCustom">
                {selectedInfo.type}
              </span>
            </div>

            {/* 5-Block Instruction Set if Agent */}
            {selectedInfo.blocks ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-background-secondary/50 rounded border border-borderCustom space-y-2">
                  <div>
                    <span className="font-semibold text-brand-blue block">1. Role:</span>
                    <span className="text-secondaryText">{selectedInfo.blocks.role}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-brand-blue block">2. Persona:</span>
                    <span className="text-secondaryText">{selectedInfo.blocks.persona}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-brand-blue block">3. Context:</span>
                    <span className="text-secondaryText">{selectedInfo.blocks.context}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-brand-blue block">4. Task:</span>
                    <span className="text-secondaryText">{selectedInfo.blocks.task}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-brand-red block">5. Constraints & Mandatory Crisis Rule:</span>
                    <span className="text-secondaryText">{selectedInfo.blocks.constraints}</span>
                  </div>
                </div>

                {selectedInfo.few_shot && (
                  <div className="p-3 bg-brand-lightBlue/30 border border-brand-blueSecondary/20 rounded">
                    <span className="font-semibold text-brand-blue block mb-1">Few-Shot Speech Example:</span>
                    <p className="text-secondaryText italic">{selectedInfo.few_shot}</p>
                  </div>
                )}
              </div>
            ) : (
              /* Responsibilities & Signatures for Tools */
              <div className="space-y-3 text-xs">
                {selectedInfo.signature && (
                  <div className="p-3 bg-background-secondary border border-borderCustom rounded font-mono text-[11px] text-brand-blue break-all">
                    {selectedInfo.signature}
                  </div>
                )}
                <div>
                  <h4 className="font-semibold text-primaryText mb-2">Core Responsibilities & Validation Rules:</h4>
                  <ul className="space-y-2 text-secondaryText">
                    {selectedInfo.responsibilities?.map((item: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 size={13} className="text-brand-green shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Footer Metadata */}
          <div className="pt-4 border-t border-borderCustom mt-4 text-[11px] text-secondaryText flex items-center justify-between">
            <span>Modular Python Architecture</span>
            <span className="font-mono text-primaryText">app/agents & app/tools</span>
          </div>
        </div>
      </div>
    </div>
  );
};

