import type { CollectionEntry, CollectionKey } from "astro:content";
import { withBase } from "@/lib/urls";

type RoutedCollectionKey = Extract<
  CollectionKey,
  "projects" | "notes" | "devops" | "research" | "paper-reviews" | "archive"
>;

type Entry = CollectionEntry<RoutedCollectionKey>;

export function isPublishedEntry(entry: Entry) {
  return !entry.data.draft;
}

export function byDateDesc(a: Entry, b: Entry) {
  return b.data.date.valueOf() - a.data.date.valueOf();
}

export function getCollectionUrl(entry: Entry) {
  return withBase(`/${entry.collection}/${entry.slug}/`);
}

export function getCollectionPath(entry: Entry) {
  return `/${entry.collection}/${entry.slug}/`;
}

export function normalizeTags(tags: string[] = []) {
  return tags.map((tag) => tag.trim()).filter(Boolean);
}

export function formatDate(date: Date) {
  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric"
  }).format(date);
}
