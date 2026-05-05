import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import { authService } from '../../services/auth.service';
import { useAuthStore } from '../../store/authStore';

const LoginPage = () => {
  const [username, setUsername] = useState('admin@pmq.com'); // Mặc định cho luồng test
  const [password, setPassword] = useState('admin');
  const [errorMsg, setErrorMsg] = useState('');
  
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const loginMutation = useMutation({
    mutationFn: () => authService.login(username, password),
    onSuccess: (data) => {
      // data.result = { accessToken, user: {id, username, role} }
      if (data.result.user.role !== 'ROLE_ADMIN' && data.result.user.role !== 'ADMIN') {
        setErrorMsg('Tài khoản không có quyền Admin');
        return;
      }
      setAuth(data.result.accessToken, data.result.user);
      navigate('/dashboard', { replace: true });
    },
    onError: (error: unknown) => {
      if (axios.isAxiosError(error)) {
        const apiMessage = (error.response?.data as { message?: string } | undefined)?.message;
        setErrorMsg(apiMessage || 'Tên đăng nhập hoặc mật khẩu không đúng');
        return;
      }
      setErrorMsg('Tên đăng nhập hoặc mật khẩu không đúng');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setErrorMsg('Vui lòng nhập đầy đủ thông tin');
      return;
    }
    setErrorMsg('');
    loginMutation.mutate();
  };

  return (
    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
      {errorMsg && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center font-medium">
          {errorMsg}
        </div>
      )}
      
      <div className="space-y-4 rounded-md shadow-sm">
        <div>
          <label className="block text-sm font-medium text-gray-700">Tên đăng nhập</label>
          <input
            type="text"
            required
            className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
            placeholder="admin / admin@pmq.com"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Mật khẩu</label>
          <input
            type="password"
            required
            className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
      </div>

      <div>
        <button
          type="submit"
          disabled={loginMutation.isPending}
          className="group relative w-full flex justify-center py-2.5 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-70 disabled:cursor-not-allowed transition-colors"
        >
          <span className="absolute left-0 inset-y-0 flex items-center pl-3">
            <LogIn className="h-5 w-5 text-green-500 group-hover:text-green-400" aria-hidden="true" />
          </span>
          {loginMutation.isPending ? 'Đang xác thực...' : 'Đăng nhập'}
        </button>
      </div>
    </form>
  );
};

export default LoginPage;
