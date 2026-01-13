/**
 * Data loader for JSON artifacts.
 * Loads job and application data from backend JSON files.
 */

class DataLoader {
    constructor() {
        this.jobsData = null;
        this.applicationsData = null;
        this.dataPath = '../data/jobs/jobs-v1.json';
        this.appsPath = '../data/applications/applications-v1.json';
    }

    /**
     * Load jobs data from JSON file.
     * @returns {Promise<Object>} Jobs data
     */
    async loadJobs() {
        try {
            const response = await fetch(this.dataPath);
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            this.jobsData = await response.json();
            console.log(`Loaded ${this.jobsData.job_count} jobs`);
            return this.jobsData;
        } catch (error) {
            console.error('Failed to load jobs:', error);
            return { version: '1.0.0', jobs: [], job_count: 0 };
        }
    }

    /**
     * Load applications data from JSON file.
     * @returns {Promise<Object>} Applications data
     */
    async loadApplications() {
        try {
            const response = await fetch(this.appsPath);
            if (!response.ok) {
                // Applications file may not exist yet
                return { version: '1.0.0', applications: [] };
            }
            this.applicationsData = await response.json();
            return this.applicationsData;
        } catch (error) {
            console.error('Failed to load applications:', error);
            return { version: '1.0.0', applications: [] };
        }
    }

    /**
     * Get all jobs.
     * @returns {Array} Array of job objects
     */
    getJobs() {
        return this.jobsData?.jobs || [];
    }

    /**
     * Get jobs filtered by criteria.
     * @param {Object} filters Filter criteria
     * @returns {Array} Filtered jobs
     */
    filterJobs(filters) {
        let jobs = this.getJobs();

        if (filters.company) {
            jobs = jobs.filter(j => j.company_id === filters.company);
        }

        if (filters.status) {
            jobs = jobs.filter(j => j.status === filters.status);
        }

        if (filters.search) {
            const search = filters.search.toLowerCase();
            jobs = jobs.filter(j =>
                j.title.toLowerCase().includes(search) ||
                j.company_name.toLowerCase().includes(search) ||
                j.location.toLowerCase().includes(search)
            );
        }

        return jobs;
    }

    /**
     * Sort jobs by field.
     * @param {Array} jobs Jobs to sort
     * @param {string} sortBy Field to sort by
     * @returns {Array} Sorted jobs
     */
    sortJobs(jobs, sortBy) {
        const sorted = [...jobs];

        switch (sortBy) {
            case 'last_seen':
                sorted.sort((a, b) => new Date(b.last_seen) - new Date(a.last_seen));
                break;
            case 'first_seen':
                sorted.sort((a, b) => new Date(b.first_seen) - new Date(a.first_seen));
                break;
            case 'company':
                sorted.sort((a, b) => a.company_name.localeCompare(b.company_name));
                break;
            case 'title':
                sorted.sort((a, b) => a.title.localeCompare(b.title));
                break;
        }

        return sorted;
    }

    /**
     * Get unique company list.
     * @returns {Array} Array of {id, name} objects
     */
    getCompanies() {
        const jobs = this.getJobs();
        const companies = new Map();

        jobs.forEach(job => {
            companies.set(job.company_id, job.company_name);
        });

        return Array.from(companies.entries()).map(([id, name]) => ({ id, name }));
    }
}

// Export for use in app.js
window.DataLoader = DataLoader;
