import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Mail, Lock, ArrowLeft } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const Signup = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { signup } = useAuth();
  const { toast } = useToast();

  const handleSignup = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      toast({
        title: 'Error',
        description: 'Las contraseñas no coinciden',
        variant: 'destructive'
      });
      return;
    }

    if (password.length < 8) {
      toast({
        title: 'Error',
        description: 'La contraseña debe tener al menos 8 caracteres',
        variant: 'destructive'
      });
      return;
    }

    setLoading(true);
    try {
      await signup(email, password);
      toast({
        title: 'Cuenta creada',
        description: 'Por favor verifica tu email'
      });
      navigate('/verify-email', { state: { email } });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'No se pudo crear la cuenta',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1e3a5f] via-slate-900 to-slate-950 p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-2xl shadow-[#17a2b8]/10 p-8">
          {/* Back Button */}
          <Link
            to="/login"
            className="inline-flex items-center text-slate-600 hover:text-[#17a2b8] mb-6 text-sm"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver al inicio de sesión
          </Link>

          {/* Title */}
          <h1 className="text-2xl font-semibold text-slate-900 mb-8">
            Crea tu cuenta
          </h1>

          {/* Form */}
          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-slate-700 mb-2 block text-sm">
                Email
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 h-11 border-slate-200"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="password" className="text-slate-700 mb-2 block text-sm">
                Password
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Min. 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 h-11 border-slate-200"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="confirmPassword" className="text-slate-700 mb-2 block text-sm">
                Confirm Password
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Re-enter password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="pl-10 h-11 border-slate-200"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-[#17a2b8] hover:bg-[#138a9d] text-white mt-6 shadow-lg shadow-[#17a2b8]/30"
              disabled={loading}
            >
              {loading ? 'Creando cuenta...' : 'Crear cuenta'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Signup;
