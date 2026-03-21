import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Mail, CheckCircle, Clock, AlertCircle, Search, Send } from 'lucide-react';
import { getEmailStats, getEmailQueue } from '../services/api';

const Outreach = () => {
  const [stats, setStats] = useState({ total_sent: 0, pending: 0, failed: 0, active_accounts: 0 });
  const [emails, setEmails] = useState([]);
  const [filteredEmails, setFilteredEmails] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    filterEmails();
  }, [emails, searchTerm, statusFilter]);

  const loadData = async () => {
    try {
      const [statsData, queueData] = await Promise.all([
        getEmailStats(),
        getEmailQueue()
      ]);
      setStats(statsData);
      setEmails(queueData.queue || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterEmails = () => {
    let filtered = emails;

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(email => email.status === statusFilter);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(email => 
        email.clinic_data?.clinica?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        email.clinic_data?.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        email.clinic_data?.ciudad?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredEmails(filtered);
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'sent':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Mail className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      sent: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      pending: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      failed: 'bg-red-500/20 text-red-400 border-red-500/30'
    };
    return (
      <Badge className={`${styles[status]} text-xs font-medium`}>
        {status === 'sent' ? 'Enviado' : status === 'pending' ? 'Pendiente' : 'Fallido'}
      </Badge>
    );
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Outreach</h1>
          <p className="text-slate-400 text-sm">Gestión y seguimiento de emails enviados</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-emerald-500/20 border-emerald-500/30 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-400 uppercase">Enviados</p>
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              </div>
              <p className="text-3xl font-bold text-white">{stats.total_sent}</p>
            </CardContent>
          </Card>

          <Card className="bg-amber-500/20 border-amber-500/30 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-400 uppercase">En Cola</p>
                <Clock className="w-5 h-5 text-amber-400" />
              </div>
              <p className="text-3xl font-bold text-white">{stats.pending}</p>
            </CardContent>
          </Card>

          <Card className="bg-red-500/20 border-red-500/30 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-400 uppercase">Fallidos</p>
                <AlertCircle className="w-5 h-5 text-red-400" />
              </div>
              <p className="text-3xl font-bold text-white">{stats.failed}</p>
            </CardContent>
          </Card>

          <Card className="bg-[#17a2b8]/20 border-[#17a2b8]/30 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-400 uppercase">Tasa de Éxito</p>
                <Send className="w-5 h-5 text-[#17a2b8]" />
              </div>
              <p className="text-3xl font-bold text-white">
                {stats.total_sent > 0 ? Math.round((stats.total_sent / (stats.total_sent + stats.failed)) * 100) : 0}%
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="bg-[#1e3a5f]/50 border-[#17a2b8]/20 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Buscar por clínica, email o ciudad..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div className="flex gap-2">
                {['all', 'sent', 'pending', 'failed'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      statusFilter === status
                        ? 'bg-[#17a2b8] text-white'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {status === 'all' ? 'Todos' : status === 'sent' ? 'Enviados' : status === 'pending' ? 'Pendientes' : 'Fallidos'}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Email List */}
        <Card className="bg-[#1e3a5f]/50 border-[#17a2b8]/20 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white text-base font-medium">
              Historial de Emails ({filteredEmails.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">Cargando...</div>
            ) : filteredEmails.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <Mail className="w-12 h-12 mx-auto mb-3 text-slate-600" />
                <p>No se encontraron emails</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredEmails.map((email, index) => (
                  <div key={index} className="p-4 bg-slate-800/50 rounded-lg border border-[#17a2b8]/20 hover:border-[#17a2b8]/40 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {getStatusIcon(email.status)}
                          <h3 className="text-white font-medium">{email.clinic_data?.clinica || 'N/A'}</h3>
                          {getStatusBadge(email.status)}
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                          <div className="text-slate-400">
                            <span className="text-slate-500">Email:</span> {email.clinic_data?.email || 'N/A'}
                          </div>
                          <div className="text-slate-400">
                            <span className="text-slate-500">Ciudad:</span> {email.clinic_data?.ciudad || 'N/A'}
                          </div>
                          <div className="text-slate-400">
                            <span className="text-slate-500">Añadido:</span> {new Date(email.added_at).toLocaleDateString('es-ES')}
                          </div>
                        </div>
                        {email.sent_at && (
                          <div className="text-sm text-slate-400 mt-2">
                            <span className="text-slate-500">Enviado:</span> {new Date(email.sent_at).toLocaleString('es-ES')}
                          </div>
                        )}
                        {email.attempts > 1 && (
                          <div className="text-sm text-amber-400 mt-2">
                            ⚠️ Intentos: {email.attempts}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Outreach;
