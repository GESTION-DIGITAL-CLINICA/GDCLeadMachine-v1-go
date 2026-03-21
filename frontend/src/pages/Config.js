import React from 'react';
import Layout from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Settings } from 'lucide-react';

const Config = () => {
  return (
    <Layout>
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="bg-[#1e3a5f]/50 border-[#17a2b8]/20 backdrop-blur-sm max-w-md w-full">
          <CardContent className="p-12 text-center">
            <Settings className="w-16 h-16 text-[#17a2b8] mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Configuración</h2>
            <p className="text-slate-400">Esta sección está en desarrollo</p>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Config;
