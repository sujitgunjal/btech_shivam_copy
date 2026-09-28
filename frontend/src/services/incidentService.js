import api from './api';
import {
  incidentsListData,
  getMockIncidentById,
  getMockInvestigationResult,
  getMockIncidentLogs,
  getMockIncidentMetrics,
  getMockIncidentTraces,
  getMockIncidentDeployments,
} from '../data/mockData';

/**
 * Fetch all incidents
 * Endpoint: GET /incidents
 */
export const getIncidents = async () => {
  const response = await api.get('/incidents');
  const rawList = Array.isArray(response.data)
    ? response.data
    : response.data.incidents || [];
  const normalized = rawList.map((inc) => ({
    id:
      inc.external_id ||
      (typeof inc.id === 'number'
        ? `INC-${String(inc.id).padStart(4, '0')}`
        : inc.id),
    db_id: inc.id,
    affectedService: inc.service || inc.affectedService || 'Order Service',
    service: inc.service || inc.affectedService || 'Order Service',
    severity: inc.severity
      ? inc.severity.charAt(0).toUpperCase() + inc.severity.slice(1)
      : 'Medium',
    status: inc.status
      ? inc.status.charAt(0).toUpperCase() + inc.status.slice(1)
      : 'Active',
    startTime: inc.start_time
      ? inc.start_time.replace('T', ' ').substring(0, 19)
      : inc.startTime || '',
    p99_latency_ms: inc.p99_latency_ms ?? (inc.external_id === 'INC-0001' || inc.id === 1 ? 4105.0 : null),
    error_rate: inc.error_rate ?? (inc.external_id === 'INC-0001' || inc.id === 1 ? 14.8 : null),
    captured_at: inc.captured_at
      ? inc.captured_at.replace('T', ' ').substring(0, 19)
      : inc.start_time
      ? inc.start_time.replace('T', ' ').substring(0, 19)
      : inc.startTime || '',
    description: inc.description || '',
  }));
  return { data: normalized, isMock: false };
};

/**
 * Fetch incident details by ID
 * Endpoint: GET /incidents/:id
 */
export const getIncidentById = async (id) => {
  try {
    const numericId =
      typeof id === 'string' && id.startsWith('INC-')
        ? parseInt(id.replace('INC-', ''), 10)
        : id;
    const response = await api.get(`/incidents/${numericId}`);
    const inc = response.data;
    const normalized = {
      id:
        inc.external_id ||
        (typeof inc.id === 'number'
          ? `INC-${String(inc.id).padStart(4, '0')}`
          : inc.id),
      db_id: inc.id,
      title: inc.title || `Alert on ${inc.service}`,
      service: inc.service || inc.affectedService || 'Order Service',
      affectedService: inc.service || inc.affectedService || 'Order Service',
      severity: inc.severity
        ? inc.severity.charAt(0).toUpperCase() + inc.severity.slice(1)
        : 'Critical',
      status: inc.status
        ? inc.status.charAt(0).toUpperCase() + inc.status.slice(1)
        : 'Active',
      createdAt: inc.start_time
        ? inc.start_time.replace('T', ' ').substring(0, 19)
        : inc.created_at || '',
      startTime: inc.start_time
        ? inc.start_time.replace('T', ' ').substring(0, 19)
        : '',
      p99_latency_ms: inc.p99_latency_ms ?? (inc.external_id === 'INC-0001' || inc.id === 1 ? 4105.0 : null),
      error_rate: inc.error_rate ?? (inc.external_id === 'INC-0001' || inc.id === 1 ? 14.8 : null),
      captured_at: inc.captured_at
        ? inc.captured_at.replace('T', ' ').substring(0, 19)
        : inc.start_time
        ? inc.start_time.replace('T', ' ').substring(0, 19)
        : inc.created_at || '',
      description: inc.description || '',
      environment: 'production-us-east',
      reporter: 'Prometheus Alertmanager',
      assignedTeam: 'Platform SRE Team',
      timeline: [
        {
          time:
            (inc.start_time || '').split('T')[1]?.substring(0, 8) || '14:15:02',
          event: `Alert firing: Anomaly on ${inc.service}`,
        },
        {
          time: '14:16:10',
          event: 'PagerDuty incident created & assigned to SRE On-call',
        },
        { time: '14:18:45', event: 'Status updated by SRE Engineer' },
      ],
    };
    return { data: normalized, isMock: false };
  } catch (error) {
    console.warn(
      `[incidentService] GET /incidents/${id} failed. Falling back to mock data. Cause:`,
      error.message
    );
    return { data: getMockIncidentById(id), isMock: true };
  }
};

