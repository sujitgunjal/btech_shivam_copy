import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Terminal,
  Play,
  CheckCircle2,
  Loader2,
  Clock,
  Server,
  AlertCircle,
} from 'lucide-react';
import InvestigationResult from '../components/InvestigationResult';
import SeverityBadge from '../components/SeverityBadge';
import DemoDataBadge from '../components/DemoDataBadge';
import { getIncidentById, investigateIncident } from '../services/incidentService';

const STEPS = [
  { id: 1, label: 'Collecting logs', detail: 'Fetching container stdout/stderr & system logs...' },
  { id: 2, label: 'Collecting metrics', detail: 'Querying Prometheus CPU, memory, and latency metrics...' },
  { id: 3, label: 'Collecting traces', detail: 'Analyzing OpenTelemetry distributed trace spans...' },
  { id: 4, label: 'Checking deployment history', detail: 'Inspecting Kubernetes deployment events & git commits...' },
  { id: 5, label: 'Investigation pending', detail: 'Operational data collection completed.' },
];

const InvestigationPage = () => {
  const { id } = useParams();
  const incidentId = id || 'INC-001';

  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isMock, setIsMock] = useState(false);

  // Simulation & Pipeline State
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [isCompleted, setIsCompleted] = useState(false);

  const fetchIncidentDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getIncidentById(incidentId);
      setIncident(res.data || null);
      setIsMock(Boolean(res.isMock));
    } catch (err) {
      console.error('[InvestigationPage] Error loading incident details:', err);
      setError('Failed to fetch target incident for investigation.');
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    fetchIncidentDetails();
  }, [fetchIncidentDetails]);

  const startInvestigation = async () => {
    setIsInvestigating(true);
    setIsCompleted(false);
    setCurrentStepIndex(0);

    // Invoke backend/service investigation API call
    try {
      const res = await investigateIncident(incidentId);
      if (res.isMock) {
        setIsMock(true);
      }
    } catch (err) {
      console.error('[InvestigationPage] Error calling investigateIncident service:', err);
    }
  };

  useEffect(() => {
    if (!isInvestigating) return;

    if (currentStepIndex < STEPS.length - 1) {
      const timer = setTimeout(() => {
        setCurrentStepIndex((prev) => prev + 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      setIsInvestigating(false);
      setIsCompleted(true);
    }
  }, [isInvestigating, currentStepIndex]);

  const affectedService = incident?.affectedService || incident?.service || 'Order Service';
  const severity = incident?.severity || 'Critical';

  const progressPercent =
    currentStepIndex < 0
      ? 0
      : Math.round(((currentStepIndex + 1) / STEPS.length) * 100);

  const investigationStatusText = isCompleted
    ? 'Operational Data Collection Completed'
    : isInvestigating
    ? `In Progress: ${STEPS[currentStepIndex]?.label}`
    : 'Investigation Pending';

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-xs text-slate-500 font-sans">
          <Link to="/incidents" className="hover:text-slate-800 font-medium">
            Incidents
          </Link>
          <span>/</span>
          <span className="text-slate-800 font-bold font-mono">{incidentId}</span>
          <span>/</span>
          <span className="text-[#384959] font-medium">investigate</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-12 flex flex-col items-center justify-center gap-3 text-slate-500 shadow-xs">
          <Loader2 className="h-8 w-8 text-[#384959] animate-spin" />
          <p className="text-xs font-medium">Preparing investigation workbench...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-sans mb-2">
            <Link to="/incidents" className="hover:text-slate-800 font-medium">
              Incidents
            </Link>
            <span>/</span>
            <span className="text-slate-800 font-bold font-mono">{incidentId}</span>
            <span>/</span>
            <span className="text-[#384959] font-medium">investigate</span>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center gap-2.5">
              <Terminal className="h-6 w-6 text-[#384959]" />
              Incident Investigation
            </h1>
            {isMock && <DemoDataBadge />}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-xl flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchIncidentDetails}
            className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-900 rounded font-semibold text-xs"
          >
            Retry
          </button>
        </div>
      )}

      {/* Overview Cards (Incident ID, Affected Service, Status) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Incident ID Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1 shadow-xs">
          <span className="text-xs font-medium text-slate-500 block">Incident</span>
          <div className="text-xl font-bold font-mono text-slate-800 flex items-center gap-2">
            <span>{incidentId}</span>
            <SeverityBadge severity={severity} size="xs" />
          </div>
        </div>

        {/* Affected Service Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1 shadow-xs">
          <span className="text-xs font-medium text-slate-500 block">Affected Service</span>
          <div className="text-xl font-bold text-slate-800 font-sans flex items-center gap-2">
            <Server className="h-5 w-5 text-[#6A89A7]" />
            <span>{affectedService}</span>
          </div>
        </div>

        {/* Investigation Status Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1 shadow-xs">
          <span className="text-xs font-medium text-slate-500 block">Investigation Status</span>
          <div className="text-sm font-bold font-sans flex items-center gap-2">
            {isCompleted ? (
              <span className="text-emerald-700 flex items-center gap-1.5 font-semibold">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                Data Collection Completed
              </span>
            ) : isInvestigating ? (
              <span className="text-amber-700 flex items-center gap-1.5 font-semibold">
                <Loader2 className="h-4 w-4 text-amber-600 animate-spin" />
                In Progress
              </span>
            ) : (
              <span className="text-slate-600 flex items-center gap-1.5 font-medium">
                <Clock className="h-4 w-4 text-slate-400" />
                Investigation Pending
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main Action Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <h2 className="text-base font-semibold text-slate-800">Operational Data Pipeline</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Trigger automated retrieval of logs, metrics, traces, and deployment logs for triage.
            </p>
          </div>

          <button
            onClick={startInvestigation}
            disabled={isInvestigating}
            className={`px-5 py-2.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 shadow-xs ${
              isInvestigating
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
                : 'bg-[#384959] text-white hover:bg-[#2b3844] border border-[#384959]'
            }`}
          >
            {isInvestigating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Running Pipeline ({progressPercent}%)...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-white" />
                <span>{isCompleted ? 'Re-run Investigation' : 'Start Investigation'}</span>
              </>
            )}
          </button>
        </div>

        {/* Progress & Step-by-Step UI */}
        {(isInvestigating || isCompleted || currentStepIndex >= 0) && (
          <div className="space-y-6">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-slate-600">Pipeline Execution Progress</span>
                <span className="text-slate-800 font-mono font-bold">{progressPercent}%</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden border border-slate-200">
                <div
                  className="bg-[#6A89A7] h-full transition-all duration-500 ease-out rounded-full"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            {/* Simulated UI Steps List */}
            <div className="grid grid-cols-1 gap-2.5 font-sans text-xs">
              {STEPS.map((step, idx) => {
                const isStepFinished = idx < currentStepIndex || (isCompleted && idx === 4);
                const isStepActive = idx === currentStepIndex && isInvestigating;

                return (
                  <div
                    key={step.id}
                    className={`p-3.5 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                      isStepFinished
                        ? 'bg-emerald-50/60 border-emerald-200 text-slate-800'
                        : isStepActive
                        ? 'bg-blue-50/60 border-blue-200 text-blue-900 shadow-xs'
                        : 'bg-slate-50 border-slate-200/80 text-slate-400 opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="shrink-0">
                        {isStepFinished ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        ) : isStepActive ? (
                          <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                        ) : (
                          <span className="h-4 w-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px] text-slate-500 font-mono">
                            {step.id}
                          </span>
                        )}
                      </div>
                      <div>
                        <div className="font-semibold text-slate-800">
                          {step.id}. {step.label}
                        </div>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {step.detail}
                        </div>
                      </div>
                    </div>

                    <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border font-medium">
                      {isStepFinished
                        ? 'Completed'
                        : isStepActive
                        ? 'Processing...'
                        : 'Pending'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Completion Banner & AI Integration Placeholder Container */}
      <InvestigationResult isCompleted={isCompleted} statusMessage={investigationStatusText} />
    </div>
  );
};

export default InvestigationPage;
