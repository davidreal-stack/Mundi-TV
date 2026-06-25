'use client';

import { useState, useEffect } from 'react';
import ChannelCard from '@/components/ChannelCard';
import { API_CONFIG } from '@/lib/api';

interface Channel {
  id: number;
  title: string;
  time: string;
  category: string;
  status: string;
  link: string;
  resolution: string;
}

const CATEGORIES = ['Todos', 'Fútbol', 'Deportes USA', 'Tenis', 'Baloncesto', 'Películas'];

export default function Dashboard() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [filteredChannels, setFilteredChannels] = useState<Channel[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('Todos');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [serverStatus, setServerStatus] = useState('offline');

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    filterChannels();
  }, [selectedCategory, channels]);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/events`);
      
      if (!response.ok) {
        throw new Error('Error al conectar con el servidor');
      }

      const data: Channel[] = await response.json();
      setChannels(data);
      setServerStatus('online');
    } catch (err) {
      setError('No se pudo conectar con el servidor. Verifica que esté ejecutando en puerto 8000.');
      setServerStatus('offline');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterChannels = () => {
    if (selectedCategory === 'Todos') {
      setFilteredChannels(channels);
    } else {
      setFilteredChannels(channels.filter(ch => ch.category === selectedCategory));
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 pt-20 pb-20">
      {/* Hero Banner */}
      <section className="relative overflow-hidden">
        <div className="gradient-hero h-80 flex items-center justify-center relative">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0 bg-gradient-to-r from-neon-blue via-neon-purple to-neon-pink"></div>
          </div>
          
          <div className="relative z-10 text-center px-4">
            <h1 className="text-6xl md:text-7xl font-bold mb-4 bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent">
              🌍 MUNDI TV
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-2">
              Tu plataforma de streaming para ver deportes en vivo
            </p>
            <p className="text-sm md:text-base text-gray-400">
              Fútbol • NFL • ATP • Baloncesto • ¡Y mucho más en HD!
            </p>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Estado del servidor */}
        <div className="mb-8 flex items-center gap-3 justify-center">
          <div className={`w-3 h-3 rounded-full ${serverStatus === 'online' ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-gray-400">
            Servidor {serverStatus === 'online' ? '🟢 Online' : '🔴 Offline'}
          </span>
        </div>

        {/* Filtros por categoría */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6 text-gray-100">Categorías</h2>
          <div className="flex flex-wrap gap-3">
            {CATEGORIES.map(category => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-6 py-2 rounded-full font-bold transition-all duration-300 ${
                  selectedCategory === category
                    ? 'bg-gradient-to-r from-neon-blue to-neon-purple text-dark-950 border-neon-blue shadow-lg shadow-neon-blue/50'
                    : 'bg-dark-800 text-gray-300 border border-dark-700 hover:border-neon-blue/50 hover:text-gray-100'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Mensaje de carga o error */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="text-center">
              <div className="inline-block">
                <div className="w-12 h-12 border-4 border-dark-700 border-t-neon-blue rounded-full animate-spin mb-4"></div>
              </div>
              <p className="text-gray-400">Cargando canales...</p>
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-900/20 border border-red-600/50 rounded-lg p-6 text-center mb-8">
            <p className="text-red-200 mb-4">{error}</p>
            <button
              onClick={fetchEvents}
              className="btn-neon"
            >
              🔄 Reintentar
            </button>
          </div>
        )}

        {/* Grid de canales */}
        {!loading && !error && (
          <>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-100">
                {selectedCategory === 'Todos' ? 'Todos los Eventos' : selectedCategory}
              </h2>
              <p className="text-gray-400 mt-2">
                {filteredChannels.length === 0 
                  ? 'No hay eventos disponibles en esta categoría' 
                  : `${filteredChannels.length} canales disponibles`}
              </p>
            </div>

            {filteredChannels.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredChannels.map(channel => (
                  <ChannelCard key={channel.id} channel={channel} />
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <p className="text-gray-400 text-lg">No hay eventos en esta categoría</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
