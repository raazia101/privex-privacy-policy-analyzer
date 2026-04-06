// Simple popup script without external dependencies

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
        
        // Load initial data
        await loadStats();
        await loadHistory();
        
        // Check if we have analysis for current site
        if (currentTab) {
            const domain = new URL(currentTab.url).origin;
            const result = await chrome.storage.local.get(`site_${domain}`);
            const siteData = result[`site_${domain}`];
            
            if (siteData && siteData.analysis) {
                displayCurrentAnalysis(siteData);
            } else {
                document.getElementById('current-analysis').innerHTML = 
                    '<div class="analysis-result">Click "Analyze Current Site" to get privacy information</div>';
            }
        }
    } catch (error) {
        console.error('Error initializing popup:', error);
        document.getElementById('current-url').textContent = 'Error loading page';
    }
});

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
    
    // Load data for the tab
    if (tabName === 'stats') {
        loadStats();
    } else if (tabName === 'history') {
        loadHistory();
    }
}

async function analyzeCurrentSite() {
    if (!currentTab) {
        alert('No active tab found');
        return;
    }
    
    const btn = document.getElementById('analyze-btn');
    btn.disabled = true;
    btn.textContent = '🔄 Analyzing...';
    
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
        const domain = new URL(currentTab.url).origin;
        const siteData = {
            url: currentTab.url,
            analysis: result,
            analyzedAt: Date.now(),
            riskLevel: result.risk?.risk_level || 'UNKNOWN',
            riskScore: result.risk?.risk_score || 0,
            analysisMethod: result.analysis_method || 'basic'
        };
        
        console.log('Storing site data:', siteData);
        await chrome.storage.local.set({ [`site_${domain}`]: siteData });
        console.log('Data stored successfully');
        
        // Display results
        displayCurrentAnalysis(siteData);
        
        // Refresh stats and history
        await loadStats();
        await loadHistory();
        
    } catch (error) {
        console.error('Error analyzing site:', error);
        document.getElementById('current-analysis').innerHTML = 
            `<div class="analysis-result" style="color: #dc2626;">Error: ${error.message}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '🚀 Analyze Current Site';
    }
}

function displayCurrentAnalysis(siteData) {
    const analysis = siteData.analysis;
    const riskLevel = analysis.risk?.risk_level || 'UNKNOWN';
    const riskClass = `risk-${riskLevel.toLowerCase()}`;
    
    // Clean risk level display
    const cleanRiskLevel = riskLevel.replace(/[^\w\s]/gi, '').trim();
    
    let html = `
        <div class="analysis-result">
            <strong>Risk Level:</strong> 
            <span class="${riskClass}">${cleanRiskLevel}</span>
            <div style="font-size: 11px; color: #666; margin-top: 4px;">
                Score: ${analysis.risk?.risk_score || 0}/100
            </div>
        </div>
    `;
    
    if (analysis.data?.data_collected?.length > 0) {
        html += `
            <div class="analysis-result">
                <strong>Data Collected:</strong> ${analysis.data.data_collected.join(', ')}
            </div>
        `;
    }
    
    if (analysis.data?.shared_with?.length > 0) {
        html += `
            <div class="analysis-result">
                <strong>Shared With:</strong> ${analysis.data.shared_with.join(', ')}
            </div>
        `;
    }
    
    if (analysis.data?.purpose?.length > 0) {
        html += `
            <div class="analysis-result">
                <strong>Purposes:</strong> ${analysis.data.purpose.join(', ')}
            </div>
        `;
    }
    
    if (analysis.summary) {
        html += `
            <div class="analysis-result">
                <strong>Summary:</strong> ${analysis.summary}
            </div>
        `;
    }
    
    document.getElementById('current-analysis').innerHTML = html;
}

async function loadStats() {
    try {
        console.log('Loading stats...');
        const items = await chrome.storage.local.get();
        console.log('All storage items:', items);
        
        const sites = Object.keys(items)
            .filter(key => key.startsWith('site_'))
            .map(key => items[key]);
        
        console.log('Filtered sites:', sites);
        
        const totalSites = sites.length;
        const highRisk = sites.filter(s => s.riskLevel === 'HIGH').length;
        const mediumRisk = sites.filter(s => s.riskLevel === 'MEDIUM').length;
        const lowRisk = sites.filter(s => s.riskLevel === 'LOW').length;
        
        console.log('Stats calculated:', { totalSites, highRisk, mediumRisk, lowRisk });
        
        // Update display
        const totalElement = document.getElementById('total-sites');
        const highElement = document.getElementById('high-risk');
        const mediumElement = document.getElementById('medium-risk');
        const lowElement = document.getElementById('low-risk');
        
        if (totalElement) totalElement.textContent = totalSites;
        if (highElement) highElement.textContent = highRisk;
        if (mediumElement) mediumElement.textContent = mediumRisk;
        if (lowElement) lowElement.textContent = lowRisk;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadHistory() {
    try {
        console.log('Loading history...');
        const items = await chrome.storage.local.get();
        console.log('All storage items for history:', items);
        
        const sites = Object.keys(items)
            .filter(key => key.startsWith('site_'))
            .map(key => items[key])
            .sort((a, b) => (b.analyzedAt || 0) - (a.analyzedAt || 0))
            .slice(0, 10);
        
        console.log('History sites:', sites);
        
        let html = '';
        if (sites.length === 0) {
            html = '<div class="analysis-result">No sites analyzed yet</div>';
        } else {
            sites.forEach(site => {
                const riskClass = `risk-${(site.riskLevel || 'unknown').toLowerCase()}`;
                const cleanRiskLevel = (site.riskLevel || 'unknown').replace(/[^\w\s]/gi, '').trim();
                html += `
                    <div class="site-item">
                        <div class="site-header">
                            <div style="font-size: 11px; font-weight: bold;">${site.url}</div>
                            <span class="${riskClass}">${cleanRiskLevel}</span>
                        </div>
                        <div style="font-size: 10px; color: #666; margin-top: 2px;">
                            ${new Date(site.analyzedAt || 0).toLocaleDateString()}
                        </div>
                    </div>
                `;
            });
        }
        
        console.log('History HTML:', html);
        const historyElement = document.getElementById('history-list');
        if (historyElement) {
            historyElement.innerHTML = html;
        }
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function viewGraph() {
    chrome.tabs.create({ url: 'graph.html' });
}
