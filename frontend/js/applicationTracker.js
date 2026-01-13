/**
 * Application tracking with LocalStorage persistence.
 */

class ApplicationTracker {
    constructor() {
        this.storageKey = 'jobseekers_applications';
        this.applications = this.loadFromStorage();
    }

    loadFromStorage() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.error('Failed to load applications:', e);
            return [];
        }
    }

    saveToStorage() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.applications));
        } catch (e) {
            console.error('Failed to save applications:', e);
        }
    }

    addApplication(jobId, data) {
        const application = {
            id: this.generateId(),
            job_id: jobId,
            applied_date: data.applied_date || new Date().toISOString().split('T')[0],
            stage: data.stage || 'applied',
            notes: data.notes || '',
            contact_person: data.contact_person || null,
            referral_source: data.referral_source || null,
            salary_info: data.salary_info || null,
            follow_ups: [],
            next_follow_up: data.next_follow_up || null,
            created_at: new Date().toISOString()
        };

        this.applications.push(application);
        this.saveToStorage();
        return application;
    }

    updateApplication(id, updates) {
        const app = this.applications.find(a => a.id === id);
        if (!app) return false;

        Object.assign(app, updates);
        app.updated_at = new Date().toISOString();
        this.saveToStorage();
        return true;
    }

    addFollowUp(applicationId, followUpData) {
        const app = this.applications.find(a => a.id === applicationId);
        if (!app) return false;

        const followUp = {
            timestamp: new Date().toISOString(),
            type: followUpData.type || 'follow-up',
            notes: followUpData.notes || ''
        };

        app.follow_ups.push(followUp);
        this.saveToStorage();
        return true;
    }

    deleteApplication(id) {
        const index = this.applications.findIndex(a => a.id === id);
        if (index === -1) return false;

        this.applications.splice(index, 1);
        this.saveToStorage();
        return true;
    }

    getApplication(id) {
        return this.applications.find(a => a.id === id);
    }

    getApplicationByJobId(jobId) {
        return this.applications.find(a => a.job_id === jobId);
    }

    getAllApplications() {
        return this.applications;
    }

    getApplicationsNeedingFollowUp() {
        const today = new Date().toISOString().split('T')[0];
        return this.applications.filter(app =>
            app.next_follow_up && app.next_follow_up <= today
        );
    }

    generateId() {
        return 'app_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    exportToJSON() {
        return JSON.stringify({
            version: '1.0.0',
            exported_at: new Date().toISOString(),
            applications: this.applications
        }, null, 2);
    }
}

window.ApplicationTracker = ApplicationTracker;
