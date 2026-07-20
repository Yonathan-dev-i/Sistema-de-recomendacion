/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Fase 9f (performance y despliegue):
  // - `output: "standalone"` genera en `.next/standalone` un servidor Node
  //   autocontenido con solo las dependencias realmente usadas en runtime,
  //   en vez de copiar todo `node_modules` a la imagen de producción. Es lo
  //   que consume el `frontend/Dockerfile` para tener una imagen liviana.
  // - `poweredByHeader: false` quita el header `X-Powered-By: Next.js`.
  // - `compress: true` habilita compresión gzip de las respuestas del
  //   servidor Node de Next en producción.
  // - `optimizePackageImports` evita que Next incluya el barrel completo
  //   de `lucide-react` (cientos de íconos) cuando solo se importan unos
  //   pocos por archivo; reduce el JS de cliente enviado por página.
  output: "standalone",
  poweredByHeader: false,
  compress: true,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

export default nextConfig;
