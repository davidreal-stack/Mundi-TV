'use client';

import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { API_CONFIG, getStreamManifest } from '@/lib/api';
import UniversalPlayer from '@/components/UniversalPlayer';

export default function ChannelPlayer() {
  const searchParams = useSearchParams();
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<any>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [channelTitle, setChannelTitle] = useState('Reproduciendo...');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isDash, setIsDash] = useState(false);
  const [manifestUrl, setManifestUrl] = useState<string | null>(null);

  /**
   * Obtener el stream URL desde el backend usando el token
   */
  const fetchStreamUrl = async (token: string): Promise<string> => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/get_link?token=${token}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP Error ${response.status}`);
      }

      const data = await response.json();
      if (!data.link) {
        throw new Error('No se recibió URL de stream del servidor');
      }

      return data.link;
    } catch (err) {
      throw new Error(
        err instanceof Error ? err.message : 'Error al obtener el stream'
      );
    }
  };

  /**
   * Inicializar reproductor HLS
   * Carga dinámicamente hls.js dentro del useEffect
   */
  useEffect(() => {
    const initializePlayer = async () => {
      try {
        const token = searchParams.get('token');
        const contentId = searchParams.get('content_id');

        if (!token && !contentId) {
          setError('❌ Canal o token no proporcionado. Selecciona un canal desde el dashboard.');
          setLoading(false);
          return;
        }

        if (contentId) {
          setIsDash(true);
          const formattedTitle = `TV Azteca ${contentId.replace('azteca-', '').toUpperCase()}`;
          setChannelTitle(formattedTitle);
          console.log(`🔗 Obteniendo manifiesto para DASH canal: ${contentId}`);
          try {
            const manifest = await getStreamManifest(contentId);
            setManifestUrl(manifest);
            setLoading(false);
            console.log('✅ Manifiesto DASH recibido:', manifest);
          } catch (err) {
            setError(`Error al cargar el stream de TV Azteca: ${err instanceof Error ? err.message : 'Error de conexión'}`);
            setLoading(false);
          }
          return;
        }

        setIsDash(false);
        // Paso 1: Obtener URL de stream del backend
        console.log('🔗 Obteniendo URL del stream...');
        const streamUrl = await fetchStreamUrl(token);
        console.log('✅ Stream URL recibida');

        // Validar URL
        try {
          new URL(streamUrl);
        } catch {
          throw new Error('URL de stream inválida');
        }

        if (!videoRef.current) {
          throw new Error('Elemento de video no disponible');
        }

        // Paso 2: Cargar hls.js dinámicamente
        console.log('📚 Cargando librería hls.js...');
        const HLS = await import('hls.js').then(mod => mod.default || mod);
        console.log('✅ hls.js cargado correctamente');

        // Paso 3: Verificar soporte
        const isHLSSupported = HLS.isSupported();
        const hasNativeSupport = videoRef.current.canPlayType(
          'application/vnd.apple.mpegurl'
        ) === 'probably';

        console.log('🎬 Información de reproducción:', {
          hlsJs: isHLSSupported,
          nativo: hasNativeSupport,
          navegador: navigator.userAgent.split(' ').slice(-2).join(' ')
        });

        // Paso 4: Configurar reproductor
        if (isHLSSupported && videoRef.current) {
          // Opción 1: Usar hls.js
          const hls = new HLS({
            debug: false,
            enableWorker: true,
            lowLatencyMode: true,
            maxBufferLength: 30,
            maxBufferSize: 60 * 1000 * 1000, // 60MB
          });

          // Listener: Manifest cargado
          hls.on(HLS.Events.MANIFEST_PARSED, () => {
            console.log('✅ Manifest cargado correctamente');
            setLoading(false);
            videoRef.current?.play().catch(err => {
              console.log('ℹ️ Autoplay bloqueado:', err.message);
            });
          });

          // Listener: Error
          hls.on(HLS.Events.ERROR, (event, data) => {
            const errorType = data.type || 'UNKNOWN';
            const errorDetails = data.details || 'Sin detalles';
            const isFatal = data.fatal === true;

            console.error('❌ HLS Error:', {
              type: errorType,
              details: errorDetails,
              fatal: isFatal,
              statusCode: data.response?.code
            });

            if (isFatal) {
              let errorMessage = 'Error fatal en la reproducción';

              if (errorType === 'networkError') {
                errorMessage = '🌐 Error de conexión. Verifica tu internet.';
              } else if (errorType === 'mediaError') {
                errorMessage = '📺 El navegador no puede reproducir este formato.';
              } else if (data.response?.code === 404) {
                errorMessage = '🔍 Stream no encontrado (404).';
              } else if (data.response?.code === 403) {
                errorMessage = '🚫 Acceso denegado (403).';
              } else if (data.response?.code === 401) {
                errorMessage = '🔑 Token expirado o no autorizado (401).';
              } else if (data.response?.code === 500) {
                errorMessage = '⚠️ Error del servidor (500).';
              }

              setError(errorMessage);
              setLoading(false);
            }
          });

          // Listener: Level Switching (cambio de resolución)
          hls.on(HLS.Events.LEVEL_SWITCHED, (event, data) => {
            console.log(`📡 Resolución cambió a: ${data.level}`);
          });

          // Cargar el stream
          hls.loadSource(streamUrl);
          hls.attachMedia(videoRef.current);

          // Guardar referencia
          hlsRef.current = hls;
          setChannelTitle('📺 En Vivo');

          return;
        }

        // Opción 2: Reproducción nativa (Safari, iOS, Android)
        if (hasNativeSupport && videoRef.current) {
          console.log('📱 Usando reproducción HLS nativa del navegador');
          videoRef.current.src = streamUrl;

          const handleLoadedMetadata = () => {
            console.log('✅ Video cargado (soporte nativo)');
            setLoading(false);
            videoRef.current?.play().catch(err => {
              console.log('ℹ️ Autoplay bloqueado:', err.message);
            });
          };

          const handleError = () => {
            console.error('❌ Error cargando stream nativo');
            setError('Error al cargar el stream. Intenta recargando.');
            setLoading(false);
          };

          videoRef.current.addEventListener('loadedmetadata', handleLoadedMetadata);
          videoRef.current.addEventListener('error', handleError);

          return;
        }

        // Sin soporte
        throw new Error(
          '🚫 Tu navegador no soporta HLS.\n' +
          'Intenta con Chrome, Firefox, Safari o Edge.'
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error desconocido';
        console.error('❌ Error inicializando reproductor:', message);
        setError(message);
        setLoading(false);
      }
    };

    initializePlayer();

    // Cleanup: Destruir HLS al desmontar
    return () => {
      console.log('🧹 Limpiando reproductor...');
      
      if (hlsRef.current) {
        try {
          hlsRef.current.destroy();
          console.log('✅ HLS destruido correctamente');
        } catch (err) {
          console.error('⚠️ Error al destruir HLS:', err);
        }
        hlsRef.current = null;
      }

      if (videoRef.current) {
        try {
          videoRef.current.pause();
          videoRef.current.src = '';
          videoRef.current.load();
        } catch (err) {
          console.error('⚠️ Error limpiando video:', err);
        }
      }
    };
  }, [searchParams]);

  /**
   * Activar/desactivar pantalla completa
   */
  const handleFullscreen = () => {
    if (!videoRef.current) return;

    if (!document.fullscreenElement) {
      videoRef.current
        .requestFullscreen()
        .catch(err => console.error('Fullscreen error:', err));
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  /**
   * Cambiar volumen
   */
  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = Math.max(0, Math.min(1, newVolume));
    }
  };

  /**
   * Play/Pause
   */
  const handlePlayPause = () => {
    if (!videoRef.current) return;

    if (videoRef.current.paused) {
      videoRef.current.play().catch(err => {
        console.log('Play error:', err.message);
      });
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 flex flex-col">
      {/* Video Container */}
      <div className="flex-1 flex items-center justify-center bg-black relative group">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-20">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-dark-700 border-t-neon-blue rounded-full animate-spin mb-4 mx-auto"></div>
              <p className="text-white text-lg">Conectando al stream...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/70 z-20">
            <div className="text-center px-6">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-xl font-bold text-red-400 mb-4">Error de Reproducción</h3>
              <p className="text-gray-300 mb-6 whitespace-pre-wrap">{error}</p>
              <Link
                href="/"
                className="btn-neon inline-block"
              >
                ← Volver al Dashboard
              </Link>
            </div>
          </div>
        )}

        {/* Video Player */}
        {isDash ? (
          manifestUrl ? (
            <div className="w-full max-w-5xl mx-auto p-4 flex items-center justify-center">
              <UniversalPlayer src={manifestUrl} title={channelTitle} autoplay={true} />
            </div>
          ) : (
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-dark-700 border-t-neon-blue rounded-full animate-spin mb-4 mx-auto"></div>
              <p className="text-white text-lg">Cargando señal DASH...</p>
            </div>
          )
        ) : (
          <>
            <video
              ref={videoRef}
              className="w-full h-full"
              controls={false}
              autoPlay
              muted={false}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
            />

            {/* Custom Controls - Visible on hover */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/50 to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <div className="flex items-center gap-4 mb-4">
                <button
                  onClick={handlePlayPause}
                  className="text-white hover:text-neon-blue transition-colors"
                >
                  {isPlaying ? '⏸️' : '▶️'}
                </button>

                <div className="flex-1 flex items-center gap-2">
                  <span className="text-xs text-gray-400">🔊</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={volume}
                    onChange={handleVolumeChange}
                    className="flex-1 h-1 bg-gray-700 rounded cursor-pointer"
                  />
                </div>

                <button
                  onClick={handleFullscreen}
                  className="text-white hover:text-neon-blue transition-colors"
                >
                  {isFullscreen ? '⛔ Salir FS' : '🖥️'}
                </button>
              </div>

              <p className="text-xs text-gray-400">
                {channelTitle}
              </p>
            </div>
          </>
        )}
      </div>

      {/* Info & Navigation */}
      <div className="bg-dark-900 border-t border-dark-700 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-100 mb-2">
                🎬 {channelTitle}
              </h1>
              <div className="flex items-center gap-2">
                <span className="badge-live">
                  <span className="pulse-dot"></span>
                  EN VIVO
                </span>
                <span className="text-sm text-gray-400">Calidad: HD</span>
              </div>
            </div>

            <Link
              href="/"
              className="btn-neon flex items-center gap-2"
            >
              ← Dashboard
            </Link>
          </div>

          <div className="mt-6 p-4 bg-dark-800/50 rounded-lg border border-dark-700/50">
            <p className="text-gray-400 text-sm">
              💡 El stream está protegido con tokens JWT. Abre la consola (F12) para ver los logs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
