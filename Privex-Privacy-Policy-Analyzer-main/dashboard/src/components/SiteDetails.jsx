import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Shield, AlertTriangle, Globe, Users, Database, FileText } from 'lucide-react';

const SiteDetails = () => {
  const { url } = useParams();
  const navigate = useNavigate();
  const [siteData, setSiteData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (url) {
      fetchSiteDetails();
    }
  }, [url]);

  const fetchSiteDetails = async () => {
    try {
      const response = await fetch(`/api/site/${encodeURIComponent(url)}`);
      if (!response.ok) {
        throw new Error('Site not found');
      }
      const data = await response.json();
      setSiteData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner h-8 w-8"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button onClick={() => navigate('/')} className="btn btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!siteData) {
    return null;
  }

  const riskLevel = siteData.risk_level?.toLowerCase() || 'unknown';
  const riskColor = {
    high: 'text-red-600 bg-red-100',
    medium: 'text-yellow-600 bg-yellow-100',
    low: 'text-green-600 bg-green-100',
    unknown: 'text-gray-600 bg-gray-100'
  }[riskLevel] || 'text-gray-600 bg-gray-100';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/')}
            className="btn btn-outline"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {new URL(siteData.url).hostname}
            </h1>
            <p className="text-gray-600">{siteData.url}</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${riskColor}`}>
          {siteData.risk_level || 'Unknown'} Risk
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="flex items-center">
            <Database className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Data Types</p>
              <p className="text-2xl font-bold text-gray-900">
                {siteData.data_collected?.length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Third Parties</p>
              <p className="text-2xl font-bold text-gray-900">
                {siteData.shared_with?.length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Risk Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {siteData.risk_score || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Status</p>
              <p className="text-lg font-bold text-gray-900 capitalize">
                {siteData.status || 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Collected */}
        <div className="stat-card">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Database className="h-5 w-5 mr-2 text-blue-600" />
            Data Collected
          </h3>
          <div className="space-y-2">
            {siteData.data_collected?.length > 0 ? (
              siteData.data_collected.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">{item}</span>
                  <span className="text-xs text-gray-500">Personal Data</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">No data collection information available</p>
            )}
          </div>
        </div>

        {/* Third Parties */}
        <div className="stat-card">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Users className="h-5 w-5 mr-2 text-green-600" />
            Shared With Third Parties
          </h3>
          <div className="space-y-2">
            {siteData.shared_with?.length > 0 ? (
              siteData.shared_with.map((party, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">{party}</span>
                  <span className="text-xs text-gray-500">Third Party</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">No third-party sharing information available</p>
            )}
          </div>
        </div>

        {/* Purposes */}
        <div className="stat-card">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Globe className="h-5 w-5 mr-2 text-purple-600" />
            Data Usage Purposes
          </h3>
          <div className="space-y-2">
            {siteData.purposes?.length > 0 ? (
              siteData.purposes.map((purpose, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700 capitalize">{purpose}</span>
                  <span className="text-xs text-gray-500">Purpose</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">No purpose information available</p>
            )}
          </div>
        </div>

        {/* Analysis Summary */}
        <div className="stat-card">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <FileText className="h-5 w-5 mr-2 text-yellow-600" />
            Analysis Summary
          </h3>
          <div className="prose prose-sm max-w-none">
            <p className="text-gray-700 text-sm whitespace-pre-line">
              {siteData.summary || 'No summary available'}
            </p>
          </div>
          
          {siteData.full_analysis?.rag_analysis && (
            <div className="mt-4 space-y-3">
              <h4 className="font-medium text-gray-900">RAG Analysis Details</h4>
              
              {siteData.full_analysis.rag_analysis.compliance_issues?.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-red-600 mb-2">Compliance Issues</h5>
                  <ul className="text-sm text-gray-700 space-y-1">
                    {siteData.full_analysis.rag_analysis.compliance_issues.map((issue, index) => (
                      <li key={index} className="flex items-start">
                        <AlertTriangle className="h-3 w-3 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                        {issue}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {siteData.full_analysis.rag_analysis.recommendations?.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-blue-600 mb-2">Recommendations</h5>
                  <ul className="text-sm text-gray-700 space-y-1">
                    {siteData.full_analysis.rag_analysis.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start">
                        <Shield className="h-3 w-3 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SiteDetails;
