// Simple working version - no complex logic

let currentTab = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Popup loaded');
    
    try {
        // Get current tab
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        currentTab = tabs[0];
        
        if (currentTab) {
            document.getElementById('current-url').textContent = currentTab.url;
        }
        
        // Load initial data
        await checkSite();
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('status').textContent = 'Error';
    }
});

// Tab switching
function showTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Add active class
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Load data for stats tab
    if (tabName === 'stats') {
        loadStatistics();
    }
}

// Check current site
async function checkSite() {
    if (!currentTab) return;
    
    try {
        const domain = new URL(currentTab.url).origin;
        const result = await chrome.storage.local.get(`site_${domain}`);
        const siteData = result[`site_${domain}`];
        
        console.log('Site data:', siteData);
        
        if (siteData) {
            document.getElementById('status').textContent = `Risk: ${siteData.riskLevel || 'Unknown'}`;
            showResults(siteData);
        } else {
            document.getElementById('status').textContent = 'Not analyzed yet';
            await analyzeSite();
        }
        
    } catch (error) {
        console.error('Error checking site:', error);
        document.getElementById('status').textContent = 'Error';
    }
}

// Analyze site
async function analyzeSite() {
    if (!currentTab) return;
    
    document.getElementById('status').textContent = 'Analyzing...';
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: currentTab.url })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Analysis result:', result);
        
        // Store data
        const domain = new URL(currentTab.url).origin;
        const siteData = {
            url: currentTab.url,
            riskLevel: result.risk?.risk_level || 'UNKNOWN',
            riskScore: result.risk?.risk_score || 0,
            analyzedAt: Date.now()
        };
        
        await chrome.storage.local.set({ [`site_${domain}`]: siteData });
        
        // Update display
        document.getElementById('status').textContent = `Risk: ${siteData.riskLevel}`;
        showResults(siteData);
        
    } catch (error) {
        console.error('Analysis error:', error);
        document.getElementById('status').textContent = 'Analysis failed';
    }
}

// Show results
function showResults(siteData) {
    const resultsDiv = document.getElementById('analysis-results');
    resultsDiv.innerHTML = `
        <div class="data-item">
            <span class="data-label">Risk Level:</span>
            <span class="data-value risk-${siteData.riskLevel.toLowerCase()}">${siteData.riskLevel}</span>
        </div>
        <div class="data-item">
            <span class="data-label">Risk Score:</span>
            <span class="data-value">${siteData.riskScore}/100</span>
        </div>
    `;
    resultsDiv.style.display = 'block';
}

// Load statistics
async function loadStatistics() {
    try {
        console.log('Loading statistics...');
        
        const items = await chrome.storage.local.get();
        console.log('Storage items:', items);
        
        const sites = Object.keys(items)
            .filter(key => key.startsWith('site_'))
            .map(key => items[key])
            .filter(site => site && site.riskScore !== undefined);
        
        console.log('Sites for stats:', sites);
        
        // Calculate stats
        const totalSites = Math.max(sites.length, 1);
        const highRisk = sites.filter(s => s.riskLevel === 'HIGH').length;
        const mediumRisk = sites.filter(s => s.riskLevel === 'MEDIUM').length;
        const avgRisk = sites.length > 0 
            ? Math.round(sites.reduce((sum, s) => sum + s.riskScore, 0) / sites.length)
            : 1;
        
        console.log('Stats:', { totalSites, highRisk, mediumRisk, avgRisk });
        
        // Update display
        document.getElementById('total-sites').textContent = totalSites;
        document.getElementById('high-risk').textContent = highRisk;
        document.getElementById('medium-risk').textContent = mediumRisk;
        document.getElementById('avg-risk').textContent = avgRisk;
        
        // Show risky sites
        const riskySites = sites
            .filter(s => s.riskScore > 0)
            .sort((a, b) => b.riskScore - a.riskScore)
            .slice(0, 3);
        
        let html = '';
        if (riskySites.length === 0) {
            html = '<div class="site-item"><span class="site-name">No sites analyzed yet</span></div>';
        } else {
            riskySites.forEach(site => {
                const domain = new URL(site.url).hostname;
                html += `
                    <div class="site-item">
                        <span class="site-name">${domain}</span>
                        <span class="site-score risk-${site.riskLevel.toLowerCase()}">${site.riskScore}/100</span>
                    </div>
                `;
            });
        }
        
        document.getElementById('risky-sites').innerHTML = html;
        
    } catch (error) {
        console.error('Stats error:', error);
    }
}
