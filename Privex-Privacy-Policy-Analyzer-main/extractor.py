from nltk.tokenize import sent_tokenize

def split_sentences(text):
    if not text:
        return []
    
    sentences = sent_tokenize(text)
    return sentences[:50]  # limit for simplicity


def simple_extract(sentences):
    data = {
        "data_collected": [],
        "shared_with": [],
        "purpose": [],
        "data_categories": {
            "personal_identifiers": [],
            "contact_information": [],
            "technical_data": [],
            "behavioral_data": [],
            "financial_data": [],
            "health_data": [],
            "location_data": []
        },
        "sharing_practices": {
            "third_parties": [],
            "legal_requirements": [],
            "business_transfers": [],
            "marketing_partners": []
        },
        "data_purposes": {
            "service_delivery": [],
            "analytics": [],
            "marketing": [],
            "security": [],
            "legal_compliance": [],
            "personalization": []
        },
        "user_rights": [],
        "retention_period": [],
        "international_transfers": []
    }
    
    # Enhanced keyword dictionaries
    data_keywords = {
        "personal_identifiers": ["name", "full name", "real name", "username", "user id", "account name", "profile name"],
        "contact_information": ["email", "phone", "address", "postal code", "zip code", "telephone", "mobile"],
        "technical_data": ["ip address", "device id", "browser", "operating system", "device information", "user agent", "mac address"],
        "behavioral_data": ["cookie", "tracking", "browsing history", "clickstream", "usage data", "interaction data", "behavior"],
        "financial_data": ["credit card", "payment", "billing", "bank account", "financial information", "transaction"],
        "health_data": ["health", "medical", "medical history", "health condition", "biometric", "genetic"],
        "location_data": ["location", "gps", "geolocation", "precise location", "approximate location", "coordinates"]
    }
    
    third_party_keywords = {
        "third_parties": ["third party", "service provider", "vendor", "contractor", "external party"],
        "legal_requirements": ["legal requirement", "law enforcement", "government", "regulatory", "compliance"],
        "business_transfers": ["business transfer", "merger", "acquisition", "sale of assets", "corporate restructuring"],
        "marketing_partners": ["marketing partner", "advertising partner", "affiliate", "joint marketing"]
    }
    
    purpose_keywords = {
        "service_delivery": ["provide service", "deliver service", "service operation", "maintain service", "customer support"],
        "analytics": ["analytics", "analyze", "research", "study", "improve service", "statistics"],
        "marketing": ["marketing", "advertising", "promotion", "campaign", "targeted ads"],
        "security": ["security", "fraud prevention", "protect", "safeguard", "detect", "prevent"],
        "legal_compliance": ["legal obligation", "comply with law", "regulatory requirement", "legal duty"],
        "personalization": ["personalize", "customize", "tailor", "individual experience", "preferences"]
    }
    
    user_rights_keywords = ["right to access", "right to delete", "right to rectify", "right to object", "right to port", "opt out", "consent", "withdraw consent"]
    retention_keywords = ["retain", "store", "keep", "period", "duration", "until", "for", "months", "years", "days"]
    international_keywords = ["international", "cross-border", "outside country", "foreign", "global", "worldwide", "transfer abroad"]


    for s in sentences:
        s_lower = s.lower()

        # Enhanced data collection detection
        for category, keywords in data_keywords.items():
            for keyword in keywords:
                if keyword in s_lower and keyword not in data["data_categories"][category]:
                    data["data_categories"][category].append(keyword)
                    if keyword not in data["data_collected"]:
                        data["data_collected"].append(keyword)

        # Enhanced sharing practices detection
        for category, keywords in third_party_keywords.items():
            for keyword in keywords:
                if keyword in s_lower and keyword not in data["sharing_practices"][category]:
                    data["sharing_practices"][category].append(keyword)
                    if keyword not in data["shared_with"]:
                        data["shared_with"].append(keyword)

        # Enhanced purpose detection
        for category, keywords in purpose_keywords.items():
            for keyword in keywords:
                if keyword in s_lower and keyword not in data["data_purposes"][category]:
                    data["data_purposes"][category].append(keyword)
                    if keyword not in data["purpose"]:
                        data["purpose"].append(keyword)

        # User rights detection
        for right in user_rights_keywords:
            if right in s_lower and right not in data["user_rights"]:
                data["user_rights"].append(right)

        # Retention period detection
        if any(keyword in s_lower for keyword in retention_keywords):
            if len(s) < 200:  # Keep only shorter, relevant sentences
                data["retention_period"].append(s.strip())

        # International transfer detection
        if any(keyword in s_lower for keyword in international_keywords):
            if len(s) < 200:  # Keep only shorter, relevant sentences
                data["international_transfers"].append(s.strip())

    return data

