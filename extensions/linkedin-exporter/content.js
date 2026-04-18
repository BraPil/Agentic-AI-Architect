/**
 * AAA LinkedIn Exporter — Content Script
 *
 * Runs on linkedin.com. Listens for messages from the popup:
 *   { action: "scrape" }   → scrapes all visible posts and returns structured JSON
 *   { action: "expand" }   → clicks all "Read more" buttons first, then scrapes
 *   { action: "scroll" }   → scrolls to bottom to load more posts
 */

"use strict";

// ---------------------------------------------------------------------------
// Post selectors — LinkedIn's classes change; try multiple in order
// ---------------------------------------------------------------------------

// Ordered by specificity — FIRST selector with ≥1 match wins (not most matches)
const POST_CONTAINERS = [
  '[data-urn*="activity"]',    // most precise: actual activity posts
  '.feed-shared-update-v2',    // classic feed posts
  '.occludable-update',        // broader wrapper — fallback only
  '.feed-shared-article',
];

const TEXT_SELECTORS = [
  // Structural selectors (derived from observed XPath — most reliable)
  // The activity container's 2nd direct child div holds the post text
  ':scope > div:nth-child(2)',
  ':scope > div:nth-child(2) > div',
  // Named class selectors — current LinkedIn markup
  '.update-components-text__text-view',
  '.update-components-text',
  '.feed-shared-update-v2__commentary',
  '.update-components-update-v2__commentary',
  // With dir attribute (older markup)
  '.update-components-text span[dir="ltr"]',
  '.feed-shared-update-v2__description span[dir="ltr"]',
  '.feed-shared-text span[dir="ltr"]',
  // Broader fallbacks
  '[class*="commentary"]',
  '[class*="update-components-text"]',
  '.feed-shared-update-v2__description',
  '.feed-shared-text',
];

const AUTHOR_SELECTORS = [
  '.update-components-actor__name span[aria-hidden="true"]',
  '.feed-shared-actor__name span[aria-hidden="true"]',
  '.update-components-actor__name',
  '.feed-shared-actor__name',
];

const AUTHOR_URL_SELECTORS = [
  '.update-components-actor__container-link',
  '.feed-shared-actor__container-link',
  '.update-components-actor__meta-link',
];

const TIMESTAMP_SELECTORS = [
  '.update-components-actor__sub-description span[aria-hidden="true"]',
  '.feed-shared-actor__sub-description span[aria-hidden="true"]',
  '.update-components-actor__sub-description',
];

const IMAGE_SELECTORS = [
  // Structural (3rd direct child of activity container holds media)
  ':scope > div:nth-child(3) img',
  ':scope > div:nth-child(3) [data-delayed-url]',
  // Named class selectors
  '.update-components-image__image',
  '.feed-shared-image__image',
  'img[data-delayed-url]',
  '.feed-shared-linkedin-video__thumbnail',
  '.update-components-image img',
  '.feed-shared-article__image',
];

