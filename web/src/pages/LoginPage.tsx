import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({});
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const setToken = useAuthStore((s) => s.setToken);
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const state = location.state as { registeredUsername?: string } | null;
    if (state?.registeredUsername) {
      setUsername(state.registeredUsername);
      setSuccess('注册成功，请登录');
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, []);

  const clearErrors = () => {
    setError('');
    setFieldErrors({});
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearErrors();

    if (username.trim() === '') {
      setFieldErrors({ username: '请输入用户名' });
      return;
    }
    if (password === '') {
      setFieldErrors({ password: '请输入密码' });
      return;
    }

    setLoading(true);
    try {
      const data = await authApi.login({ username, password });
      setToken(data.access_token);
      await fetchUser();
      navigate('/dashboard');
    } catch (err: any) {
      if (!err.response) {
        setError('网络连接失败，请稍后重试');
      } else if (err.response.status === 401) {
        setError('用户名或密码错误');
        setPassword('');
        document.getElementById('密码')?.focus();
      } else {
        setError('服务异常，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="flex w-[480px] flex-col items-center justify-center bg-blue-600 px-12 text-white">
        <h1 className="mb-3 text-4xl font-bold tracking-tight">EasyBX</h1>
        <p className="text-lg text-blue-100">智能发票报销助手</p>
      </div>
      <div className="flex flex-1 items-center justify-center bg-gray-50">
        <div className="w-full max-w-sm rounded-lg bg-white p-8 shadow-md">
          {success && (
            <p className="mb-4 rounded-md bg-green-50 px-4 py-3 text-sm font-medium text-green-700">
              {success}
            </p>
          )}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              label="用户名"
              value={username}
              error={fieldErrors.username}
              onChange={(e) => {
                setUsername(e.target.value);
                clearErrors();
              }}
            />
            <Input
              label="密码"
              type="password"
              value={password}
              error={fieldErrors.password}
              onChange={(e) => {
                setPassword(e.target.value);
                clearErrors();
              }}
            />
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? '登录中...' : '登录'}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500">
            还没有账号？{' '}
            <Link to="/register" className="text-blue-600 hover:underline">
              注册
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
