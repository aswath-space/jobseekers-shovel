/**
 * Main application controller.
 */

class App {
    constructor() {
        this.dataLoader = new DataLoader();
        this.appTracker = new ApplicationTracker();
        this.currentView = 'jobs';
        this.filters = { company: '', status: '', search: '' };
        this.sortBy = 'last_seen';
        this.currentJobForApp = null;
    }

    async init() {
        await this.dataLoader.loadJobs();
        await this.dataLoader.loadApplications();
        this.setupEventListeners();
        this.populateCompanyFilter();
        this.renderJobs();
        this.renderApplications();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchView(e.target.dataset.view));
        });

        // Search
        document.getElementById('job-search').addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.renderJobs();
        });

        // Filters
        document.getElementById('company-filter').addEventListener('change', (e) => {
            this.filters.company = e.target.value;
            this.renderJobs();
        });

        document.getElementById('status-filter').addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.renderJobs();
        });

        // Sort
        document.getElementById('sort-by').addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.renderJobs();
        });

        // Modal
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        document.getElementById('app-modal').addEventListener('click', (e) => {
            if (e.target.id === 'app-modal') this.closeModal();
        });

        document.getElementById('job-detail-modal').addEventListener('click', (e) => {
            if (e.target.id === 'job-detail-modal') this.closeJobDetailModal();
        });

        // Application form
        document.getElementById('application-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveApplication();
        });

        // Add application button
        document.getElementById('add-application').addEventListener('click', () => {
            this.openApplicationModal();
        });

        // Export buttons
        document.getElementById('export-jobs-csv').addEventListener('click', () => {
            this.exportJobsCSV();
        });

        document.getElementById('export-jobs-json').addEventListener('click', () => {
            this.exportJobsJSON();
        });

        document.getElementById('export-apps-json').addEventListener('click', () => {
            this.exportApplicationsJSON();
        });
    }

    switchView(view) {
        this.currentView = view;

        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        // Update views
        document.querySelectorAll('.view').forEach(v => {
            v.classList.toggle('active', v.id === `${view}-view`);
        });
    }

    populateCompanyFilter() {
        const companies = this.dataLoader.getCompanies();
        const select = document.getElementById('company-filter');

        companies.forEach(company => {
            const option = document.createElement('option');
            option.value = company.id;
            option.textContent = company.name;
            select.appendChild(option);
        });
    }

    renderJobs() {
        const filtered = this.dataLoader.filterJobs(this.filters);
        const sorted = this.dataLoader.sortJobs(filtered, this.sortBy);
        const container = document.getElementById('jobs-list');

        if (sorted.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:var(--text-secondary);padding:2rem;">No jobs found</p>';
            return;
        }

        container.innerHTML = sorted.map(job => this.renderJobCard(job)).join('');

        // Add click handlers to job cards for detail view
        document.querySelectorAll('.job-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't trigger if clicking on a button or link
                if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A') {
                    this.openJobDetailModal(card.dataset.jobId);
                }
            });
            card.classList.add('job-card-clickable');
        });
    }

    renderJobCard(job) {
        const lastSeen = new Date(job.last_seen).toLocaleDateString();
        const firstSeen = new Date(job.first_seen).toLocaleDateString();
        const hasApplication = this.appTracker.getApplicationByJobId(job.id);

        return `
            <div class="job-card" data-job-id="${job.id}">
                <div class="job-header">
                    <a href="${job.url}" target="_blank" class="job-title">${job.title}</a>
                    <span class="job-status status-${job.status}">${job.status}</span>
                </div>
                <div class="job-meta">
                    <span><strong>${job.company_name}</strong></span>
                    <span>${job.location}</span>
                    <span class="job-classification">${job.classification}</span>
                </div>
                <div class="job-meta">
                    <span>First seen: ${firstSeen}</span>
                    <span>Last seen: ${lastSeen}</span>
                    ${hasApplication ? '<span style="color:var(--success)">✓ Applied</span>' : `<button class="btn-primary" onclick="app.openApplicationModal('${job.id}')">Track Application</button>`}
                </div>
            </div>
        `;
    }

    renderApplications() {
        const apps = this.appTracker.getAllApplications();
        const container = document.getElementById('applications-list');

        if (apps.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:var(--text-secondary);padding:2rem;">No applications tracked yet</p>';
            return;
        }

        container.innerHTML = apps.map(app => this.renderApplicationCard(app)).join('');
    }

    renderApplicationCard(app) {
        const job = this.dataLoader.getJobs().find(j => j.id === app.job_id);
        if (!job) return '';

        const appliedDate = new Date(app.applied_date).toLocaleDateString();
        const needsFollowUp = app.next_follow_up && app.next_follow_up <= new Date().toISOString().split('T')[0];

        return `
            <div class="app-card">
                <div class="app-card-header">
                    <div>
                        <a href="${job.url}" target="_blank" class="job-title">${job.title}</a>
                        <div style="color:var(--text-secondary);font-size:0.875rem;">${job.company_name}</div>
                    </div>
                    <span class="stage-badge stage-${app.stage}">${app.stage}</span>
                </div>
                <div class="job-meta">
                    <span>Applied: ${appliedDate}</span>
                    ${app.next_follow_up ? `<span>Follow-up: ${new Date(app.next_follow_up).toLocaleDateString()}</span>` : ''}
                </div>
                ${app.notes ? `<p style="margin-top:0.5rem;font-size:0.875rem;">${app.notes}</p>` : ''}
                ${needsFollowUp ? '<div class="follow-up-alert">⏰ Follow-up needed!</div>' : ''}
            </div>
        `;
    }

    openApplicationModal(jobId = null) {
        this.currentJobForApp = jobId;
        const modal = document.getElementById('app-modal');
        const form = document.getElementById('application-form');

        form.reset();
        document.getElementById('applied-date').valueAsDate = new Date();

        if (jobId) {
            const job = this.dataLoader.getJobs().find(j => j.id === jobId);
            if (job) {
                document.getElementById('app-job-id').value = jobId;
                document.getElementById('app-job-info').innerHTML = `
                    <strong>${job.title}</strong><br>
                    ${job.company_name} - ${job.location}
                `;
            }
        }

        modal.classList.add('active');
    }

    closeModal() {
        document.getElementById('app-modal').classList.remove('active');
        document.getElementById('job-detail-modal').classList.remove('active');
        this.currentJobForApp = null;
    }

    closeJobDetailModal() {
        document.getElementById('job-detail-modal').classList.remove('active');
    }

    openJobDetailModal(jobId) {
        const job = this.dataLoader.getJobs().find(j => j.id === jobId);
        if (!job) return;

        const modal = document.getElementById('job-detail-modal');
        const title = document.getElementById('job-detail-title');
        const content = document.getElementById('job-detail-content');

        title.textContent = job.title;

        const firstSeen = new Date(job.first_seen).toLocaleDateString();
        const lastSeen = new Date(job.last_seen).toLocaleDateString();
        const hasApplication = this.appTracker.getApplicationByJobId(job.id);

        let html = `
            <div class="job-detail-section">
                <div class="job-detail-meta">
                    <div class="job-detail-meta-item">
                        <strong>Company</strong>
                        <div>${job.company_name}</div>
                    </div>
                    <div class="job-detail-meta-item">
                        <strong>Location</strong>
                        <div>${job.location}</div>
                    </div>
                    <div class="job-detail-meta-item">
                        <strong>Status</strong>
                        <div><span class="job-status status-${job.status}">${job.status}</span></div>
                    </div>
                    <div class="job-detail-meta-item">
                        <strong>Classification</strong>
                        <div><span class="job-classification">${job.classification}</span></div>
                    </div>
                </div>
            </div>

            <div class="job-detail-section">
                <h3>Temporal Tracking</h3>
                <div class="job-detail-meta">
                    <div class="job-detail-meta-item">
                        <strong>First Seen</strong>
                        <div>${firstSeen}</div>
                    </div>
                    <div class="job-detail-meta-item">
                        <strong>Last Seen</strong>
                        <div>${lastSeen}</div>
                    </div>
                    <div class="job-detail-meta-item">
                        <strong>Total Observations</strong>
                        <div>${job.observations ? job.observations.length : 0}</div>
                    </div>
                </div>
            </div>
        `;

        if (job.department) {
            html += `
                <div class="job-detail-section">
                    <h3>Department</h3>
                    <p>${job.department}</p>
                </div>
            `;
        }

        if (job.description) {
            html += `
                <div class="job-detail-section">
                    <h3>Description</h3>
                    <p>${job.description.substring(0, 500)}${job.description.length > 500 ? '...' : ''}</p>
                </div>
            `;
        }

        if (job.classification_reasoning) {
            html += `
                <div class="job-detail-section">
                    <h3>Classification Reasoning</h3>
                    <p>${job.classification_reasoning}</p>
                </div>
            `;
        }

        if (job.observations && job.observations.length > 0) {
            html += `
                <div class="job-detail-section">
                    <h3>Recent Observations</h3>
                    <ul class="observation-list">
            `;

            job.observations.slice(-3).reverse().forEach(obs => {
                const obsDate = new Date(obs.timestamp).toLocaleDateString();
                html += `
                    <li class="observation-item">
                        ${obsDate} - Source: ${obs.source_identifier}
                    </li>
                `;
            });

            html += `</ul></div>`;
        }

        html += `
            <div class="job-detail-actions">
                <a href="${job.url}" target="_blank" class="btn-primary">View Original Posting</a>
                ${!hasApplication ? `<button class="btn-primary" onclick="app.openApplicationModal('${job.id}'); app.closeJobDetailModal();">Track Application</button>` : '<span style="color:var(--success)">✓ Application Tracked</span>'}
            </div>
        `;

        content.innerHTML = html;
        modal.classList.add('active');
    }

    saveApplication() {
        const data = {
            applied_date: document.getElementById('applied-date').value,
            stage: document.getElementById('stage').value,
            notes: document.getElementById('notes').value,
            contact_person: document.getElementById('contact-person').value || null,
            next_follow_up: document.getElementById('next-follow-up').value || null
        };

        this.appTracker.addApplication(this.currentJobForApp, data);
        this.closeModal();
        this.renderJobs();
        this.renderApplications();
    }

    exportJobsCSV() {
        const filtered = this.dataLoader.filterJobs(this.filters);
        const sorted = this.dataLoader.sortJobs(filtered, this.sortBy);

        const headers = ['Company', 'Title', 'Location', 'Status', 'Classification', 'First Seen', 'Last Seen', 'URL'];
        const rows = sorted.map(job => [
            job.company_name,
            job.title,
            job.location,
            job.status,
            job.classification,
            new Date(job.first_seen).toLocaleDateString(),
            new Date(job.last_seen).toLocaleDateString(),
            job.url
        ]);

        const csv = [headers, ...rows].map(row =>
            row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
        ).join('\n');

        this.downloadFile(csv, 'jobs-export.csv', 'text/csv');
    }

    exportJobsJSON() {
        const filtered = this.dataLoader.filterJobs(this.filters);
        const sorted = this.dataLoader.sortJobs(filtered, this.sortBy);

        const json = JSON.stringify(sorted, null, 2);
        this.downloadFile(json, 'jobs-export.json', 'application/json');
    }

    exportApplicationsJSON() {
        const apps = this.appTracker.getAllApplications();
        const json = JSON.stringify(apps, null, 2);
        this.downloadFile(json, 'applications-export.json', 'application/json');
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}

// Make app global for inline event handlers
let app;

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app = new App();
    app.init();
});
