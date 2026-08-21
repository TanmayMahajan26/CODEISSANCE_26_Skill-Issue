/**
 * Nexus360 — Centralized API Client
 * Connects to the FastAPI backend with Bearer JWT token authentication.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  getToken() {
    return localStorage.getItem('nexus360_token');
  }

  setToken(token) {
    if (token) {
      localStorage.setItem('nexus360_token', token);
    } else {
      localStorage.removeItem('nexus360_token');
    }
  }

  getHeaders(customHeaders = {}, isMultipart = false) {
    const headers = { ...customHeaders };
    if (!isMultipart) {
      headers['Content-Type'] = 'application/json';
    }
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const isMultipart = options.body instanceof FormData;
    const headers = this.getHeaders(options.headers, isMultipart);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        // Token expired or invalid
        console.warn('Session expired or unauthorized. Clearing token.');
        this.setToken(null);
        window.dispatchEvent(new Event('auth:unauthorized'));
      }

      if (!response.ok) {
        let errorDetail = `HTTP Error ${response.status}`;
        try {
          const errJson = await response.json();
          errorDetail = errJson.detail || errorDetail;
        } catch {
          // ignore parsing error
        }
        const error = new Error(errorDetail);
        error.status = response.status;
        throw error;
      }

      return await response.json();
    } catch (err) {
      console.warn(`API call to ${endpoint} failed:`, err.message);
      throw err;
    }
  }

  get(endpoint, params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.append(key, value);
      }
    });
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`${endpoint}${queryString}`, { method: 'GET' });
  }

  post(endpoint, body) {
    const isMultipart = body instanceof FormData;
    return this.request(endpoint, {
      method: 'POST',
      body: isMultipart ? body : JSON.stringify(body),
    });
  }

  put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  patch(endpoint, body) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
