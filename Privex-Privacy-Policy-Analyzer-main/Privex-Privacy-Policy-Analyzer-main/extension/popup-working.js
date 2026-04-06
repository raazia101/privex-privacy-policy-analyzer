// Working Privacy Policy Analyzer - No Tabs, Fully Automatic

let currentTab = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Popup loaded successfully');
    
    try {
        // Get current tab
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        currentTab = tabs[0];
        
        if (currentTab) {
            document.getElementById('current-url').textContent = currentTab.url;
            console.log('Current tab:', currentTab.url);
        }
        
        // Check if we have data for this site
        await checkSiteData();
        
        // If no data, automatically analyze
        const domain = new URL(currentTab.url).origin;
        const result = await chrome.storage.local.get(`site_${domain}`);
        const siteData = result[`site_${domain}`];
        
        if (!siteData) {
            console.log('No data found, starting automatic analysis...');
            await analyzeSite();
        }
        
        // Load statistics automatically
        await loadStatistics();
        
    } catch (error) {
        console.error('Error initializing popup:', error);
        document.getElementById('status').textContent = 'Error loading';
    }
});

// Check site data
async function checkSiteData() {
    if (!currentTab) return;
    
    try {
        const domain = new URL(currentTab.url).origin;
        const result = await chrome.storage.local.get(`site_${domain}`);
        const siteData = result[`site_${domain}`];
        
        console.log('Site data found:', siteData);
        
        if (siteData) {
            document.getElementById('status').textContent = `Risk: ${siteData.riskLevel}`;
            showAnalysisResults(siteData);
        } else {
            document.getElementById('status').textContent = 'Analyzing...';
        }
        
    } catch (error) {
        console.error('Error checking site data:', error);
        document.getElementById('status').textContent = 'Error';
    }
}

// Analyze site (automatic)
async function analyzeSite() {
    if (!currentTab) return;
    
    document.getElementById('status').textContent = 'Analyzing...';
    
    try {
        console.log('Analyzing site:', currentTab.url);
        
        const response = await fetch('http://127.0.0.1:5000/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                url: currentTab.url
            })
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
        console.log('Data stored:', siteData);
        
        // Update display
        document.getElementById('status').textContent = `Risk: ${siteData.riskLevel}`;
        showAnalysisResults(siteData);
        
        // Refresh statistics
        await loadStatistics();
        
    } catch (error) {
        console.error('Analysis error:', error);
        document.getElementById('status').textContent = 'Analysis failed';
    }
}

// Show analysis results
function showAnalysisResults(siteData) {
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

// Load statistics - AUTOMATIC VERSION
async function loadStatistics() {
    try {
        console.log('Loading statistics...');
        
        // Clear any existing content
        const riskySitesElement = document.getElementById('risky-sites');
        if (riskySitesElement) {
            riskySitesElement.innerHTML = '<div class="site-item"><span class="site-name">Loading...</span></div>';
        }
        
        const items = await chrome.storage.local.get();
        console.log('All storage items:', items);
        
        const sites = Object.keys(items)
            .filter(key => key.startsWith('site_'))
            .map(key => items[key])
            .filter(site => site && site.riskScore !== undefined);
        
        console.log('Sites for statistics:', sites);
        
        // Calculate statistics
        const totalSites = Math.max(sites.length, 1);
        const highRisk = sites.filter(s => s.riskLevel === 'HIGH').length;
        const mediumRisk = sites.filter(s => s.riskLevel === 'MEDIUM').length;
        const avgRisk = sites.length > 0 
            ? Math.round(sites.reduce((sum, s) => sum + s.riskScore, 0) / sites.length)
            : 1;
        
        console.log('Calculated stats:', { totalSites, highRisk, mediumRisk, avgRisk });
        
        // Update display with error checking
        const totalElement = document.getElementById('total-sites');
        const highElement = document.getElementById('high-risk');
        const mediumElement = document.getElementById('medium-risk');
        const avgElement = document.getElementById('avg-risk');
        
        if (totalElement) totalElement.textContent = totalSites;
        if (highElement) highElement.textContent = highRisk;
        if (mediumElement) mediumElement.textContent = mediumRisk;
        if (avgElement) avgElement.textContent = avgRisk;
        
        // Show risky sites
        showRiskySites(sites);
        
    } catch (error) {
        console.error('Error loading statistics:', error);
        // Show error message
        const riskySitesElement = document.getElementById('risky-sites');
        if (riskySitesElement) {
            riskySitesElement.innerHTML = '<div class="site-item"><span class="site-name">Error loading statistics</span></div>';
        }
    }
}

// Show risky sites - FIXED VERSION
function showRiskySites(sites) {
    try {
        const riskySites = sites
            .filter(site => site.riskScore > 0)
            .sort((a, b) => b.riskScore - a.riskScore)
            .slice(0, 3);
        
        console.log('Risky sites to display:', riskySites);
        
        let html = '';
        if (riskySites.length === 0) {
            html = '<div class="site-item"><span class="site-name">No sites analyzed yet</span></div>';
        } else {
            riskySites.forEach(site => {
                try {
                    const domain = new URL(site.url).hostname;
                    html += `
                        <div class="site-item">
                            <span class="site-name">${domain}</span>
                            <span class="site-score risk-${site.riskLevel.toLowerCase()}">${site.riskScore}/100</span>
                        </div>
                    `;
                } catch (e) {
                    console.error('Error processing site:', site, e);
                }
            });
        }
        
        const riskySitesElement = document.getElementById('risky-sites');
        if (riskySitesElement) {
            riskySitesElement.innerHTML = html;
        }
    } catch (error) {
        console.error('Error showing risky sites:', error);
    }
}