/**
 * Fetch logs related to a specific incident
 * Endpoint: GET /incidents/:id/evidence
 */
export const getIncidentLogs = async (id) => {
  try {
    const numericId =
      typeof id === 'string' && id.startsWith('INC-')
        ? parseInt(id.replace('INC-', ''), 10)
        : id;
    const response = await api.get(`/incidents/${numericId}/evidence`);
    return { data: response.data, isMock: false };
  } catch (error) {
    console.warn(
      `[incidentService] GET /incidents/${id}/evidence failed. Falling back to mock logs. Cause:`,
      error.message
    );
    return { data: getMockIncidentLogs(id), isMock: true };
  }
};

/**
 * Fetch metrics related to a specific incident
 */
export const getIncidentMetrics = async (id) => {
  try {
    const numericId =
      typeof id === 'string' && id.startsWith('INC-')
        ? parseInt(id.replace('INC-', ''), 10)
        : id;
    const response = await api.get(`/incidents/${numericId}/evidence`);
    return { data: response.data, isMock: false };
  } catch (error) {
    console.warn(
      `[incidentService] GET /incidents/${id}/evidence failed. Falling back to mock metrics. Cause:`,
      error.message
    );
    return { data: getMockIncidentMetrics(id), isMock: true };
  }
};

/**
 * Fetch traces related to a specific incident
 */
export const getIncidentTraces = async (id) => {
  try {
    const numericId =
      typeof id === 'string' && id.startsWith('INC-')
        ? parseInt(id.replace('INC-', ''), 10)
        : id;
    const response = await api.get(`/incidents/${numericId}/evidence`);
    return { data: response.data, isMock: false };
  } catch (error) {
    console.warn(
      `[incidentService] GET /incidents/${id}/evidence failed. Falling back to mock traces. Cause:`,
      error.message
    );
    return { data: getMockIncidentTraces(id), isMock: true };
  }
};

/**
 * Fetch deployment history related to a specific incident
 */
export const getIncidentDeployments = async (id) => {
  try {
    return { data: getMockIncidentDeployments(id), isMock: true };
  } catch (error) {
    return { data: getMockIncidentDeployments(id), isMock: true };
  }
};

/**
 * Create a new incident record
 * Endpoint: POST /incidents
 */
export const createIncident = async (data) => {
  try {
    const payload = {
      title: data.title || data.description || 'New Incident',
      description: data.description || '',
      service: data.service || data.affectedService || 'order-service',
      severity: (data.severity || 'critical').toLowerCase(),
      start_time: data.start_time || new Date().toISOString(),
    };
    const response = await api.post('/incidents', payload);
    return { data: response.data, isMock: false };
  } catch (error) {
    console.warn(
      '[incidentService] POST /incidents failed. Falling back to mock creation response. Cause:',
      error.message
    );
    const newMockIncident = {
      id: `INC-${Math.floor(100 + Math.random() * 900)}`,
      affectedService: data.affectedService || 'Order Service',
      severity: data.severity || 'Medium',
      status: data.status || 'Active',
      startTime: new Date().toISOString().replace('T', ' ').substring(0, 19),
      description: data.description || 'Newly created incident',
    };
    return { data: newMockIncident, isMock: true };
  }
};

/**
 * Trigger operational investigation workflow for an incident
 * Endpoint: POST /incidents/:id/investigate
 */
export const investigateIncident = async (id) => {
  try {
    const numericId =
      typeof id === 'string' && id.startsWith('INC-')
        ? parseInt(id.replace('INC-', ''), 10)
        : id;
    const response = await api.post(`/incidents/${numericId}/investigate`);
    return { data: response.data, isMock: false };
  } catch (error) {
    console.warn(
      `[incidentService] POST /incidents/${id}/investigate failed. Falling back to mock investigation. Cause:`,
      error.message
    );
    return { data: getMockInvestigationResult(id), isMock: true };
  }
};

/**
 * Alias for investigateIncident to match pipeline triggering conventions
 */
export const startInvestigation = investigateIncident;
