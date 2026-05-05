import { useState, useEffect, type ReactElement } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from './store/authStore';
import { AUTH_SERVICE_URL } from './lib/apiClient';

// Layouts & Pages
import ProtectedLayout from './components/layout/ProtectedLayout';
import AuthLayout from './components/layout/AuthLayout';
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import ArticlesPage from './pages/articles/ArticlesPage';
import ArticleDetailPage from './pages/articles/ArticleDetailPage';
import CategoriesPage from './pages/categories/CategoriesPage';
import UsersPage from './pages/users/UsersPage';

// Loading spinner hiện trong lúc silent-restore session
const FullScreenLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="flex flex-col items-center gap-3">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-green-500 border-t-transparent" />
      <p className="text-sm text-gray-500">Đang khôi phục phiên đăng nhập…</p>
    </div>
  </div>
);

/**
 * Bảo vệ route — yêu cầu đăng nhập.
 *
 * Luồng xử lý khi page load/refresh:
 * 1. accessToken có trong memory → cho qua ngay.
 * 2. accessToken = null nhưng user còn persist → thử silent refresh
 *    dùng HttpOnly cookie. Thành công → cập nhật token, tiếp tục.
 *    Thất bại → logout, redirect login.
 * 3. Cả hai null → redirect login ngay.
 */
const RequireAuth = ({ children }: { children: ReactElement }) => {
  const { accessToken, user, updateAccessToken, logout } = useAuthStore();
  
  // Chỉ restore nếu không có token memory nhưng có user persist (refresh page)
  const [isRestoring, setIsRestoring] = useState(() => !accessToken && !!user);

  useEffect(() => {
    // Nếu không cần restore (có token hoặc chưa login) -> done
    if (!isRestoring) return;

    let cancelled = false;
    axios
      .post<{ result?: { accessToken?: string }; accessToken?: string }>(
        `${AUTH_SERVICE_URL}/api/auth/refresh`,
        {},
        { withCredentials: true }
      )
      .then((res) => {
        if (cancelled) return;
        const token = res.data.result?.accessToken ?? res.data.accessToken;
        if (token) {
          updateAccessToken(token);
        } else {
          logout();
        }
      })
      .catch(() => {
        if (!cancelled) logout();
      })
      .finally(() => {
        if (!cancelled) setIsRestoring(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isRestoring, updateAccessToken, logout]);

  if (isRestoring) return <FullScreenLoader />;
  if (!accessToken) return <Navigate to="/login" replace />;
  return children;
};

// Routing tổng quan Admin Portal
function App() {
  return (
    <Routes>
      {/* Public Routes (Không cần đăng nhập) */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* Protected Routes (Bắt buộc đăng nhập với role ADMIN) */}
      <Route
        path="/"
        element={
          <RequireAuth>
            <ProtectedLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        
        {/* Quản lý Bài Báo (ArticleService) */}
        <Route path="articles" element={<ArticlesPage />} />
        <Route path="articles/:id" element={<ArticleDetailPage />} />

        {/* Quản lý Danh Mục (ArticleService) */}
        <Route path="categories" element={<CategoriesPage />} />
        
        {/* Quản lý Users (AuthService) */}
        <Route path="users" element={<UsersPage />} />
      </Route>

      {/* 404 Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
