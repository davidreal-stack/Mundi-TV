'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { API_CONFIG } from '@/lib/api';

interface ChannelCardProps {
  channel: {
    id: number;
    title: string;
    time: string;
    category: string;
    status: string;
    link: string;
    resolution: string;
    type?: string;
    content_id?: string;
  };
}

export default function ChannelCard({ channel }: ChannelCardProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleWatch = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (channel.type === 'dash') {
      router.push(`/channel?content_id=${channel.content_id}`);
      return;
    }

    try {
      // Paso 1: Generar token JWT
      const tokenResponse = await fetch(`${API_CONFIG.BASE_URL}/api/generate-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          link: channel.link,
        }),
      });

      if (!tokenResponse.ok) {
        throw new Error('Error al generar token');
      }

      const tokenData = await tokenResponse.json();
      const token = tokenData.token;

      // Paso 2: Redirigir a la página del reproductor con el token
      router.push(`/channel?token=${token}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
      setLoading(false);
    }
  };

  return (
    <div className="card-dark rounded-xl overflow-hidden group h-full flex flex-col fade-in hover:scale-105 transition-transform duration-300">
      {/* Header con categoría */}
      <div className="relative overflow-hidden h-32 bg-gradient-to-br from-neon-blue/20 to-neon-purple/20 flex items-center justify-center">
        {/* Animated background */}
        <div className="absolute inset-0 opacity-30 group-hover:opacity-50 transition-opacity">
          <div className="absolute inset-0 bg-gradient-to-r from-neon-blue to-neon-purple"></div>
        </div>

        <div className="relative z-10 text-center px-4">
          <p className="text-xs uppercase tracking-widest text-neon-blue font-bold mb-2">
            {channel.category}
          </p>
          <h3 className="text-lg md:text-xl font-bold text-white truncate group-hover:text-neon-blue transition-colors">
            {channel.title}
          </h3>
        </div>

        {/* Decorative corners */}
        <div className="absolute top-2 right-2 w-2 h-2 border-t-2 border-r-2 border-neon-blue/50"></div>
        <div className="absolute bottom-2 left-2 w-2 h-2 border-b-2 border-l-2 border-neon-blue/50"></div>
      </div>

      {/* Content */}
      <div className="flex-1 p-4 flex flex-col justify-between">
        {/* Info */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="badge-live">
              <span className="pulse-dot"></span>
              {channel.type === 'dash' ? 'TV Azteca (DASH)' : 'EN VIVO'}
            </div>
            <span className="text-xs bg-dark-700/50 px-3 py-1 rounded text-gray-300 font-bold">
              {channel.resolution}
            </span>
          </div>

          <p className="text-gray-400 text-xs mb-3">
            📡 {channel.time}
          </p>

          {error && (
            <p className="text-red-400 text-xs mb-3 bg-red-900/20 p-2 rounded border border-red-600/30">
              ❌ {error}
            </p>
          )}
        </div>

        {/* Button */}
        <button
          onClick={handleWatch}
          disabled={loading}
          className={`w-full py-3 rounded-lg font-bold transition-all duration-300 flex items-center justify-center gap-2 ${
            loading
              ? 'bg-dark-700 text-gray-500 cursor-not-allowed'
              : 'btn-neon'
          }`}
        >
          {loading ? (
            <>
              <span className="inline-block w-4 h-4 border-2 border-neon-blue border-t-transparent rounded-full animate-spin"></span>
              Conectando...
            </>
          ) : (
            <>
              ▶️ Ver en HD
            </>
          )}
        </button>
      </div>

      {/* Bottom border glow */}
      <div className="h-[1px] bg-gradient-to-r from-transparent via-neon-blue/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
    </div>
  );
}
