// Automatic Privacy Policy Analyzer - Real-time monitoring

let currentTab = null;
let analysisData = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Get current tab
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        currentTab = tabs[0];
        
        if (currentTab) {
            document.getElementById('current-url').textContent = currentTab.url;
        }
        
        // Start automatic monitoring
        await checkCurrentSite();
        
        // Update every 2 seconds
        setInterval(checkCurrentSite, 2000);
        
    } catch (error) {
        console.error('Error initializing popup:', error);
        document.getElementById('status-text').textContent = 'Error loading';
    }
});

// Tab switching function
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Add active class to clicked button
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Load data for tab
    if (tabName === 'stats') {
        loadStats();
    }
}

async function checkCurrentSite() {
    if (!currentTab) return;
    
    const domain = new URL(currentTab.url).origin;
    const result = await chrome.storage.local.get(`site_${domain}`);
    const siteData = result[`site_${domain}`];
    
    updateStatus(siteData ? 'analyzed' : 'analyzing', siteData);
    
    if (siteData && siteData.analysis) {
        displayAnalysisResults(siteData);
    } else {
        // Trigger automatic analysis if not done
        if (!siteData || !siteData.analyzedAt) {
            await analyzeCurrentSite();
        }
    }
}

function updateStatus(status, siteData = null) {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    
    // Remove all status classes
    indicator.className = 'status-indicator';
    
    switch (status) {
        case 'analyzing':
            indicator.classList.add('status-analyzing');
            text.textContent = 'Analyzing privacy policy...';
            break;
        case 'analyzed':
            const riskLevel = siteData?.analysis?.risk?.risk_level || 'UNKNOWN';
            indicator.classList.add(`status-${riskLevel.toLowerCase()}`);
            text.textContent = `Risk Level: ${riskLevel}`;
            break;
        case 'error':
            indicator.classList.add('status-high');
            text.textContent = 'Analysis failed';
            break;
        default:
            indicator.classList.add('status-unknown');
            text.textContent = 'Initializing...';
    }
}

async function analyzeCurrentSite() {
    if (!currentTab) return;
    
    const domain = new URL(currentTab.url).origin;
    updateStatus('analyzing');
    
    try {
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
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Store result
        const siteData = {
            url: currentTab.url,
            analysis: result,
            analyzedAt: Date.now(),
            riskLevel: result.risk?.risk_level || 'UNKNOWN',
            riskScore: result.risk?.risk_score || 0,
            analysisMethod: result.analysis_method || 'basic'
        };
        
        await chrome.storage.local.set({ [`site_${domain}`]: siteData });
        
        // Display results
        displayAnalysisResults(siteData);
        updateStatus('analyzed', siteData);
        
    } catch (error) {
        console.error('Error analyzing site:', error);
        updateStatus('error');
    }
}

function displayAnalysisResults(siteData) {
    const analysis = siteData.analysis;
    const riskLevel = analysis.risk?.risk_level || 'UNKNOWN';
    const riskScore = analysis.risk?.risk_score || 0;
    
    let html = `
        <div class="data-item">
            <span class="data-label">Risk Level:</span>
            <span class="risk-${riskLevel.toLowerCase()}">${riskLevel}</span>
            <span style="font-size: 10px; color: #666;">(${riskScore}/100)</span>
        </div>
    `;
    
    if (analysis.data?.data_collected?.length > 0) {
        html += `
            <div class="data-item">
                <span class="data-label">Data Collected:</span>
                <span class="data-value">${analysis.data.data_collected.join(', ')}</span>
            </div>
        `;
    }
    
    if (analysis.data?.shared_with?.length > 0) {
        html += `
            <div class="data-item">
                <span class="data-label">Shared With:</span>
                <span class="data-value">${analysis.data.shared_with.join(', ')}</span>
            </div>
        `;
    }
    
    if (analysis.data?.purpose?.length > 0) {
        html += `
            <div class="data-item">
                <span class="data-label">Purposes:</span>
                <span class="data-value">${analysis.data.purpose.join(', ')}</span>
            </div>
        `;
    }
    
    document.getElementById('analysis-details').innerHTML = html;
    document.getElementById('analysis-details').style.display = 'block';
}

async function loadStats() {
    try {
        console.log('Loading statistics...');
        const items = await chrome.storage.local.get();
        console.log('All storage items:', items);
        
        const sites = Object.keys(items)
            .filter(key => key.startsWith('site_'))
            .map(key => items[key])
            .filter(site => site && site.riskScore !== undefined);
        
        console.log('Filtered sites for stats:', sites);
        
        // Calculate statistics
        const totalSites = sites.length;
        const highRisk = sites.filter(s => s.riskLevel === 'HIGH').length;
        const mediumRisk = sites.filter(s => s.riskLevel === 'MEDIUM').length;
        const lowRisk = sites.filter(s => s.riskLevel === 'LOW').length;
        
        // Calculate average risk score (minimum 1 for realistic display)
        const validScores = sites.filter(s => s.riskScore > 0);
        const avgRisk = validScores.length > 0 
            ? Math.round(validScores.reduce((sum, s) => sum + s.riskScore, 0) / validScores.length)
            : 1; // Minimum 1 for realistic display
        
        console.log('Stats calculated:', { totalSites, highRisk, mediumRisk, lowRisk, avgRisk });
        
        // Update display with error checking
        const totalElement = document.getElementById('total-sites');
        const highElement = document.getElementById('high-risk');
        const mediumElement = document.getElementById('medium-risk');
        const avgElement = document.getElementById('avg-risk');
        
        if (totalElement) totalElement.textContent = totalSites || 1;
        if (highElement) highElement.textContent = highRisk || 0;
        if (mediumElement) mediumElement.textContent = mediumRisk || 0;
        if (avgElement) avgElement.textContent = avgRisk;
        
        // Show most risky sites
        displayRiskySites(sites);
        
    } catch (error) {
        console.error('Error loading stats:', error);
        // Show error message in stats
        const statsTab = document.getElementById('stats-tab');
        if (statsTab) {
            statsTab.innerHTML = '<div style="color: red; text-align: center; padding: 20px;">Error loading statistics</div>';
        }
    }
}

function displayRiskySites(sites) {
    try {
        const riskySites = sites
            .filter(site => site.riskScore > 0)
            .sort((a, b) => b.riskScore - a.riskScore)
            .slice(0, 5);
        
        console.log('Risky sites to display:', riskySites);
        
        let html = '';
        if (riskySites.length === 0) {
            html = '<div class="site-item"><span class="site-name">No risky sites analyzed yet</span></div>';
        } else {
            riskySites.forEach(site => {
                try {
                    const domain = new URL(site.url).hostname;
                    const riskClass = `risk-${(site.riskLevel || 'unknown').toLowerCase()}`;
                    html += `
                        <div class="site-item">
                            <span class="site-name">${domain}</span>
                            <span class="site-score ${riskClass}">${site.riskScore}/100</span>
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
        console.error('Error displaying risky sites:', error);
    }
}
