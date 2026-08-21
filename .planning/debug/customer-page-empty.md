---
status: investigating
trigger: bro customer wala page is empty and uske wajah se everything is empty on localhost
---
# Symptoms
- Expected behavior: Customer page should load with data
- Actual behavior: Customer page is empty, everything is empty on localhost. The browser console shows `ERR_CONNECTION_REFUSED` for the frontend and backend.
- Error messages: `TypeError: Failed to fetch` at `ApiClient.request` (/matching/stats)
- Timeline: Unknown, just started happening
- Reproduction: Open http://localhost:5173/

# Current Focus
- hypothesis: The local backend and frontend servers are currently not running, causing the page to be empty due to network requests failing.
- next_action: Restart the local servers and verify if the page loads correctly.
