'use client';

import { useEffect, useRef, useState } from 'react';

interface UniversalPlayerProps {
  src: string;
  poster?: string;
  title?: string;
  autoplay?: boolean;
  muted?: boolean;
}

/**
 * UniversalPlayer - Reproductor universal para HLS (.m3u8) y MPEG-DASH (.mpd)
 * 
 * Utiliza Shaka Player para soporte multi-formato.
 * Compatible con SSR mediante "use client".
 * 
 * Props:
 * - src: URL del stream (m3u8 o mpd)
 * - poster: URL de la imagen de portada (opcional)
 * - title: Título del contenido (opcional)
 * - autoplay: Autoplay del video (default: false)
 * - muted: Muted por defecto (default: false)
 */
export default function UniversalPlayer({
  src,
  poster,
  title = 'Reproductor de Video',
  autoplay = false,
  muted = false,
}: UniversalPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerRef = useRef<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const initializePlayer = async () => {
      try {
        // Importar dinámicamente shaka-player para evitar problemas SSR
        const shaka = (await import('shaka-player')).default;

        // Verificar que el video element existe
        if (!videoRef.current) {
          throw new Error('Video element no encontrado');
        }

        // Verificar soporte de shaka-player en el navegador
        if (!shaka.Player.isBrowserSupported()) {
          throw new Error(
            'Shaka Player no es soportado en este navegador. Por favor, actualiza tu navegador.'
          );
        }

        // Instalar polyfills necesarios para compatibilidad
        console.log('📦 Instalando polyfills de Shaka Player...');
        shaka.polyfill.installAll();

        // Crear instancia del reproductor
        if (!isMounted) return;

        const player = new shaka.Player(videoRef.current);
        playerRef.current = player;

        console.log('🎬 Inicializando Shaka Player...');

        // Configurar listeners de eventos
        player.addEventListener('error', (event: any) => {
          const error = event.detail;
          const errorMessage = `${error.code}: ${error.message}`;
          console.error('❌ Error en Shaka Player:', errorMessage);
          setError(`Error de reproducción: ${error.message}`);
        });

        player.addEventListener('adaptation', () => {
          console.log('📊 Calidad ajustada automáticamente');
        });

        player.addEventListener('streaming', () => {
          console.log('✅ Streaming iniciado');
        });

        // Configurar el video en el reproductor
        console.log(`🔗 Cargando stream: ${src}`);
        await player.load(src);

        if (isMounted) {
          setIsInitialized(true);
          setLoading(false);
          setError(null);
          console.log('✨ Reproductor inicializado correctamente');
        }

        // Reproducir automáticamente si está configurado
        if (autoplay && videoRef.current) {
          // Intentar autoplay con sonido, fallback a muted si falla
          try {
            videoRef.current.play();
          } catch (e) {
            console.warn(
              '⚠️ Autoplay con sonido falló. Intentando con muted...'
            );
            videoRef.current.muted = true;
            videoRef.current.play();
          }
        }
      } catch (err) {
        if (isMounted) {
          const errorMessage =
            err instanceof Error ? err.message : 'Error desconocido';
          console.error('🔴 Error inicializando reproductor:', errorMessage);
          setError(errorMessage);
          setLoading(false);
        }
      }
    };

    initializePlayer();

    // Cleanup
    return () => {
      isMounted = false;

      // Destruir el reproductor para evitar fugas de memoria
      if (playerRef.current) {
        console.log('🧹 Limpiando Shaka Player...');
        playerRef.current
          .destroy()
          .catch((err: any) => {
            console.warn('⚠️ Error al destruir reproductor:', err);
          });
        playerRef.current = null;
      }

      // Pausar y resetear video
      if (videoRef.current) {
        videoRef.current.pause();
        videoRef.current.currentTime = 0;
      }
    };
  }, [src, autoplay]);

  /**
   * Cambiar la fuente del stream dinámicamente
   */
  const changeSource = async (newSrc: string) => {
    if (!playerRef.current) {
      console.error('❌ Reproductor no inicializado');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      console.log(`🔄 Cambiando stream a: ${newSrc}`);
      await playerRef.current.load(newSrc);
      setLoading(false);
      console.log('✅ Stream cambiado correctamente');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      console.error('❌ Error cambiando stream:', errorMessage);
      setError(errorMessage);
      setLoading(false);
    }
  };

  /**
   * Obtener información del reproductor
   */
  const getPlayerInfo = () => {
    if (!playerRef.current) {
      return null;
    }

    return {
      duration: videoRef.current?.duration || 0,
      currentTime: videoRef.current?.currentTime || 0,
      isPlaying: videoRef.current ? !videoRef.current.paused : false,
      volume: videoRef.current?.volume || 1,
      buffered: videoRef.current?.buffered || null,
    };
  };

  return (
    <div className="w-full bg-black rounded-lg overflow-hidden shadow-2xl">
      {/* Video Element */}
      <div className="relative w-full pt-[56.25%] bg-black">
        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full"
          poster={poster}
          controls
          autoPlay={autoplay}
          muted={muted}
          crossOrigin="anonymous"
          playsInline
        />

        {/* Loading Spinner */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
            <div className="flex flex-col items-center gap-3">
              <div className="animate-spin">
                <div className="w-12 h-12 border-4 border-neon-blue border-t-transparent rounded-full"></div>
              </div>
              <p className="text-neon-blue text-sm font-medium">
                Cargando stream...
              </p>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75">
            <div className="bg-dark-900 border border-red-500 rounded-lg p-4 max-w-sm">
              <p className="text-red-400 font-semibold mb-2">⚠️ Error</p>
              <p className="text-gray-300 text-sm mb-4">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded transition-colors"
              >
                Reintentar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Info Bar */}
      <div className="bg-dark-800 px-4 py-3 flex justify-between items-center">
        <div>
          <h3 className="text-white font-semibold truncate">{title}</h3>
          <p className="text-gray-400 text-xs truncate">{src}</p>
        </div>
        <div className="flex items-center gap-2">
          {isInitialized && (
            <span className="inline-flex items-center gap-1 bg-neon-green bg-opacity-20 text-neon-green px-3 py-1 rounded-full text-xs font-medium">
              <span className="w-2 h-2 bg-neon-green rounded-full animate-pulse"></span>
              En vivo
            </span>
          )}
        </div>
      </div>

      {/* Debug Info (Development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="bg-dark-900 px-4 py-2 text-xs text-gray-400 border-t border-dark-700">
          <p>🔗 Fuente: {src}</p>
          <p>📊 Estado: {isInitialized ? '✅ Listo' : '⏳ Inicializando'}</p>
          {error && <p className="text-red-400">⚠️ {error}</p>}
        </div>
      )}
    </div>
  );
}
