/**
 * API Client — Axios instance with base URL and error handling.
 */
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s — analysis can take a while
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.error?.message || error.message || 'An unexpected error occurred';
    console.error('[API Error]', message);
    return Promise.reject(error);
  }
);

export default apiClient;
