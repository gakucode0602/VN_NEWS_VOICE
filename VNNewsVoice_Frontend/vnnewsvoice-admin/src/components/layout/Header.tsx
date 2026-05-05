import { Menu, LogOut, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/auth.service';

interface HeaderProps {
  toggleMobileSidebar: () => void;
  toggleDesktopSidebar: () => void;
  desktopSidebarOpen: boolean;
}

const Header = ({
  toggleMobileSidebar,
  toggleDesktopSidebar,
  desktopSidebarOpen,
}: HeaderProps) => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authService.logout();
    } finally {
      logout();
      navigate('/login');
    }
  };

  return (
    <header className="flex h-16 items-center justify-between bg-white px-6 shadow-sm z-10">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleMobileSidebar}
          className="text-gray-500 hover:text-gray-700 lg:hidden p-1 rounded-md hover:bg-gray-100 transition-colors"
          aria-label="Mở sidebar"
        >
          <Menu size={24} />
        </button>

        <button
          onClick={toggleDesktopSidebar}
          className="hidden lg:inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
          aria-label={desktopSidebarOpen ? 'Thu gọn sidebar' : 'Mở rộng sidebar'}
        >
          {desktopSidebarOpen ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
          {desktopSidebarOpen ? 'Thu gọn menu' : 'Mở menu'}
        </button>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">{user?.username || 'Admin User'}</span>
          <span className="px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded-full">
            {user?.role?.replace('ROLE_', '') || 'ADMIN'}
          </span>
        </div>
        
        <div className="h-8 w-px bg-gray-200 mx-2"></div>
        
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 px-3 py-2 rounded-lg transition-colors"
        >
          <LogOut size={18} />
          <span className="hidden sm:inline">Đăng xuất</span>
        </button>
      </div>
    </header>
  );
};

export default Header;
