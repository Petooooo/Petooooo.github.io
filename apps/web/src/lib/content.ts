import type { CollectionEntry, CollectionKey } from "astro:content";
import { withBase } from "@/lib/urls";

export type RoutedCollectionKey = Extract<
  CollectionKey,
  "projects" | "notes" | "devops" | "research" | "paper-reviews" | "archive"
>;

export type RoutedEntry = CollectionEntry<RoutedCollectionKey>;
const naturalTitleCollator = new Intl.Collator(["ko", "en"], {
  numeric: true,
  sensitivity: "base"
});

export function isPublishedEntry(entry: RoutedEntry) {
  return !entry.data.draft;
}

export function byDateDesc(a: RoutedEntry, b: RoutedEntry) {
  const dateOrder = b.data.date.valueOf() - a.data.date.valueOf();
  if (dateOrder !== 0) return dateOrder;

  const titleOrder = naturalTitleCollator.compare(a.data.title, b.data.title);
  if (titleOrder !== 0) return titleOrder;

  return naturalTitleCollator.compare(a.slug, b.slug);
}

export function getCollectionUrl(entry: RoutedEntry) {
  return withBase(`/${entry.collection}/${entry.slug}/`);
}

export function getCollectionPath(entry: RoutedEntry) {
  return `/${entry.collection}/${entry.slug}/`;
}

export function normalizeTags(tags: string[] = []) {
  return tags.map((tag) => tag.trim()).filter(Boolean);
}

export function getEntryArea(entry: RoutedEntry) {
  return entry.data.area ?? "Uncategorized";
}

export function getAreaId(area: string) {
  return area.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "uncategorized";
}

export function sortAreas(areas: string[], preferredOrder: readonly string[] = []) {
  return [...areas].sort((a, b) => {
    const aIndex = preferredOrder.indexOf(a);
    const bIndex = preferredOrder.indexOf(b);

    if (aIndex >= 0 && bIndex >= 0) return aIndex - bIndex;
    if (aIndex >= 0) return -1;
    if (bIndex >= 0) return 1;

    return naturalTitleCollator.compare(a, b);
  });
}

export function formatDate(date: Date) {
  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric"
  }).format(date);
}
