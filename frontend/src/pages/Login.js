import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Package } from 'lucide-react';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [role, setRole] = useState('admin');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login';
      const payload = isRegister
        ? { email, password, name, role }
        : { email, password };

      const response = await api.post(endpoint, payload);
      const { access_token, user } = response.data;

      login(access_token, user);
      toast.success(`Welcome ${user.name}!`);
      navigate('/dashboard');
    } catch (error) {
      toast.error(
        error.response?.data?.detail || 'Authentication failed'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <img src="/furni-logo.png" alt="FURNI" className="h-16" />
          </div>
          <h1 className="text-3xl font-bold font-[Manrope] text-foreground mb-2">
            FURNI Operations Hub
          </h1>
          <p className="text-muted-foreground">Manage your furniture business seamlessly</p>
        </div>

        <Card className="shadow-lg border-border/60">
          <CardHeader>
            <CardTitle className="font-[Manrope]">{isRegister ? 'Create Account' : 'Sign In'}</CardTitle>
            <CardDescription>
              {isRegister
                ? 'Register a new account to get started'
                : 'Enter your credentials to access the dashboard'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegister && (
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    data-testid="register-name-input"
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    placeholder="John Doe"
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  data-testid="login-email-input"
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  data-testid="login-password-input"
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                />
              </div>

              {isRegister && (
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <select
                    data-testid="register-role-select"
                    id="role"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background/50 focus:border-primary focus:ring-1 focus:ring-primary"
                    required
                  >
                    <option value="admin">Admin</option>
                    <option value="sales">Sales</option>
                    <option value="support">Support</option>
                    <option value="dispatch">Dispatch</option>
                    <option value="warehouse">Warehouse</option>
                  </select>
                </div>
              )}

              <Button
                data-testid="login-submit-button"
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
              </Button>
            </form>

            <div className="mt-4 text-center text-sm">
              <button
                data-testid="toggle-auth-mode-button"
                type="button"
                onClick={() => setIsRegister(!isRegister)}
                className="text-primary hover:underline"
              >
                {isRegister
                  ? 'Already have an account? Sign in'
                  : "Don't have an account? Register"}
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
