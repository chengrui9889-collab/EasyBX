import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '@/api/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export function RegisterPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string; displayName?: string }>({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

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
    if (displayName.trim() === '') {
      setFieldErrors({ displayName: '请输入显示名称' });
      return;
    }
    if (password === '') {
      setFieldErrors({ password: '请输入密码' });
      return;
    }
    if (password.length < 6) {
      setFieldErrors({ password: '密码至少需要 6 个字符' });
      return;
    }

    setLoading(true);
    try {
      await authApi.register({ username, password, display_name: displayName });
      navigate('/login', { state: { registeredUsername: username } });
    } catch (err: any) {
      if (!err.response) {
        setError('网络连接失败，请稍后重试');
      } else if (err.response.status === 409) {
        setError('用户名已存在');
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
              label="显示名称"
              value={displayName}
              error={fieldErrors.displayName}
              onChange={(e) => {
                setDisplayName(e.target.value);
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
              {loading ? '注册中...' : '注册'}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500">
            已有账号？{' '}
            <Link to="/login" className="text-blue-600 hover:underline">
              登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
