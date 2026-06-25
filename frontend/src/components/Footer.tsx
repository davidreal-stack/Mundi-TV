'use client';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-dark-900 border-t border-dark-700/50 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Footer Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Branding */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="text-3xl">🌍</div>
              <h3 className="text-xl font-bold bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent">
                MUNDI TV
              </h3>
            </div>
            <p className="text-gray-400 text-sm">
              La plataforma de streaming más segura para ver deportes en vivo con tokens JWT.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-white font-bold mb-4">Navegación</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-gray-400 hover:text-neon-blue transition-colors text-sm">
                  Inicio
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-neon-blue transition-colors text-sm">
                  Canales
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-neon-blue transition-colors text-sm">
                  Soporte
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-white font-bold mb-4">Legal</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-gray-400 hover:text-neon-blue transition-colors text-sm">
                  Privacidad
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-neon-blue transition-colors text-sm">
                  Términos de Servicio
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-neon-blue transition-colors text-sm">
                  Cookies
                </a>
              </li>
            </ul>
          </div>

          {/* Tech Stack */}
          <div>
            <h4 className="text-white font-bold mb-4">Tecnología</h4>
            <div className="space-y-2 text-sm text-gray-400">
              <p>🐍 Backend: Python & FastAPI</p>
              <p>⚛️ Frontend: Next.js 14</p>
              <p>🔐 Seguridad: JWT Tokens</p>
              <p>🎬 Video: HLS Streaming</p>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="h-[1px] bg-gradient-to-r from-transparent via-dark-700 to-transparent my-8"></div>

        {/* Bottom Footer */}
        <div className="flex flex-col md:flex-row items-center justify-between">
          <p className="text-gray-500 text-sm text-center md:text-left">
            © {currentYear} Mundi TV. Todos los derechos reservados.
          </p>

          {/* Social Links */}
          <div className="flex gap-4 mt-4 md:mt-0">
            <a
              href="#"
              className="text-gray-400 hover:text-neon-blue transition-colors"
              title="GitHub"
            >
              🐙
            </a>
            <a
              href="#"
              className="text-gray-400 hover:text-neon-blue transition-colors"
              title="Twitter"
            >
              𝕏
            </a>
            <a
              href="#"
              className="text-gray-400 hover:text-neon-blue transition-colors"
              title="Discord"
            >
              💬
            </a>
          </div>
        </div>

        {/* Status Bar */}
        <div className="mt-8 pt-8 border-t border-dark-700/50 text-center">
          <p className="text-xs text-gray-600">
            Versión 1.0.0 • Estado: 🟢 Operacional • Ultima actualización: {new Date().toLocaleDateString('es-ES')}
          </p>
        </div>
      </div>
    </footer>
  );
}
