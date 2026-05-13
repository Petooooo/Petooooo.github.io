import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwind from "@astrojs/tailwind";
import { defineConfig } from "astro/config";

const siteUrl = new URL(process.env.SITE_URL || "http://localhost:4321");
const base = process.env.BASE_PATH ?? (siteUrl.pathname === "/" ? "/" : siteUrl.pathname.replace(/\/$/, ""));

export default defineConfig({
  site: siteUrl.origin,
  base,
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
