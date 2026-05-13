import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import { siteConfig } from "@/site.config";
import { byDateDesc, getCollectionPath, isPublishedEntry } from "@/lib/content";
import { withBase } from "@/lib/urls";

export async function GET(context) {
  const entries = [
    ...(await getCollection("projects")),
    ...(await getCollection("notes")),
    ...(await getCollection("devops")),
    ...(await getCollection("research")),
    ...(await getCollection("auto-archive"))
  ].filter(isPublishedEntry).sort(byDateDesc);

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: new URL(withBase("/"), context.site ?? "http://localhost:4321").toString(),
    customData: `<language>en</language><lastBuildDate>${new Date().toUTCString()}</lastBuildDate>`,
    items: entries.map((entry) => ({
      title: entry.data.title,
      description: entry.data.description,
      pubDate: entry.data.date,
      link: getCollectionPath(entry).replace(/^\//, "")
    }))
  });
}
