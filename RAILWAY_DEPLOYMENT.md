# Railway Deployment Guide

This document contains important instructions for deploying and configuring the SVU Helper Dashboard on Railway.

## Required Environment Variables

For the dashboard to function correctly on Railway, you **must** ensure the following environment variables are set in your Railway project settings:

*   **`DASHBOARD_USER`**: The username for the admin login (e.g., `admin`).
*   **`DASHBOARD_PASS`**: The password for the admin login.
*   **`JWT_SECRET_KEY`**: A secure secret key used for signing JWT tokens. 
    *   *You can generate a secure key by running `openssl rand -hex 32` in your terminal.*
*   **`MONGO_URI`**: Your MongoDB Atlas connection string (this should already be set for the bot).
*   **`DASHBOARD_CORS_ORIGIN`**: (Optional) If your API and UI ever run on different domains, set this to the UI's public URL. Since both run from the same Railway app currently, this isn't strictly necessary, but good to know.

## Expected Behavior

When you first deploy the dashboard and log in, the charts will show **"no data"** placeholders (like "Revenue data will appear as projects are completed"). 

This is expected behavior. The charts and statistics will populate automatically as soon as actual projects flow through the bot and are logged into the database.
