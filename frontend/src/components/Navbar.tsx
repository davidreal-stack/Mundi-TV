'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { API_CONFIG } from '@/lib/api';

export default function Navbar() {
  const [serverStatus, setServerStatus] = useState('checking');

  useEffect(() => {
    const checkServer = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/health`, {
          method: 'GET',
          mode: 'cors',
        });
        
        if (response.ok) {
          setServerStatus('online');
        } else {
          setServerStatus('offline');
        }
      } catch {
        setServerStatus('offline');
      }
    };

    checkServer();
    const interval = setInterval(checkServer, 30000); // Verificar cada 30 segundos
    
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-dark-900/80 backdrop-blur border-b border-dark-700/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="text-4xl">🌍</div>
            <div>
              <h1 className="text-2xl font-black bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent group-hover:from-neon-purple group-hover:to-neon-blue transition-all duration-300">
                MUNDI TV
              </h1>
              <p className="text-xs text-gray-500 group-hover:text-neon-blue/70 transition-colors">
                Streaming en Vivo
              </p>
            </div>
          </Link>

          {/* Centro - Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <Link
              href="/"
              className="text-gray-300 hover:text-neon-blue transition-colors font-medium flex items-center gap-2"
            >
              📺 Dashboard
            </Link>
            <a
              href="#"
              className="text-gray-300 hover:text-neon-blue transition-colors font-medium flex items-center gap-2"
            >
              ⚙️ Configuración
            </a>
          </div>

          {/* Server Status */}
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg bg-dark-800/50 border border-dark-700/50">
              <div
                className={`w-2 h-2 rounded-full ${
                  serverStatus === 'online'
                    ? 'bg-green-500 animate-pulse'
                    : serverStatus === 'checking'
                    ? 'bg-yellow-500 animate-pulse'
                    : 'bg-red-500'
                }`}
              ></div>
              <span className="text-xs text-gray-400 font-medium">
                {serverStatus === 'online'
                  ? 'Backend 🟢'
                  : serverStatus === 'checking'
                  ? 'Verificando...'
                  : 'Backend 🔴'}
              </span>
            </div>

            {/* Mobile Menu Button */}
            <button className="md:hidden text-gray-300 hover:text-neon-blue transition-colors text-2xl">
              ☰
            </button>
          </div>
        </div>
      </div>

      {/* Top Border Glow Effect */}
      <div className="h-[1px] bg-gradient-to-r from-transparent via-neon-blue to-transparent opacity-30"></div>
    </nav>
  );
}
