'use client';

import { useState, useEffect } from 'react';
import ChannelCard from '@/components/ChannelCard';
import { API_CONFIG, fetchAPI } from '@/lib/api'; // Añadí fetchAPI para aprovechar tu utilidad

interface Channel {
  id: number;
  title: string;
  time: string;
  category: string;
  status: string;
  link: string;
  resolution: string;
}

// Nueva interfaz para aguantar la orden del backend
interface EventsResponse {
  total: number;
  paises: Record<string, Channel[]>;
  categorias: Record<string, Channel[]>;
}

type ViewMode = 'categorias' | 'paises';

export default function Dashboard() {
  const [eventsData, setEventsData] = useState<EventsResponse | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('categorias');
  const [selectedGroup, setSelectedGroup] = useState<string>('Todos');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [serverStatus, setServerStatus] = useState('offline');

  useEffect(() => {
    fetchEvents();
  }, []);

  // Si cambiamos de vista (Paises <-> Categorias), regresamos al tab de "Todos" por defecto
  useEffect(() => {
    setSelectedGroup('Todos');
  }, [viewMode]);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);

      // ¡Usando tu propio helper de api.ts!
      const data = await fetchAPI<EventsResponse>('EVENTS');

      setEventsData(data);
      setServerStatus('online');
    } catch (err) {
      setError('No se pudo conectar con el servidor. Verifica que esté ejecutando en puerto 8000.');
      setServerStatus('offline');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Función para resolver qué canales renderizar
  const getDisplayChannels = (): Channel[] => {
    if (!eventsData) return [];

    if (selectedGroup === 'Todos') {
      // Extraemos todos los canales de la vista actual y filtramos duplicados por ID
      const allChannels = Object.values(eventsData[viewMode]).flat();
      const uniqueChannels = Array.from(new Map(allChannels.map(item => [item.id, item])).values());
      return uniqueChannels;
    }

    // Retorna los canales del grupo específico (ej. "mx" o "Deportes")
    return eventsData[viewMode][selectedGroup] || [];
  };

  const displayChannels = getDisplayChannels();

  // Extraemos las llaves del JSON dinámicamente para pintar los botones
  const availableGroups = eventsData ? ['Todos', ...Object.keys(eventsData[viewMode])] : [];

  return (
    <div className="min-h-screen bg-dark-950 pt-20 pb-20">
      {/* Hero Banner (Sin cambios, pura belleza neón) */}
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

        {/* Controles maestros: ¿Qué queremos ver? */}
        <div className="mb-8 flex justify-center gap-4">
          <button
            onClick={() => setViewMode('categorias')}
            className={`px-8 py-3 rounded-xl font-bold transition-all duration-300 ${viewMode === 'categorias'
                ? 'bg-dark-800 text-neon-blue border border-neon-blue shadow-[0_0_15px_rgba(0,255,255,0.3)]'
                : 'bg-dark-900 text-gray-500 border border-dark-700 hover:text-gray-300'
              }`}
          >
            🗂️ Por Categoría
          </button>
          <button
            onClick={() => setViewMode('paises')}
            className={`px-8 py-3 rounded-xl font-bold transition-all duration-300 ${viewMode === 'paises'
                ? 'bg-dark-800 text-neon-purple border border-neon-purple shadow-[0_0_15px_rgba(157,78,221,0.3)]'
                : 'bg-dark-900 text-gray-500 border border-dark-700 hover:text-gray-300'
              }`}
          >
            🌎 Por País
          </button>
        </div>

        {/* Filtros dinámicos */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6 text-gray-100">
            Filtros
          </h2>
          <div className="flex flex-wrap gap-3">
            {availableGroups.map(group => (
              <button
                key={group}
                onClick={() => setSelectedGroup(group)}
                className={`px-6 py-2 rounded-full font-bold transition-all duration-300 ${selectedGroup === group
                    ? 'bg-gradient-to-r from-neon-blue to-neon-purple text-dark-950 border-neon-blue shadow-lg shadow-neon-blue/50'
                    : 'bg-dark-800 text-gray-300 border border-dark-700 hover:border-neon-blue/50 hover:text-gray-100'
                  }`}
              >
                {group === 'Todos' ? group : group.toUpperCase()}
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
              className="px-6 py-2 rounded-full font-bold bg-dark-800 text-gray-300 border border-dark-700 hover:border-neon-blue hover:text-white transition-all"
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
                {selectedGroup === 'Todos' ? 'Todos los Eventos' : selectedGroup.toUpperCase()}
              </h2>
              <p className="text-gray-400 mt-2">
                {displayChannels.length === 0
                  ? 'No hay eventos disponibles en esta selección'
                  : `${displayChannels.length} canales disponibles`}
              </p>
            </div>

            {displayChannels.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {displayChannels.map(channel => (
                  <ChannelCard key={channel.id} channel={channel} />
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <p className="text-gray-400 text-lg">No hay eventos para mostrar</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}