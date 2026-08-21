import axios from "axios";

// Create Axios instance with default config
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    // Attempt to get token from localStorage (if in browser)
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("accessToken");
      if (token && config.headers && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling 401s (token expiration)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // If the error is 401 and we have a token, we might want to refresh it or logout.
    // For this hackathon scope, we'll just log out and redirect to login if 401.
    if (error.response?.status === 401 && typeof window !== "undefined") {
      // Don't loop infinitely if the failure was on the login route
      if (!error.config.url.includes("/auth/login")) {
        localStorage.removeItem("accessToken");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
