import { getJobs, applyToJob, saveJob, denyJob, updateTrackingStatus, moveJobStatus } from './api.js';

const STATE = {
  currentPage: 'dashboard',
  jobs: [],
  currentJobId: null,
  searchQuery: '',
  sortBy: 'date-desc'
};

function init() {
  setupEventListeners();
  loadInitialData();
  handleRouting();
}

function setupEventListeners() {
  document.getElementById('menuToggle').addEventListener('click', toggleSidebar);
  document.getElementById('filterBtn').addEventListener('click', toggleFilters);
  document.getElementById('searchInput').addEventListener('input', handleSearch);
  document.getElementById('sortDropdown').addEventListener('change', handleSort);

  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', handleNavigation);
  });

  document.getElementById('modalOverlay').addEventListener('click', closeModals);
  document.getElementById('closeApplyModal').addEventListener('click', closeApplyModal);
  document.getElementById('cancelApply').addEventListener('click', closeApplyModal);
  document.getElementById('confirmApply').addEventListener('click', confirmApply);

  document.getElementById('closeDenyModal').addEventListener('click', closeDenyModal);
  document.getElementById('cancelDeny').addEventListener('click', closeDenyModal);
  document.getElementById('confirmDeny').addEventListener('click', confirmDeny);

  window.addEventListener('hashchange', handleRouting);
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('open');
}

function toggleFilters() {
  const filtersBar = document.getElementById('filtersBar');
  if (filtersBar.style.display === 'none' || !filtersBar.style.display) {
    filtersBar.style.display = 'flex';
  } else {
    filtersBar.style.display = 'none';
  }
}

function handleSearch(e) {
  STATE.searchQuery = e.target.value.toLowerCase();
  renderCurrentPage();
}

function handleSort(e) {
  STATE.sortBy = e.target.value;
  renderCurrentPage();
}

function handleNavigation(e) {
  e.preventDefault();
  const page = e.currentTarget.dataset.page;
  window.location.hash = page;
}

function handleRouting() {
  const hash = window.location.hash.slice(1) || 'dashboard';
  navigateToPage(hash);
}

async function navigateToPage(page) {
  STATE.currentPage = page;

  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    if (item.dataset.page === page) {
      item.classList.add('active');
    }
  });

  document.querySelectorAll('.page').forEach(p => {
    p.style.display = 'none';
  });

  const pageElement = document.getElementById(`${page}Page`);
  if (pageElement) {
    pageElement.style.display = 'block';
  }

  if (window.innerWidth < 1024) {
    document.getElementById('sidebar').classList.remove('open');
  }

  await loadPageData(page);
}

async function loadInitialData() {
    const response = await fetch("/data");
    const data = await response.json();

    console.log(data);

    STATE.jobs = data;  
    updateCounts();      
    renderCurrentPage();
}


async function loadPageData(page) {
  const statusMap = {
    'dashboard': 'new',
    'applied': 'applied',
    'waiting': 'waiting',
    'history': 'denied'
  };

  const status = statusMap[page];
  if (!status) return;

  try {
    const response = await getJobs(status);
    if (response.success) {
      renderJobs(page, response.data);
    } else {
      throw new Error(response.error || 'Backend error');
    }
  } catch (error) {
    showToast('Error', 'Failed to load jobs', 'error');
  }
}

function renderCurrentPage() {
  loadPageData(STATE.currentPage);
}

