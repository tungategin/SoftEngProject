import axios from 'axios';

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, '');
const API_DEBUG = String(import.meta.env.VITE_API_DEBUG || 'true').toLowerCase() === 'true';

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

function normalizeSuccess(response) {
  const body = response && response.data;

  if (body && typeof body === 'object') {
    if (body.ok === true) {
      return {
        ok: true,
        data: body.data || {},
        status: response.status,
        raw: body,
      };
    }

    if (body.ok === false) {
      return {
        ok: false,
        error: body.error || 'operation_failed',
        status: response.status,
        raw: body,
      };
    }
  }

  return {
    ok: false,
    error: 'invalid_response',
    status: response ? response.status : 0,
    raw: body,
  };
}

function normalizeError(error) {
  if (API_DEBUG) {
    const debugPayload = {
      message: error && error.message ? error.message : 'unknown',
      code: error && error.code ? error.code : null,
      baseURL: API_BASE_URL,
      url: error && error.config ? error.config.url : null,
      method: error && error.config ? error.config.method : null,
      hasResponse: Boolean(error && error.response),
      status: error && error.response ? error.response.status : null,
      data: error && error.response ? error.response.data : null,
    };
    console.error('[DEBUG][API] request failed', debugPayload);
  }

  if (error && error.response) {
    const status = error.response.status;
    const payload = error.response.data;

    if (status === 422) {
      return {
        ok: false,
        error: 'validation_error',
        status,
        validation: payload && payload.detail ? payload.detail : [],
        raw: payload,
      };
    }

    return {
      ok: false,
      error: payload && payload.error ? payload.error : 'request_failed',
      status,
      raw: payload,
    };
  }

  return {
    ok: false,
    error: 'network_error',
    status: 0,
    detail:
      (error && error.message ? error.message : 'Unknown network error') +
      ' | Check backend URL / CORS / mixed localhost vs 127.0.0.1 origin.',
    debug: {
      baseURL: API_BASE_URL,
      url: error && error.config ? error.config.url : null,
      method: error && error.config ? error.config.method : null,
      code: error && error.code ? error.code : null,
    },
  };
}

export async function postJson(path, payload) {
  if (API_DEBUG) {
    console.log('[DEBUG][API] POST', {
      baseURL: API_BASE_URL,
      path,
      payload,
    });
  }

  try {
    const response = await http.post(path, payload);
    if (API_DEBUG) {
      console.log('[DEBUG][API] success', {
        path,
        status: response.status,
        body: response.data,
      });
    }
    return normalizeSuccess(response);
  } catch (error) {
    return normalizeError(error);
  }
}
