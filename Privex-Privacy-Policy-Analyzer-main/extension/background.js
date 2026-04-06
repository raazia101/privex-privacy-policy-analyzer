// Background Service Worker for Privacy Policy Analyzer

class PrivacyAnalyzer {
    constructor() {
        this.analyzedSites = new Map();
        this.init();
    }

    init() {
        // Listen for messages from content script
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message, sender, sendResponse);
            return true; // Keep message channel open for async response
        });

        // Listen for tab updates - automatic analysis
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab.url) {
                this.handleTabUpdate(tabId, tab.url);
            }
        });

        // Listen for new tab creation
        chrome.tabs.onCreated.addListener((tab) => {
            if (tab.url) {
                setTimeout(() => {
                    this.handleTabUpdate(tab.id, tab.url);
                }, 2000); // Wait 2 seconds for page to load
            }
        });

        // Start automatic monitoring on browser startup
        chrome.runtime.onStartup.addListener(() => {
            this.startAutomaticMonitoring();
        });

        // Start monitoring when extension is installed
        chrome.runtime.onInstalled.addListener(() => {
            this.startAutomaticMonitoring();
        });
    }

    startAutomaticMonitoring() {
        console.log('Starting automatic privacy monitoring...');
        
        // Analyze all existing tabs
        chrome.tabs.query({}, (tabs) => {
            tabs.forEach(tab => {
                if (tab.url && this.shouldAnalyzeSite(tab.url)) {
                    setTimeout(() => {
                        this.handleTabUpdate(tab.id, tab.url);
                    }, 1000);
                }
            });
        });
    }

    async handleMessage(message, sender, sendResponse) {
        switch (message.type) {
            case 'COOKIE_BANNER_DETECTED':
                await this.handleCookieBanner(message, sender);
                break;
                
            case 'PRIVACY_POLICY_FOUND':
                await this.handlePrivacyPolicyFound(message, sender);
                break;
                
            case 'GET_ANALYSIS_DATA':
                const data = await this.getAnalysisData();
                sendResponse(data);
                break;
                
            default:
                console.log('Unknown message type:', message.type);
        }
    }

    async handleCookieBanner(message, sender) {
        console.log('Cookie banner detected on:', message.url);
        
        // Store detection
        const siteData = this.getSiteData(message.url);
        siteData.cookieBannerDetected = true;
        siteData.bannerText = message.bannerText;
        siteData.lastDetected = message.timestamp;
        
        // Trigger automatic privacy policy analysis
        await this.analyzePrivacyPolicy(message.url);
        
        // Update badge
        this.updateBadge(sender.tab.id);
    }

    async handlePrivacyPolicyFound(message, sender) {
        console.log('Privacy policy found:', message.policyUrl);
        
        const siteData = this.getSiteData(message.url);
        siteData.privacyPolicyUrl = message.policyUrl;
        
        // Analyze the policy
        await this.analyzePrivacyPolicy(message.url, message.policyUrl);
    }

    async handleTabUpdate(tabId, url) {
        console.log('handleTabUpdate called for:', url);
        // Check if we should analyze this site
        if (this.shouldAnalyzeSite(url)) {
            console.log('Automatically analyzing site:', url);
            await this.analyzePrivacyPolicy(url);
        } else {
            console.log('Skipping analysis for:', url);
        }
        
        // Update extension badge
        await this.updateBadge(tabId, url);
    }
    
    async updateBadge(tabId, url) {
        try {
            const domain = new URL(url).origin;
            const result = await chrome.storage.local.get(`site_${domain}`);
            const siteData = result[`site_${domain}`];
            
            if (siteData && siteData.riskLevel) {
                const riskLevel = siteData.riskLevel.toUpperCase();
                let color = '#10b981'; // green for LOW
                let text = '✓';
                
                if (riskLevel === 'MEDIUM') {
                    color = '#f59e0b'; // orange
                    text = '!';
                } else if (riskLevel === 'HIGH') {
                    color = '#ef4444'; // red
                    text = '⚠';
                }
                
                await chrome.action.setBadgeText({ tabId, text });
                await chrome.action.setBadgeBackgroundColor({ tabId, color });
            } else {
                await chrome.action.setBadgeText({ tabId: tabId, text: '' });
            }
        } catch (error) {
            console.error('Error updating badge:', error);
        }
    }

    async analyzePrivacyPolicy(siteUrl, policyUrl = null) {
        try {
            // If no specific policy URL, try to find one
            if (!policyUrl) {
                policyUrl = await this.findPrivacyPolicyUrl(siteUrl);
            }

            if (!policyUrl) {
                console.log('No privacy policy found for:', siteUrl);
                return;
            }

            // Check if we already analyzed this recently
            const siteData = this.getSiteData(siteUrl);
            const now = Date.now();
            if (siteData.analyzedAt && (now - siteData.analyzedAt) < 24 * 60 * 60 * 1000) { // 24 hours
                console.log('Recently analyzed, skipping:', siteUrl);
                return;
            }

            // Call backend API
            const response = await fetch('http://127.0.0.1:5000/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: policyUrl })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const analysis = await response.json();
            
            // Store analysis results
            const updatedSiteData = this.getSiteData(siteUrl);
            updatedSiteData.analysis = analysis;
            updatedSiteData.policyUrl = policyUrl;
            updatedSiteData.analyzedAt = Date.now();
            updatedSiteData.riskLevel = analysis.risk?.risk_level || 'UNKNOWN';
            updatedSiteData.riskScore = analysis.risk?.risk_score || 0;
            
            console.log('Automatic analysis completed for:', siteUrl, analysis);
            
            // Store in Chrome storage
            await this.saveSiteData(siteUrl, updatedSiteData);
            
            // Update badge for all tabs of this domain
            await this.updateAllBadges();
            
        } catch (error) {
            console.error('Error analyzing privacy policy:', error);
            
            const siteData = this.getSiteData(siteUrl);
            siteData.error = error.message;
            siteData.analyzedAt = Date.now();
            
            await this.saveSiteData(siteUrl, siteData);
        }
    }

    async findPrivacyPolicyUrl(siteUrl) {
        try {
            // Try common privacy policy URL patterns
            const patterns = [
                '/privacy',
                '/privacy-policy',
                '/privacy.html',
                '/privacy-policy.html',
                '/legal/privacy',
                '/legal/privacy-policy',
                '/data-protection',
                '/gdpr'
            ];

            const baseUrl = new URL(siteUrl).origin;

            for (const pattern of patterns) {
                try {
                    const testUrl = baseUrl + pattern;
                    const response = await fetch(testUrl, { method: 'HEAD' });
                    
                    if (response.ok) {
                        return testUrl;
                    }
                } catch (e) {
                    // Continue to next pattern
                }
            }

            return null;
        } catch (error) {
            console.error('Error finding privacy policy URL:', error);
            return null;
        }
    }

    getSiteData(url) {
        const domain = new URL(url).origin;
        return this.analyzedSites.get(domain) || {
            url: domain,
            cookieBannerDetected: false,
            analyzedAt: null,
            riskLevel: 'UNKNOWN',
            riskScore: 0,
            dataCollected: [],
            sharedWith: [],
            purposes: []
        };
    }

    async saveSiteData(url, data) {
        const domain = new URL(url).origin;
        this.analyzedSites.set(domain, data);
        
        // Save to Chrome storage
        const storageData = {};
        storageData[`site_${domain}`] = data;
        
        await chrome.storage.local.set(storageData);
    }

    async getAnalysisData() {
        try {
            // Load from Chrome storage
            const items = await chrome.storage.local.get();
            
            const sites = Object.keys(items)
                .filter(key => key.startsWith('site_'))
                .map(key => items[key]);
            
            return {
                sites: sites,
                totalSites: sites.length,
                highRiskSites: sites.filter(s => s.riskLevel === 'HIGH').length,
                mediumRiskSites: sites.filter(s => s.riskLevel === 'MEDIUM').length,
                lowRiskSites: sites.filter(s => s.riskLevel === 'LOW').length
            };
        } catch (error) {
            console.error('Error getting analysis data:', error);
            return { sites: [], totalSites: 0 };
        }
    }

    shouldAnalyzeSite(url) {
        try {
            const urlObj = new URL(url);
            
            // Allow file:// URLs for testing
            if (urlObj.protocol === 'chrome:' || 
                urlObj.protocol === 'chrome-extension:' ||
                urlObj.protocol === 'moz-extension:' ||
                urlObj.protocol === 'about:') {
                return false;
            }
            
            // Skip common non-content pages
            const skipPatterns = [
                '/login', '/signin', '/signup', '/register',
                '/cart', '/checkout', '/payment'
            ];
            
            return !skipPatterns.some(pattern => urlObj.pathname.includes(pattern));
        } catch (error) {
            return false;
        }
    }

    async updateBadge(tabId) {
        try {
            const data = await this.getAnalysisData();
            
            if (data.totalSites > 0) {
                const highRiskCount = data.highRiskSites;
                chrome.action.setBadgeText({
                    text: highRiskCount > 0 ? highRiskCount.toString() : '✓',
                    tabId: tabId
                });
                
                chrome.action.setBadgeBackgroundColor({
                    color: highRiskCount > 0 ? '#FF0000' : '#00FF00',
                    tabId: tabId
                });
            }
        } catch (error) {
            console.error('Error updating badge:', error);
        }
    }

    async updateAllBadges() {
        try {
            const tabs = await chrome.tabs.query({});
            const data = await this.getAnalysisData();
            
            if (data.totalSites > 0) {
                const highRiskCount = data.highRiskSites;
                const badgeText = highRiskCount > 0 ? highRiskCount.toString() : '✓';
                const badgeColor = highRiskCount > 0 ? '#FF0000' : '#00FF00';
                
                tabs.forEach(tab => {
                    chrome.action.setBadgeText({
                        text: badgeText,
                        tabId: tab.id
                    });
                    
                    chrome.action.setBadgeBackgroundColor({
                        color: badgeColor,
                        tabId: tab.id
                    });
                });
            }
        } catch (error) {
            console.error('Error updating all badges:', error);
        }
    }
}

// Initialize the background service
new PrivacyAnalyzer();