def calculate_risk_score(data):
    score = 0
    reasons = []
    factors = []
    breakdown = {
        "data_collection": 0,
        "sharing_practices": 0,
        "purpose_risk": 0,
        "user_rights": 0,
        "international_transfers": 0
    }

    # Enhanced data collection risk assessment
    sensitive_categories = ["personal_identifiers", "contact_information", "financial_data", "health_data"]
    tracking_categories = ["behavioral_data", "technical_data", "location_data"]
    
    for category, items in data.get("data_categories", {}).items():
        if category in sensitive_categories and items:
            score += len(items) * 3
            breakdown["data_collection"] += len(items) * 3
            reasons.append(f"Collects sensitive data ({category}): {', '.join(items)}")
            factors.append(f"Sensitive data collection: {category}")
        elif category in tracking_categories and items:
            score += len(items) * 2
            breakdown["data_collection"] += len(items) * 2
            reasons.append(f"Collects tracking data ({category}): {', '.join(items)}")
            factors.append(f"Tracking data: {category}")

    # Enhanced sharing practices risk assessment
    sharing_categories = data.get("sharing_practices", {})
    if sharing_categories.get("third_parties"):
        score += len(sharing_categories["third_parties"]) * 2
        breakdown["sharing_practices"] += len(sharing_categories["third_parties"]) * 2
        reasons.append(f"Shares with third parties: {', '.join(sharing_categories['third_parties'])}")
        factors.append("Third-party data sharing")
    
    if sharing_categories.get("marketing_partners"):
        score += len(sharing_categories["marketing_partners"]) * 3
        breakdown["sharing_practices"] += len(sharing_categories["marketing_partners"]) * 3
        reasons.append(f"Shares with marketing partners: {', '.join(sharing_categories['marketing_partners'])}")
        factors.append("Marketing data sharing")

    # Enhanced purpose risk assessment
    purpose_categories = data.get("data_purposes", {})
    risky_purposes = ["marketing", "analytics"]
    for purpose in risky_purposes:
        if purpose_categories.get(purpose):
            score += len(purpose_categories[purpose])
            breakdown["purpose_risk"] += len(purpose_categories[purpose])
            reasons.append(f"Uses data for {purpose}: {', '.join(purpose_categories[purpose])}")
            factors.append(f"Data used for {purpose}")

    # User rights assessment (negative risk for good practices)
    user_rights = data.get("user_rights", [])
    if user_rights:
        score_reduction = min(len(user_rights), 3)
        score = max(0, score - score_reduction)
        breakdown["user_rights"] = -score_reduction
        reasons.append(f"User rights protections: {', '.join(user_rights[:3])}")

    # International transfers risk
    international_transfers = data.get("international_transfers", [])
    if international_transfers:
        score += len(international_transfers)
        breakdown["international_transfers"] = len(international_transfers)
        reasons.append(f"International data transfers: {len(international_transfers)} instances")
        factors.append("Cross-border data transfers")

    # Risk classification
    if score >= 15:
        risk_level = "HIGH"
    elif score >= 8:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "reasons": reasons,
        "factors": factors,
        "breakdown": breakdown
    }

def simplify_policy(data, risk):
    summary = []

    # Enhanced data collection summary
    data_categories = data.get("data_categories", {})
    collected_types = []
    for category, items in data_categories.items():
        if items:
            collected_types.append(f"{category.replace('_', ' ')} ({len(items)})")
    
    if collected_types:
        summary.append(f"This website collects data in {len(collected_types)} categories: {', '.join(collected_types)}.")

    # Enhanced sharing summary
    sharing_practices = data.get("sharing_practices", {})
    sharing_types = []
    for category, items in sharing_practices.items():
        if items:
            sharing_types.append(f"{category.replace('_', ' ')} ({len(items)})")
    
    if sharing_types:
        summary.append(f"Your data may be shared through {len(sharing_types)} types of arrangements: {', '.join(sharing_types)}.")

    # Enhanced purpose summary
    data_purposes = data.get("data_purposes", {})
    purpose_types = []
    for category, items in data_purposes.items():
        if items:
            purpose_types.append(f"{category.replace('_', ' ')} ({len(items)})")
    
    if purpose_types:
        summary.append(f"Your data is used for {len(purpose_types)} main purposes: {', '.join(purpose_types)}.")

    # User rights summary
    user_rights = data.get("user_rights", [])
    if user_rights:
        summary.append(f"The policy mentions {len(user_rights)} user rights and protections.")

    # International transfers
    international_transfers = data.get("international_transfers", [])
    if international_transfers:
        summary.append(f"The policy mentions international data transfers in {len(international_transfers)} instances.")

    # Risk summary
    summary.append(f"Overall Privacy Risk Level: {risk['risk_level']} (Score: {risk['risk_score']}).")

    if risk["risk_level"] == "HIGH":
        summary.append("This policy indicates higher privacy risk due to extensive sensitive data collection and sharing practices.")
    elif risk["risk_level"] == "MEDIUM":
        summary.append("This policy shows moderate privacy risk with some data tracking and third-party sharing.")
    else:
        summary.append("This policy shows relatively low privacy risk with limited data collection.")

    return " ".join(summary)

