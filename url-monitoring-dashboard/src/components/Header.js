// src/components/Header.js
import { useState } from 'react';
import { MoonIcon, SunIcon, Bars3Icon, XMarkIcon } from '@heroicons/react/24/solid';
import useStore from '../store/useStore';

function Header() {
  const [darkMode, setDarkMode] = useState(false);
  const { isSidebarOpen, toggleSidebar } = useStore();

  const toggleDarkModeHandler = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="bg-white dark:bg-gray-800 shadow p-4 flex justify-between items-center">
      <div className="flex items-center">
        {/* 모바일 화면에서 햄버거 메뉴 아이콘 표시 */}
        <button
          className="md:hidden mr-4 focus:outline-none"
          onClick={toggleSidebar}
          aria-label="사이드바 토글"
        >
          {isSidebarOpen ? (
            <XMarkIcon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
          ) : (
            <Bars3Icon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
          )}
        </button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          URL 상태 모니터링 대시보드
        </h1>
      </div>
      <button onClick={toggleDarkModeHandler} aria-label="다크 모드 토글">
        {darkMode ? (
          <SunIcon className="w-6 h-6 text-yellow-500" />
        ) : (
          <MoonIcon className="w-6 h-6 text-gray-500" />
        )}
      </button>
    </header>
  );
}

export default Header;
