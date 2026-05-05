import { NavLink, type NavLinkRenderProps } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  FolderTree,
  X
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface SidebarProps {
  mobileOpen: boolean;
  setMobileOpen: (val: boolean) => void;
  desktopOpen: boolean;
}

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Quản lý bài báo', path: '/articles', icon: FileText },
  { name: 'Quản lý danh mục', path: '/categories', icon: FolderTree },
  { name: 'Tài khoản hệ thống', path: '/users', icon: Users },
];

const Sidebar = ({ mobileOpen, setMobileOpen, desktopOpen }: SidebarProps) => {
  return (
    <>
      <div
        className={cn(
          'fixed inset-0 z-20 bg-black/50 transition-opacity lg:hidden',
          mobileOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={() => setMobileOpen(false)}
      />

      <div
        className={cn(
          'fixed inset-y-0 left-0 z-30 transform transition-all duration-300 lg:relative lg:inset-auto lg:translate-x-0 lg:shadow-none',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
          desktopOpen
            ? 'w-64 lg:w-64 lg:opacity-100 lg:pointer-events-auto'
            : 'w-64 lg:w-0 lg:opacity-0 lg:pointer-events-none lg:overflow-hidden'
        )}
      >
        <aside className="flex h-full w-64 flex-col border-r border-gray-100 bg-white shadow-xl lg:shadow-none">
          <div className="flex h-16 items-center justify-between px-6 border-b border-gray-100">
            <span className="text-xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Admin Portal
            </span>
            <button onClick={() => setMobileOpen(false)} className="lg:hidden text-gray-500 hover:text-gray-700">
              <X size={20} />
            </button>
          </div>

          <nav className="mt-6 px-4 space-y-2">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }: NavLinkRenderProps) =>
                  cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-green-50 text-green-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )
                }
                onClick={() => setMobileOpen(false)}
              >
                <item.icon size={20} />
                {item.name}
              </NavLink>
            ))}
          </nav>
        </aside>
      </div>
    </>
  );
};

export default Sidebar;
