// -------------------------------
// BACKEND API BASE URL
// -------------------------------
// Use same-origin so it works whether served via Vite or Flask
const API_BASE = "";



// -------------------------------
// GET JOBS (from backend DB)
// -------------------------------
export async function getJobs(status = "new") {
  try {
    const res = await fetch(`${API_BASE}/jobs?status=${status}`);
    return await res.json();
  } catch (err) {
    return { success: false, error: "Cannot reach backend" };
  }
}



// -------------------------------
// APPLY TO JOB
// -------------------------------
export async function applyToJob(jobId) {
  try {
    const res = await fetch(`${API_BASE}/apply/${jobId}`, {
      method: "POST"
    });
    return await res.json();
  } catch (err) {
    return { success: false, error: "Backend error" };
  }
}



// -------------------------------
// SAVE JOB
// -------------------------------
export async function saveJob(jobId) {
  try {
    const res = await fetch(`${API_BASE}/save/${jobId}`, {
      method: "POST"
    });
    return await res.json();
  } catch (err) {
    return { success: false, error: "Backend error" };
  }
}



// -------------------------------
// DENY JOB WITH REASON
// -------------------------------
export async function denyJob(jobId, reason) {
  try {
    const res = await fetch(`${API_BASE}/deny/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason })
    });

    return await res.json();
  } catch (err) {
    return { success: false, error: "Backend error" };
  }
}



// -------------------------------
// UPDATE TRACKING STATUS
// -------------------------------
export async function updateTrackingStatus(jobId, trackingStatus) {
  try {
    const res = await fetch(`${API_BASE}/tracking/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trackingStatus })
    });

    return await res.json();
  } catch (err) {
    return { success: false, error: "Backend error" };
  }
}



// -------------------------------
// MOVE JOB TO NEW COLUMN (new → applied → waiting → denied etc.)
// -------------------------------
export async function moveJobStatus(jobId, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/move/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ newStatus })
    });

    return await res.json();
  } catch (err) {
    return { success: false, error: "Backend error" };
  }
}



// -------------------------------
// RESET (optional — only if backend supports)
// -------------------------------
export async function resetDatabase() {
  try {
    const res = await fetch(`${API_BASE}/reset`, {
      method: "POST"
    });

    return await res.json();
  } catch (err) {
    return { success: false, error: "Backend error" };
  }
}


// -------------------------------
// DELETE JOB (permanent)
// -------------------------------
export async function deleteJob(jobId) {
  try {
    const res = await fetch(`${API_BASE}/delete/${jobId}`, {
      method: "DELETE"
    });
    return await res.json();
  } catch (err) {
    return { success: false, error: "Backend error" };
  }
}
