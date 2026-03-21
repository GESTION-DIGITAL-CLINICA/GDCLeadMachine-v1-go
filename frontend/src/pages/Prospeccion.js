import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Target, Play, Pause, TrendingUp, MapPin, Sparkles } from 'lucide-react';
import axios from 'axios';
import { useToast } from '../hooks/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Prospeccion = () => {
  const [stats, setStats] = useState({ by_region: [] });
  const [discoveryStatus, setDiscoveryStatus] = useState({ is_running: false });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000); // Refresh every 15s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsData, statusData] = await Promise.all([
        axios.get(`${API}/stats/dashboard`),
        axios.get(`${API}/discovery/status`)
      ]);
      setStats(statsData.data);
      setDiscoveryStatus(statusData.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const triggerDiscovery = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/discovery/trigger`);
      toast({
        title: 'Búsqueda iniciada',
        description: 'El sistema está buscando nuevas clínicas...'
      });
      loadData();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'No se pudo iniciar la búsqueda',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const regionData = stats.by_region || [];
  const madridLeads = regionData.find(r => r._id === 'Madrid')?.count || 0;
  const otherLeads = regionData.filter(r => r._id !== 'Madrid' && r._id !== null);

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Prospección Automática</h1>
            <p className="text-slate-400 text-sm">Búsqueda continua de leads con IA - Prioridad Madrid</p>
          </div>
          <Button
            onClick={triggerDiscovery}
            disabled={loading || discoveryStatus.is_running}
            className="bg-[#17a2b8] hover:bg-[#138a9d] text-white shadow-lg shadow-[#17a2b8]/30"
          >
            {discoveryStatus.is_running ? (
              <>
                <Pause className="w-4 h-4 mr-2 animate-pulse" />
                Búsqueda en Curso...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Iniciar Búsqueda Manual
              </>
            )}
          </Button>
        </div>

        {/* Status Card */}
        <Card className="bg-[#1e3a5f]/50 border-[#17a2b8]/20 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-4 h-4 rounded-full ${discoveryStatus.is_running ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`}></div>
                <div>
                  <p className="text-white font-medium">
                    {discoveryStatus.is_running ? 'Búsqueda Activa' : 'Sistema en Espera'}
                  </p>
                  <p className="text-xs text-slate-400">
                    {discoveryStatus.is_running 
                      ? 'Descubriendo leads en Google Maps, Doctoralia y Páginas Amarillas'
                      : 'Próxima búsqueda automática en menos de 2 horas'}
                  </p>
                </div>
              </div>
              <Sparkles className={`w-8 h-8 ${discoveryStatus.is_running ? 'text-[#17a2b8] animate-pulse' : 'text-slate-600'}`} />
            </div>
          </CardContent>
        </Card>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-[#17a2b8]/20 border-[#17a2b8]/30 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-400 uppercase">Leads en Madrid</p>
                <MapPin className="w-5 h-5 text-[#17a2b8]" />
              </div>
              <p className="text-3xl font-bold text-white">{madridLeads}</p>
              <p className="text-xs text-slate-400 mt-1">Prioridad #1</p>
            </CardContent>
          </Card>

          <Card className="bg-emerald-500/20 border-emerald-500/30 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-400 uppercase">Score Alto (≥7)</p>
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              </div>
              <p className="text-3xl font-bold text-white">{stats.high_score || 0}</p>
              <p className="text-xs text-slate-400 mt-1">Listos para contactar</p>
            </CardContent>
          </Card>

          <Card className="bg-purple-500/20 border-purple-500/30 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-slate-400 uppercase">Total Leads</p>
                <Target className="w-5 h-5 text-purple-400" />
              </div>
              <p className="text-3xl font-bold text-white">{stats.total_leads || 0}</p>
              <p className="text-xs text-slate-400 mt-1">En base de datos</p>
            </CardContent>
          </Card>
        </div>

        {/* Regions Table */}
        <Card className="bg-[#1e3a5f]/50 border-[#17a2b8]/20 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white text-base font-medium">Leads por Comunidad Autónoma</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {/* Madrid (Priority) */}
              {madridLeads > 0 && (
                <div className="flex items-center justify-between p-4 bg-[#17a2b8]/10 rounded-lg border border-[#17a2b8]/30">
                  <div className="flex items-center gap-3">
                    <MapPin className="w-5 h-5 text-[#17a2b8]" />
                    <div>
                      <p className="text-white font-medium">Madrid</p>
                      <p className="text-xs text-slate-400">Prioridad máxima</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-white">{madridLeads}</p>
                    <p className="text-xs text-[#17a2b8]">leads</p>
                  </div>
                </div>
              )}

              {/* Other Regions */}
              {otherLeads.map((region, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                  <div className="flex items-center gap-3">
                    <MapPin className="w-5 h-5 text-slate-400" />
                    <div>
                      <p className="text-white font-medium">{region._id || 'Sin categorizar'}</p>
                      <p className="text-xs text-slate-400">Comunidad autónoma</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-white">{region.count}</p>
                    <p className="text-xs text-slate-400">leads</p>
                  </div>
                </div>
              ))}

              {regionData.length === 0 && (
                <p className="text-center text-slate-500 py-8">
                  No hay datos de regiones todavía
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-6">
            <h3 className="text-white font-medium mb-3">Cómo funciona la prospección automática</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li className="flex items-start gap-2">
                <span className="text-[#17a2b8]">•</span>
                <span><strong className="text-white">Prioridad Madrid:</strong> Busca primero en Madrid y alrededores</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#17a2b8]">•</span>
                <span><strong className="text-white">Fuentes múltiples:</strong> Google Maps, Doctoralia, Páginas Amarillas</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#17a2b8]">•</span>
                <span><strong className="text-white">IA scoring automático:</strong> Valida autenticidad y calidad de cada lead</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#17a2b8]">•</span>
                <span><strong className="text-white">Queue automática:</strong> Leads con score ≥5 van directo a cola de emails</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#17a2b8]">•</span>
                <span><strong className="text-white">Continuo 24/7:</strong> Se ejecuta cada 2 horas automáticamente</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Prospeccion;