const READ_MORE_SELECTORS = [
  // Current LinkedIn markup
  '.see-more-less-html__button',          // reactions/feed pages
  '.see-more-less-text__button',
  '.feed-shared-inline-show-more-text__see-more-less-toggle',
  'button.inline-show-more-text__button',
  // Structural: "see more" button is inside div[2] of the activity container
  ':scope > div:nth-child(2) button',
  // Attribute fallbacks
  'button[aria-label*="more"]',
  'button[aria-label*="see"]',
  '.see-more',
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function firstText(el, selectors) {
  for (const sel of selectors) {
    try {
      const found = el.querySelector(sel);
      if (found) {
        const t = (found.innerText || found.textContent || "").trim();
        if (t.length > 20) return t;
      }
    } catch (_) {}
  }
  return "";
}

// Walk the single-child chain from el until we reach a node with multiple children.
// LinkedIn wraps post content in a deep single-child tunnel before forking into
// header / text / media siblings. Returns the fork node, or el if none found.
function findForkNode(el, maxDepth = 15) {
  let node = el;
  for (let i = 0; i < maxDepth; i++) {
    if (node.children.length !== 1) return node;
    node = node.children[0];
  }
  return node;
}

// Extract post text using the fork-node pattern:
// fork.children[0] = header (author, timestamp, controls)
// fork.children[1] = text body  ← we want this
// fork.children[2] = media (images, video)
function extractPostText(el) {
  // Try class-based selectors first (fast path)
  const fromSelectors = firstText(el, TEXT_SELECTORS);
  if (fromSelectors) return fromSelectors;

  // Traverse the single-child tunnel to the fork
  const fork = findForkNode(el);
  if (fork.children.length >= 2) {
    const textArea = fork.children[1];
    const t = (textArea.innerText || textArea.textContent || "").trim();
    if (t.length > 20) return t;
  }

  // Final fallback: full innerText, drop short UI chrome lines
  const raw = el.innerText || el.textContent || "";
  const lines = raw.split("\n").map(l => l.trim()).filter(l => l.length > 30);
  return lines.join("\n").slice(0, 8000);
}

// Extract images using the fork-node pattern:
// fork.children[2] = media section
function extractImagesFromFork(el) {
  const fork = findForkNode(el);
  if (fork.children.length >= 3) {
    const mediaArea = fork.children[2];
    const imgs = extractImages(mediaArea);
    if (imgs.length) return imgs;
  }
  return extractImages(el);
}

function firstAttr(el, selectors, attr) {
  for (const sel of selectors) {
    const found = el.querySelector(sel);
    if (found && found.getAttribute(attr)) {
      return found.getAttribute(attr);
    }
  }
  return "";
}

function extractImages(el) {
  const images = [];
  const seen = new Set();
  for (const sel of IMAGE_SELECTORS) {
    el.querySelectorAll(sel).forEach(img => {
      const src =
        img.getAttribute("data-delayed-url") ||
        img.getAttribute("src") ||
        img.src ||
        "";
      // Skip tiny icons (< 50px), gifs, tracking pixels
      if (!src || seen.has(src)) return;
      if (src.includes("data:") && src.length < 200) return;
      if (src.includes("ghost") || src.includes("icon") || src.includes("emoji")) return;
      const w = img.naturalWidth || img.width || 0;
      const h = img.naturalHeight || img.height || 0;
      if (w > 0 && w < 50) return;
      if (h > 0 && h < 50) return;
      seen.add(src);
      images.push({
        src,
        alt: img.alt || "",
        width: w,
        height: h,
      });
    });
  }
  return images;
}

function extractPostUrl(el) {
  // Try data-urn → construct feed URL
  const urn = el.getAttribute("data-urn") || el.closest("[data-urn]")?.getAttribute("data-urn") || "";
  if (urn) {
    const activityMatch = urn.match(/activity:(\d+)/);
    if (activityMatch) {
      return `https://www.linkedin.com/feed/update/urn:li:activity:${activityMatch[1]}/`;
    }
  }
  // Try permalink elements
  const permalink = el.querySelector('[data-control-name="actor_container"] a, a[href*="/posts/"], a[href*="/feed/update/"]');
  if (permalink) return permalink.href;
  // Structural fallback: header is div[1], controls are in header's div[2]
  // The "Copy link to post" button stores the urn in a nearby data attribute
  const headerControls = el.querySelector(':scope > div:nth-child(1)');
  if (headerControls) {
    const urnEl = headerControls.closest('[data-urn]');
    if (urnEl) {
      const m = urnEl.getAttribute("data-urn")?.match(/activity:(\d+)/);
      if (m) return `https://www.linkedin.com/feed/update/urn:li:activity:${m[1]}/`;
    }
  }
  return "";
}

function extractArticleUrl(el) {
  const article = el.querySelector('a[href*="linkedin.com/pulse"], a[href*="articles"]');
  return article ? article.href : "";
}

function detectPostType(el) {
  if (el.querySelector(".update-components-image, .feed-shared-image")) return "image";
  if (el.querySelector(".update-components-linkedin-video, .feed-shared-linkedin-video")) return "video";
  if (el.querySelector(".feed-shared-article, .update-components-article")) return "article";
  if (el.querySelector(".update-components-document, .feed-shared-document")) return "document";
  return "text";
}

// ---------------------------------------------------------------------------
// Click all "Read more" buttons in an element
// ---------------------------------------------------------------------------

async function expandReadMore(container) {
  const buttons = [...container.querySelectorAll(READ_MORE_SELECTORS.join(", "))].filter(btn => {
    const label = (btn.innerText || btn.getAttribute("aria-label") || "").toLowerCase();
    return label.includes("more") || label.includes("see") || label.includes("show");
  });
  for (const btn of buttons) {
    try {
      btn.click();
      await sleep(150);
    } catch (_) {}
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Scroll to load more posts
// ---------------------------------------------------------------------------

async function scrollToLoadAll(maxScrolls = 20, delayMs = 1500) {
  let lastHeight = 0;
  let unchanged = 0;
  for (let i = 0; i < maxScrolls; i++) {
    window.scrollTo(0, document.body.scrollHeight);
    await sleep(delayMs);
    const newHeight = document.body.scrollHeight;
    if (newHeight === lastHeight) {
      unchanged++;
      if (unchanged >= 2) break; // No new content loaded
    } else {
      unchanged = 0;
    }
    lastHeight = newHeight;
  }
  window.scrollTo(0, 0);
}

// ---------------------------------------------------------------------------
// Scrape all posts currently in the DOM
// ---------------------------------------------------------------------------

async function scrapePosts(options = {}) {
  const { expandAll = true } = options;

  // Find post container elements — use FIRST selector with ≥1 match (priority order)
  let containers = [];
  for (const sel of POST_CONTAINERS) {
    const found = [...document.querySelectorAll(sel)];
    if (found.length > 0) {
      containers = found;
      break;
    }
  }

  // De-duplicate (nested selectors can match parent + child)
  const unique = [];
  const seenUrns = new Set();
  for (const el of containers) {
    const urn = el.getAttribute("data-urn") || "";
    const postUrl = extractPostUrl(el);
    const key = urn || postUrl || el.innerHTML.substring(0, 100);
    if (!seenUrns.has(key)) {
      seenUrns.add(key);
      unique.push(el);
    }
  }

  if (expandAll) {
    for (const el of unique) {
      await expandReadMore(el);
    }
    await sleep(300);
  }

  console.log(`[AAA] scrapePosts: ${unique.length} containers`);

  const posts = [];
  for (const el of unique) {
    const text = extractPostText(el);
    const images = extractImagesFromFork(el);
    console.log(`[AAA] container text=${text.length}chars images=${images.length}`);
    if (!text && !images.length) continue; // Skip empty containers

    const author = firstText(el, AUTHOR_SELECTORS);
    const authorUrl = firstAttr(el, AUTHOR_URL_SELECTORS, "href");
    const timestamp = firstText(el, TIMESTAMP_SELECTORS);
    const postUrl = extractPostUrl(el);
    const articleUrl = extractArticleUrl(el);
    const postType = detectPostType(el);

    // Extract all link URLs from post text (external references)
    const links = [...el.querySelectorAll("a[href]")]
      .map(a => a.href)
      .filter(h => h && !h.includes("linkedin.com") && !h.startsWith("javascript"));

    posts.push({
      post_url: postUrl || articleUrl,
      author,
      author_url: authorUrl ? `https://www.linkedin.com${authorUrl}` : "",
      timestamp,
      post_type: postType,
      text,
      images,
      external_links: [...new Set(links)],
      article_url: articleUrl,
    });
  }

  return posts;
}

// ---------------------------------------------------------------------------
// Message listener (popup → content script)
// ---------------------------------------------------------------------------

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "ping") {
    sendResponse({ ok: true, url: window.location.href, version: AAA_CONTENT_VERSION });
    return true;
  }

  if (message.action === "scroll") {
    scrollToLoadAll(message.maxScrolls || 15, message.delay || 1500).then(() => {
      sendResponse({ ok: true, message: "Scrolling complete" });
    });
    return true;
  }

  if (message.action === "scrape") {
    scrapePosts({ expandAll: message.expandAll !== false }).then(posts => {
      sendResponse({
        ok: true,
        posts,
        page_url: window.location.href,
        scraped_at: new Date().toISOString(),
        count: posts.length,
      });
    }).catch(err => {
      sendResponse({ ok: false, error: err.message });
    });
    return true;
  }

  if (message.action === "scroll_then_scrape") {
    (async () => {
      await scrollToLoadAll(message.maxScrolls || 15, message.delay || 1500);
      const posts = await scrapePosts({ expandAll: true });
      sendResponse({
        ok: true,
        posts,
        page_url: window.location.href,
        scraped_at: new Date().toISOString(),
        count: posts.length,
      });
    })().catch(err => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  return false;
});

const AAA_CONTENT_VERSION = "3";
console.log("[AAA LinkedIn Exporter] Content script v" + AAA_CONTENT_VERSION + " loaded on", window.location.href);
