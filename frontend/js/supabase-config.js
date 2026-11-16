/**
 * Srinivasa Textiles - Cloud & Backend Deployment Configuration
 * Centralized configuration for Supabase Database and Vercel Serverless Backend.
 */

// 1. SUPABASE DATABASE CONFIGURATION
window.SUPABASE_CONFIG = {
  // Your Supabase Project URL
  SUPABASE_URL: "https://xanpwoxqwidruibavovz.supabase.co",

  // Your Supabase Public Anonymous API Key (anon / public)
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndtYWZrcGd5anR3b2dlem1tcHZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc4MDIxNjYsImV4cCI6MjEwMzM3ODE2Nn0.7NWBHKvgjlTJ_BB5AhsdSx2hID7Nh6tMsbOS7AU-WQY"
};

// 2. VERCEL BACKEND API URL CONFIGURATION
// Automatically connects to local backend when developing, or to Vercel when deployed on GitHub Pages.
(function () {
  const isLocal = typeof window !== "undefined" && window.location && (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.protocol === "file:"
  );

  // Set your Vercel URL below (e.g. "https://your-project.vercel.app/api")
  const VERCEL_API_URL = "https://srinivasa-textiles.vercel.app/api";

  window.SRINIVASA_API_BASE = isLocal ? "http://localhost:5500/api" : VERCEL_API_URL;
  window.API_BASE_URL = window.SRINIVASA_API_BASE;
})();
