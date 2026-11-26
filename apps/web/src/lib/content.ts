import { getCollection, type CollectionEntry, type CollectionKey } from "astro:content";
import { withBase } from "@/lib/urls";

export type RoutedCollectionKey = Extract<
  CollectionKey,
  "projects" | "notes" | "research" | "archive"
>;

export type RoutedEntry = CollectionEntry<RoutedCollectionKey>;
const naturalTitleCollator = new Intl.Collator(["ko", "en"], {
  numeric: true,
  sensitivity: "base"
});

export function isPublishedEntry(entry: RoutedEntry) {
  return !entry.data.draft;
}

export async function getPublishedCollectionEntries(collection: RoutedCollectionKey) {
  const entries = (await getCollection(collection)) as RoutedEntry[];
  return entries.filter(isPublishedEntry).sort(byDateDesc);
}

export function byTitleAsc(a: RoutedEntry, b: RoutedEntry) {
  const titleOrder = naturalTitleCollator.compare(a.data.title, b.data.title);
  if (titleOrder !== 0) return titleOrder;

  return naturalTitleCollator.compare(a.slug, b.slug);
}

function byTitleDesc(a: RoutedEntry, b: RoutedEntry) {
  return byTitleAsc(b, a);
}

export function byDateAsc(a: RoutedEntry, b: RoutedEntry) {
  const dateOrder = a.data.date.valueOf() - b.data.date.valueOf();
  if (dateOrder !== 0) return dateOrder;

  return byTitleAsc(a, b);
}

export function byDateDesc(a: RoutedEntry, b: RoutedEntry) {
  const dateOrder = b.data.date.valueOf() - a.data.date.valueOf();
  if (dateOrder !== 0) return dateOrder;

  return byTitleDesc(a, b);
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
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  return `${year}.${month}.${day}`;
}

const monthNames = [
  "January", "February", "March", "April", "May", "June", "July",
  "August", "September", "October", "November", "December"
];

export function formatMonth(date: Date) {
  return `${monthNames[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
}

/** Normalize display only; never invent months or days for a year-level period. */
export function formatDisplayPeriod(period: string) {
  const parts = period.trim().split(/\s*[–—]\s*|\s+-\s+/);
  if (parts.length > 2) return period;
  const monthPart = /^([A-Za-z]+)(?:\s+(\d{4}))?$/;
  const endYear = parts.length === 2 ? parts[1].match(/\b(\d{4})$/)?.[1] : undefined;
  function expand(value: string, inheritedYear?: string) {
    const match = value.match(monthPart);
    if (!match) return value;
    const name = monthNames.find((m) =>
      m.toLowerCase() === match[1].toLowerCase() ||
      m.slice(0, 3).toLowerCase() === match[1].toLowerCase() ||
      (m === "September" && match[1].toLowerCase() === "sept")
    );
    const year = match[2] ?? inheritedYear;
    return name && year ? `${name} ${year}` : value;
  }
  return parts.map((part, i) => expand(part, i === 0 ? endYear : undefined)).join(" – ");
}

/** Exact reference days belong on article details, not listing cards. */
export function formatProjectWorkDate(entry: CollectionEntry<"projects">) {
  if (entry.data.datePrecision === "day") return formatDate(entry.data.date);
  if (entry.data.datePrecision === "month") return formatMonth(entry.data.date);
  return formatDisplayPeriod(entry.data.period);
}
