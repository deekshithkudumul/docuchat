// src/api.config.js
// Automatically uses Railway backend URL in production
// Falls back to localhost in development
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
export default API;