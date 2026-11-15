import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwind from "@astrojs/tailwind";
import { defineConfig } from "astro/config";

const siteUrl = new URL(process.env.SITE_URL || "http://localhost:4321");
export default defineConfig({
  site: siteUrl.origin,
  redirects: {
    "/projects/kdt-linux-system-kernel-expert-course/": "/notes/study-kdt-overview/",
    "/projects/kdt-posix-system-programming/": "/notes/study-kdt-posix/",
    "/projects/kdt-kernel-tracing-vfs-memory/": "/notes/study-kdt-kernel-vfs-memory/",
    "/projects/kdt-embedded-linux-drivers/": "/notes/study-kdt-embedded-linux/",
    "/projects/kdt-crash-dump-analysis-progress/": "/notes/study-kdt-crash-dump/",
    "/projects/kdt-ebpf-observability-progress/": "/notes/study-kdt-ebpf-observability/"
  },
  integrations: [
    mdx(),
    tailwind({ applyBaseStyles: false }),
    sitemap()
  ],
  markdown: {
    shikiConfig: {
      theme: "github-dark"
    }
  }
});
