import React from 'react';
import { NavLink } from 'react-router-dom';
import { BarChart3, Shield, History, Settings, Globe, AlertTriangle } from 'lucide-react';

const Sidebar = ({ stats }) => {
  const menuItems = [
    { name: 'Dashboard', icon: BarChart3, path: '/' },
    { name: 'Sites', icon: Globe, path: '/sites' },
    { name: 'Risk Analysis', icon: Shield, path: '/risks' },
    { name: 'History', icon: History, path: '/history' },
    { name: 'Settings', icon: Settings, path: '/settings' },
  ];

  return (
    <div className="w-64 bg-white shadow-lg">
      <div className="p-6">
        <div className="flex items-center">
          <Shield className="h-8 w-8 text-blue-600" />
          <span className="ml-2 text-xl font-bold text-gray-900">Privacy Analyzer</span>
        </div>
      </div>

      <nav className="mt-6">
        <div className="px-4 space-y-2">
          {menuItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
            >
              <item.icon className="h-5 w-5 mr-3" />
              {item.name}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Stats Summary */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Total Sites</span>
            <span className="font-medium">{stats.total_sites || 0}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">High Risk</span>
            <span className="font-medium text-red-600">{stats.high_risk_sites || 0}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Cookie Banners</span>
            <span className="font-medium">{stats.sites_with_cookie_banners || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
