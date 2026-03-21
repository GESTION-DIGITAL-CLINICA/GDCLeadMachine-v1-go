import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Target, Mail, Settings } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/leads', label: 'Leads', icon: Users },
    { path: '/prospeccion', label: 'Prospección', icon: Target },
    { path: '/outreach', label: 'Outreach', icon: Mail },
    { path: '/config', label: 'Config', icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Top Navigation */}
      <nav className="bg-[#1e3a5f] border-b border-[#17a2b8]/20">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <img 
                src="https://customer-assets.emergentagent.com/job_ecstatic-knuth-2/artifacts/u25di08h_GDC%20LOGO.jpg" 
                alt="GDC Logo" 
                className="h-10 w-auto"
              />
              <div className="hidden sm:block">
                <div className="text-white font-bold text-sm">GESTIÓN</div>
                <div className="text-[#17a2b8] font-bold text-xs -mt-1">DIGITAL CLÍNICA</div>
              </div>
            </div>

            {/* Nav Items */}
            <div className="flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-[#17a2b8] text-white shadow-lg shadow-[#17a2b8]/50'
                        : 'text-slate-300 hover:text-white hover:bg-[#1e3a5f]/80'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden md:inline">{item.label}</span>
                  </Link>
                );
              })}
            </div>

            {/* Logout Button */}
            <Button
              onClick={handleLogout}
              variant="ghost"
              size="sm"
              className="text-slate-300 hover:text-white hover:bg-[#1e3a5f]/80"
            >
              Logout
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  );
};

export default Layout;