function renderJobs(page, jobs) {
  const containerMap = {
    'dashboard': 'jobsContainer',
    'applied': 'appliedContainer',
    'waiting': 'waitingContainer',
    'history': 'historyContainer'
  };

  const containerId = containerMap[page];
  const container = document.getElementById(containerId);
  const emptyState = document.getElementById(`emptyState${page.charAt(0).toUpperCase() + page.slice(1)}`);
  const loader = document.getElementById('loader');

  if (loader && page === 'dashboard') {
    loader.style.display = 'none';
  }

  let filteredJobs = jobs;

  if (STATE.searchQuery) {
    filteredJobs = jobs.filter(job =>
      job.job_title.toLowerCase().includes(STATE.searchQuery) ||
      job.company.toLowerCase().includes(STATE.searchQuery) ||
      job.location.toLowerCase().includes(STATE.searchQuery) ||
      job.skills.some(skill => skill.toLowerCase().includes(STATE.searchQuery))
    );
  }

  filteredJobs = sortJobs(filteredJobs);

  if (filteredJobs.length === 0) {
    container.innerHTML = '';
    if (emptyState) emptyState.style.display = 'flex';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';

  container.innerHTML = filteredJobs.map(job => createJobCard(job, page)).join('');

  attachJobCardListeners();
}

function sortJobs(jobs) {
  const sorted = [...jobs];

  switch (STATE.sortBy) {
    case 'date-desc':
      sorted.sort((a, b) => new Date(b.posted_date) - new Date(a.posted_date));
      break;
    case 'date-asc':
      sorted.sort((a, b) => new Date(a.posted_date) - new Date(b.posted_date));
      break;
    case 'company':
      sorted.sort((a, b) => a.company.localeCompare(b.company));
      break;
  }

  return sorted;
}

function createJobCard(job, page) {
  const initials = job.company.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
  const postedDate = formatDate(job.posted_date);
  const statusBadge = getStatusBadge(job);

  let actions = '';

  if (page === 'dashboard') {
    actions = `
      <button class="btn btn-primary apply-btn" data-job-id="${job.job_id}">Apply</button>
      <button class="btn btn-secondary save-btn" data-job-id="${job.job_id}">Save for Later</button>
      <button class="btn btn-ghost deny-btn" data-job-id="${job.job_id}">Not Interested</button>
    `;
  } else if (page === 'applied') {
    actions = `
      <select class="status-select" data-job-id="${job.job_id}">
        <option value="pending" ${job.tracking_status === 'pending' ? 'selected' : ''}>Pending</option>
        <option value="under-review" ${job.tracking_status === 'under-review' ? 'selected' : ''}>Under Review</option>
        <option value="shortlisted" ${job.tracking_status === 'shortlisted' ? 'selected' : ''}>Shortlisted</option>
        <option value="rejected" ${job.tracking_status === 'rejected' ? 'selected' : ''}>Rejected</option>
        <option value="offer" ${job.tracking_status === 'offer' ? 'selected' : ''}>Offer</option>
      </select>
      <button class="btn btn-ghost move-waiting-btn" data-job-id="${job.job_id}">Move to Waiting</button>
    `;
  } else if (page === 'waiting') {
    actions = `
      <button class="btn btn-primary apply-btn" data-job-id="${job.job_id}">Apply Now</button>
      <button class="btn btn-ghost deny-btn" data-job-id="${job.job_id}">Remove</button>
    `;
  } else if (page === 'history') {
    actions = `
      <button class="btn btn-secondary restore-btn" data-job-id="${job.job_id}">Restore to Dashboard</button>
    `;
  }

  return `
    <div class="job-card" data-job-id="${job.job_id}">
      <div class="job-card-header">
        <div class="company-logo">${initials}</div>
        <div class="job-card-info">
          <div class="job-card-title-row">
            <h3 class="job-title">${job.job_title}</h3>
            ${statusBadge}
          </div>
          <div class="job-meta">
            <span class="job-meta-item">${job.company}</span>
            <span class="job-meta-item">${job.location}</span>
            <span class="job-meta-item">${postedDate}</span>
          </div>
        </div>
      </div>
      <p class="job-snippet">${job.snippet}</p>
      <div class="job-skills">
        ${job.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
      </div>
      <div class="job-card-actions">
        ${actions}
        <a href="${job.link}" target="_blank" rel="noopener noreferrer" class="btn btn-ghost">View Details</a>
      </div>
    </div>
  `;
}

function getStatusBadge(job) {
  if (job.status === 'applied' && job.tracking_status) {
    const statusText = job.tracking_status.replace('-', ' ');
    return `<span class="status-badge ${job.tracking_status}">${statusText}</span>`;
  }

  const statusMap = {
    'new': 'New',
    'waiting': 'Saved',
    'denied': 'Denied',
    'applied': 'Applied'
  };

  const statusClass = job.status;
  const statusText = statusMap[job.status] || job.status;

  return `<span class="status-badge ${statusClass}">${statusText}</span>`;
}

function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function attachJobCardListeners() {
  document.querySelectorAll('.apply-btn').forEach(btn => {
    btn.addEventListener('click', handleApplyClick);
  });

  document.querySelectorAll('.save-btn').forEach(btn => {
    btn.addEventListener('click', handleSaveClick);
  });

  document.querySelectorAll('.deny-btn').forEach(btn => {
    btn.addEventListener('click', handleDenyClick);
  });

  document.querySelectorAll('.status-select').forEach(select => {
    select.addEventListener('change', handleStatusChange);
  });

  document.querySelectorAll('.move-waiting-btn').forEach(btn => {
    btn.addEventListener('click', handleMoveToWaiting);
  });

  document.querySelectorAll('.restore-btn').forEach(btn => {
    btn.addEventListener('click', handleRestore);
  });
}

function handleApplyClick(e) {
  const jobId = e.currentTarget.dataset.jobId;
  STATE.currentJobId = jobId;

  const job = STATE.jobs.find(j => j.job_id === jobId);
  if (!job) return;

  const summaryHtml = `
    <h4>${job.job_title}</h4>
    <p>${job.company} - ${job.location}</p>
  `;

  document.getElementById('applySummary').innerHTML = summaryHtml;
  openModal('applyModal');
}

async function confirmApply() {
  if (!STATE.currentJobId) return;

  try {
    const response = await applyToJob(STATE.currentJobId);
    if (response.success) {
      const jobIndex = STATE.jobs.findIndex(j => j.job_id === STATE.currentJobId);
      if (jobIndex !== -1) {
        STATE.jobs[jobIndex] = response.data;
      }

      showToast('Success', 'Application submitted successfully!', 'success');
      closeApplyModal();
      updateCounts();
      renderCurrentPage();
    }
  } catch (error) {
    showToast('Error', 'Failed to apply to job', 'error');
  }
}

async function handleSaveClick(e) {
  const jobId = e.currentTarget.dataset.jobId;

  try {
    const response = await saveJob(jobId);
    if (response.success) {
      const jobIndex = STATE.jobs.findIndex(j => j.job_id === jobId);
      if (jobIndex !== -1) {
        STATE.jobs[jobIndex] = response.data;
      }

      showToast('Saved', 'Job saved to waiting list', 'info');
      updateCounts();
      renderCurrentPage();
    }
  } catch (error) {
    showToast('Error', 'Failed to save job', 'error');
  }
}

function handleDenyClick(e) {
  const jobId = e.currentTarget.dataset.jobId;
  STATE.currentJobId = jobId;
  openModal('denyModal');
}

async function confirmDeny() {
  if (!STATE.currentJobId) return;

  const reason = document.getElementById('denyReason').value;

  try {
    const response = await denyJob(STATE.currentJobId, reason);
    if (response.success) {
      const jobIndex = STATE.jobs.findIndex(j => j.job_id === STATE.currentJobId);
      if (jobIndex !== -1) {
        STATE.jobs[jobIndex] = response.data;
      }

      showToast('Success', 'Job moved to history', 'info');
      closeDenyModal();
      updateCounts();
      renderCurrentPage();
    }
  } catch (error) {
    showToast('Error', 'Failed to deny job', 'error');
  }
}

async function handleStatusChange(e) {
  const jobId = e.currentTarget.dataset.jobId;
  const newStatus = e.currentTarget.value;

  try {
    const response = await updateTrackingStatus(jobId, newStatus);
    if (response.success) {
      const jobIndex = STATE.jobs.findIndex(j => j.job_id === jobId);
      if (jobIndex !== -1) {
        STATE.jobs[jobIndex] = response.data;
      }

      showToast('Updated', 'Tracking status updated', 'success');
      renderCurrentPage();
    }
  } catch (error) {
    showToast('Error', 'Failed to update status', 'error');
  }
}

async function handleMoveToWaiting(e) {
  const jobId = e.currentTarget.dataset.jobId;

  try {
    const response = await moveJobStatus(jobId, 'waiting');
    if (response.success) {
      const jobIndex = STATE.jobs.findIndex(j => j.job_id === jobId);
      if (jobIndex !== -1) {
        STATE.jobs[jobIndex] = response.data;
      }

      showToast('Moved', 'Job moved to waiting list', 'info');
      updateCounts();
      renderCurrentPage();
    }
  } catch (error) {
    showToast('Error', 'Failed to move job', 'error');
  }
}

async function handleRestore(e) {
  const jobId = e.currentTarget.dataset.jobId;

  try {
    const response = await moveJobStatus(jobId, 'new');
    if (response.success) {
      const jobIndex = STATE.jobs.findIndex(j => j.job_id === jobId);
      if (jobIndex !== -1) {
        STATE.jobs[jobIndex] = response.data;
      }

      showToast('Restored', 'Job restored to dashboard', 'success');
      updateCounts();
      renderCurrentPage();
    }
  } catch (error) {
    showToast('Error', 'Failed to restore job', 'error');
  }
}

function updateCounts() {
  const counts = {
    dashboard: STATE.jobs.filter(j => j.status === 'new').length,
    applied: STATE.jobs.filter(j => j.status === 'applied').length,
    waiting: STATE.jobs.filter(j => j.status === 'waiting').length,
    history: STATE.jobs.filter(j => j.status === 'denied').length
  };

  document.getElementById('dashboardCount').textContent = counts.dashboard;
  document.getElementById('appliedCount').textContent = counts.applied;
  document.getElementById('waitingCount').textContent = counts.waiting;
  document.getElementById('historyCount').textContent = counts.history;
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  const overlay = document.getElementById('modalOverlay');

  overlay.classList.add('active');
  modal.classList.add('active');
}

function closeModals() {
  document.querySelectorAll('.modal').forEach(modal => {
    modal.classList.remove('active');
  });
  document.getElementById('modalOverlay').classList.remove('active');
}

function closeApplyModal() {
  document.getElementById('applyModal').classList.remove('active');
  document.getElementById('modalOverlay').classList.remove('active');
  STATE.currentJobId = null;
}

function closeDenyModal() {
  document.getElementById('denyModal').classList.remove('active');
  document.getElementById('modalOverlay').classList.remove('active');
  STATE.currentJobId = null;
}

function showToast(title, message, type = 'info') {
  const container = document.getElementById('toast-container');

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close" aria-label="Close">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 4L4 12M4 4l8 8" stroke-linecap="round"/>
      </svg>
    </button>
  `;

  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => {
    toast.remove();
  });

  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 5000);
}

document.addEventListener('DOMContentLoaded', init);
