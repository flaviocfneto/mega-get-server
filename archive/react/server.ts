import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import { fileURLToPath } from "url";
import { createProxyMiddleware } from "http-proxy-middleware";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_PROXY_TARGET = process.env.API_PROXY_TARGET || "http://127.0.0.1:8080";

async function startServer() {
  const app = express();
  const PORT = Number(process.env.PORT) || 3000;

  app.use(express.json());

  app.use(
    "/api",
    createProxyMiddleware({
      target: API_PROXY_TARGET,
      changeOrigin: true,
      pathRewrite: (path) => `/api${path}`,
    }),
  );

  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Dev server http://localhost:${PORT} (API proxy → ${API_PROXY_TARGET})`);
  });
}

startServer();
