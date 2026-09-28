import React from 'react';
import {
  CheckCircle2,
  Brain,
  ShieldCheck,
  FileSearch,
  History,
  Lightbulb,
  Sparkles,
} from 'lucide-react';

/**
 * InvestigationResult component - Light SaaS container for Phase 1 data collection completion
 * and future Phase 2 AI-powered Root Cause Analysis, Confidence Score, Evidence, Timeline & Recommendations.
 */
const InvestigationResult = ({
  isCompleted = false,
  statusMessage = '',
  rootCause = null,
  confidenceScore = null,
  evidence = null,
  timeline = null,
  recommendations = null,
}) => {
  if (!isCompleted) {
    return null;
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 shadow-xs">
      {/* Phase 1 Completion Header Banner */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-emerald-100 text-emerald-700 shrink-0 mt-0.5">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-emerald-900 font-sans">
              Operational Data Collection Completed
            </h3>
            <p className="text-xs text-emerald-800 mt-0.5 leading-relaxed">
              Operational data collection completed.
              <br />
              <span className="text-emerald-700 font-medium">
                AI-powered root cause analysis will be integrated in the next phase.
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 bg-white px-3 py-1.5 rounded-lg border border-emerald-200 shrink-0 text-emerald-800 font-medium text-xs shadow-xs">
          <Sparkles className="h-4 w-4 text-emerald-600" />
          <span>Phase 1 Complete</span>
        </div>
      </div>

      {/* Structured Placeholders for Phase 2 AI Integration */}
      <div className="space-y-4 pt-2 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <Brain className="h-4 w-4 text-[#384959]" />
            AI Root Cause Analysis Engine (Phase 2 Ready)
          </h4>
          <span className="text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded">
            Modular API Slot
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 1. Root Cause Slot */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1.5 text-slate-800 font-semibold">
                <Brain className="h-3.5 w-3.5 text-[#384959]" />
                Root Cause Hypothesis
              </span>
              <span className="text-[10px] text-slate-400">Phase 2 AI</span>
            </div>
            {rootCause ? (
              <p className="text-xs text-slate-700 font-mono">{rootCause}</p>
            ) : (
              <div className="bg-white border border-dashed border-slate-200 rounded-lg p-3 text-xs text-slate-400 font-sans">
                [Root cause analysis placeholder - LLM inference will populate here]
              </div>
            )}
          </div>

          {/* 2. Confidence Score Slot */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1.5 text-slate-800 font-semibold">
                <ShieldCheck className="h-3.5 w-3.5 text-amber-600" />
                Confidence Score
              </span>
              <span className="text-[10px] text-slate-400">Phase 2 Metric</span>
            </div>
            {confidenceScore ? (
              <div className="text-lg font-bold font-mono text-amber-700">{confidenceScore}</div>
            ) : (
              <div className="bg-white border border-dashed border-slate-200 rounded-lg p-3 text-xs text-slate-400 font-sans">
                [Confidence rating e.g., 94% confidence score based on vector embeddings]
              </div>
            )}
          </div>

          {/* 3. Evidence Slot */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1.5 text-slate-800 font-semibold">
                <FileSearch className="h-3.5 w-3.5 text-[#6A89A7]" />
                Evidence & Log Snippets
              </span>
              <span className="text-[10px] text-slate-400">Phase 2 RAG</span>
            </div>
            {evidence ? (
              <div className="text-xs text-slate-700 font-mono">{evidence}</div>
            ) : (
              <div className="bg-white border border-dashed border-slate-200 rounded-lg p-3 text-xs text-slate-400 font-sans">
                [RAG evidence snippets, log stacktraces, and metric anomaly correlates]
              </div>
            )}
          </div>

          {/* 4. Timeline Slot */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1.5 text-slate-800 font-semibold">
                <History className="h-3.5 w-3.5 text-blue-600" />
                Incident Timeline
              </span>
              <span className="text-[10px] text-slate-400">Phase 2 Chronology</span>
            </div>
            {timeline ? (
              <div className="text-xs text-slate-700 font-mono">{timeline}</div>
            ) : (
              <div className="bg-white border border-dashed border-slate-200 rounded-lg p-3 text-xs text-slate-400 font-sans">
                [Automated chronological sequence of events leading to failure]
              </div>
            )}
          </div>
        </div>

        {/* 5. Recommendations Slot */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center gap-1.5 text-slate-800 font-semibold">
              <Lightbulb className="h-3.5 w-3.5 text-yellow-600" />
              Remediation Recommendations
            </span>
            <span className="text-[10px] text-slate-400">Phase 2 Action Plan</span>
          </div>
          {recommendations ? (
            <div className="text-xs text-slate-700 font-mono">{recommendations}</div>
          ) : (
            <div className="bg-white border border-dashed border-slate-200 rounded-lg p-3 text-xs text-slate-400 font-sans">
              [Suggested remediation scripts, rollbacks, or auto-scaling adjustments]
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InvestigationResult;
