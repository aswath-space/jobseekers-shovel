/**
 * Data export utilities for CSV and JSON formats.
 */

class DataExporter {
    exportJobsToCSV(jobs) {
        const headers = ['Company', 'Title', 'Location', 'Status', 'Classification', 'First Seen', 'Last Seen', 'URL'];
        const rows = jobs.map(job => [
            job.company_name,
            job.title,
            job.location,
            job.status,
            job.classification,
            new Date(job.first_seen).toLocaleDateString(),
            new Date(job.last_seen).toLocaleDateString(),
            job.url
        ]);

        const csv = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        this.downloadFile(csv, 'jobs-export.csv', 'text/csv');
    }

    exportApplicationsToJSON(applications) {
        const data = {
            version: '1.0.0',
            exported_at: new Date().toISOString(),
            applications: applications
        };

        const json = JSON.stringify(data, null, 2);
        this.downloadFile(json, 'applications-export.json', 'application/json');
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    }
}

window.DataExporter = DataExporter;
