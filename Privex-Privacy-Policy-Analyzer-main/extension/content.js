// Cookie Consent Detection and Privacy Policy Analyzer

class CookieDetector {
    constructor() {
        this.cookieKeywords = [
            'cookie', 'consent', 'accept', 'agree', 'privacy', 'policy',
            'gdpr', 'ccpa', 'personal data', 'data protection', 'legitimate interest',
            'data processing', 'third party', 'analytics', 'marketing', 'advertising'
        ];
        
        this.bannerSelectors = [
            '[class*="cookie"]', '[id*="cookie"]',
            '[class*="consent"]', '[id*="consent"]',
            '[class*="privacy"]', '[id*="privacy"]',
            '.cookie-banner', '.consent-banner', '.privacy-notice',
            '[role="dialog"]', '[aria-label*="cookie"]', '[aria-label*="consent"]',
            '[data-testid*="cookie"]', '[data-testid*="consent"]',
            '.cookie-consent', '.privacy-banner', '.cookie-notice',
            '#cookie-consent', '#privacy-notice', '#cookie-banner',
            '.ccpa-banner', '.gdpr-banner', '.privacy-overlay',
            '.cookie-consent-overlay', '.consent-overlay'
        ];
        
        this.init();
    }

    init() {
        console.log('Privacy Policy Analyzer: Content script loaded on:', window.location.href);
        
        // Immediate detection
        setTimeout(() => {
            this.detectCookieBanners();
        }, 1000);
        
        // Observe page changes
        this.observePageChanges();
        
        // Check periodically for delayed banners
        this.startPeriodicCheck();
    }

    startPeriodicCheck() {
        // Check every 3 seconds for the first 30 seconds
        let checks = 0;
        const interval = setInterval(() => {
            this.detectCookieBanners();
            checks++;
            
            if (checks >= 10) { // Stop after 30 seconds
                clearInterval(interval);
            }
        }, 3000);
    }

    detectCookieBanners() {
        const banners = document.querySelectorAll(this.bannerSelectors.join(','));
        
        banners.forEach(banner => {
            if (this.isCookieBanner(banner)) {
                console.log('Cookie banner detected:', banner);
                this.handleCookieBanner(banner);
            }
        });
    }

    isCookieBanner(element) {
        const text = element.textContent.toLowerCase();
        const hasKeywords = this.cookieKeywords.some(keyword => text.includes(keyword));
        const isVisible = element.offsetParent !== null;
        
        // Additional checks for better detection
        const hasCookieButtons = this.hasCookieButtons(element);
        const hasCookieText = this.hasCookieText(text);
        
        return isVisible && (hasKeywords || hasCookieButtons || hasCookieText);
    }

    hasCookieButtons(element) {
        const buttons = element.querySelectorAll('button, a, [role="button"]');
        const buttonKeywords = ['accept', 'agree', 'consent', 'allow', 'ok', 'got it', 'understand'];
        
        return Array.from(buttons).some(button => {
            const buttonText = button.textContent.toLowerCase();
            return buttonKeywords.some(keyword => buttonText.includes(keyword));
        });
    }

    hasCookieText(text) {
        const cookiePhrases = [
            'we use cookies', 'our website uses cookies', 'this site uses cookies',
            'by using our site', 'cookie policy', 'privacy policy',
            'personal data', 'data collection', 'third parties'
        ];
        
        return cookiePhrases.some(phrase => text.includes(phrase));
    }

    handleCookieBanner(banner) {
        // Send message to background script
        chrome.runtime.sendMessage({
            type: 'COOKIE_BANNER_DETECTED',
            url: window.location.href,
            bannerText: banner.textContent.substring(0, 500),
            timestamp: Date.now()
        });

        // Find privacy policy link
        const policyLink = this.findPrivacyPolicyLink(banner);
        if (policyLink) {
            chrome.runtime.sendMessage({
                type: 'PRIVACY_POLICY_FOUND',
                url: window.location.href,
                policyUrl: policyLink.href,
                timestamp: Date.now()
            });
        }

        // Also search the entire page for privacy policy
        setTimeout(() => {
            this.searchPageForPrivacyPolicy();
        }, 2000);
    }

    findPrivacyPolicyLink(context = document) {
        const policyKeywords = [
            'privacy policy', 'privacy statement', 'data protection',
            'privacy notice', 'gdpr', 'privacy'
        ];

        const links = context.querySelectorAll('a[href]');
        
        for (const link of links) {
            const text = link.textContent.toLowerCase();
            const href = link.href.toLowerCase();
            
            if (policyKeywords.some(keyword => 
                text.includes(keyword) || href.includes(keyword))) {
                return link;
            }
        }
        
        return null;
    }

    searchPageForPrivacyPolicy() {
        // Search in footer first
        const footer = document.querySelector('footer');
        if (footer) {
            const policyLink = this.findPrivacyPolicyLink(footer);
            if (policyLink) {
                chrome.runtime.sendMessage({
                    type: 'PRIVACY_POLICY_FOUND',
                    url: window.location.href,
                    policyUrl: policyLink.href,
                    timestamp: Date.now()
                });
                return;
            }
        }

        // Search in common navigation areas
        const navSelectors = ['nav', '.nav', '.navigation', '.menu', '.footer-nav'];
        for (const selector of navSelectors) {
            const element = document.querySelector(selector);
            if (element) {
                const policyLink = this.findPrivacyPolicyLink(element);
                if (policyLink) {
                    chrome.runtime.sendMessage({
                        type: 'PRIVACY_POLICY_FOUND',
                        url: window.location.href,
                        policyUrl: policyLink.href,
                        timestamp: Date.now()
                    });
                    return;
                }
            }
        }

        // Search entire page as last resort
        const policyLink = this.findPrivacyPolicyLink();
        if (policyLink) {
            chrome.runtime.sendMessage({
                type: 'PRIVACY_POLICY_FOUND',
                url: window.location.href,
                policyUrl: policyLink.href,
                timestamp: Date.now()
            });
        }
    }

    observePageChanges() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (this.isCookieBanner(node)) {
                            this.handleCookieBanner(node);
                        }
                        
                        // Check child elements
                        const banners = node.querySelectorAll ? 
                            node.querySelectorAll(this.bannerSelectors.join(',')) : [];
                        banners.forEach(banner => {
                            if (this.isCookieBanner(banner)) {
                                this.handleCookieBanner(banner);
                            }
                        });
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: false,
            characterData: false
        });
    }
}

// Initialize the detector immediately
new CookieDetector();
