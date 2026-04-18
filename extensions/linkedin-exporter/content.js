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

// Fallback container selectors for non-reactions pages (feed, profile, etc.)
const POST_CONTAINERS = [
  '[data-urn*="activity"]',
  '.feed-shared-update-v2',
  '.occludable-update',
  '.feed-shared-article',
];

// Find the reactions list <ul> by locating whichever <ul> in main has the most
// direct <li> children that contain a [data-urn*="activity"] descendant.
// This survives LinkedIn injecting "suggested posts" sections elsewhere in the DOM.
function findPostContainers() {
  const diagLog = [];

  // ── Step 1: probe all [data-urn*="activity"] on the page ──────────────────
  const allActivity = [...document.querySelectorAll('[data-urn*="activity"]')];
  diagLog.push(`probe: ${allActivity.length} [data-urn*=activity] on page`);
  if (allActivity.length > 0) {
    // Log parent tag chain for the first 3 so we know the structure
    allActivity.slice(0, 3).forEach((el, i) => {
      const chain = [];
      let n = el;
      for (let d = 0; d < 6 && n; d++) { chain.push(n.tagName); n = n.parentElement; }
      diagLog.push(`  activity[${i}] chain: ${chain.join("←")} urn=${el.getAttribute("data-urn")?.slice(-12)}`);
    });
  }

  // ── Step 2: score every <ul> in <main> ────────────────────────────────────
  const uls = [...document.querySelectorAll("main ul")];
  diagLog.push(`probe: ${uls.length} <ul> in <main>`);
  let bestUl = null, bestScore = 0;
  for (const ul of uls) {
    const liCount = [...ul.children].filter(
      li => li.tagName === "LI" && li.querySelector('[data-urn*="activity"]')
    ).length;
    if (liCount > 0) diagLog.push(`  ul liCount=${liCount} cls=${ul.className.slice(0,40)}`);
    if (liCount > bestScore) { bestScore = liCount; bestUl = ul; }
  }

  if (bestUl && bestScore >= 1) {
    const items = [...bestUl.children].filter(li => li.tagName === "LI");
    diagLog.push(`winner: ul with ${bestScore} activity-li → ${items.length} LI items`);
    return { containers: items, log: diagLog.join(" | ") };
  }

  // ── Step 3: try <div> containers (LinkedIn sometimes skips <ul>) ───────────
  const divActivity = [...document.querySelectorAll(
    'main div[data-urn*="activity"], main > div [data-urn*="activity"]'
  )];
  diagLog.push(`probe: ${divActivity.length} div[data-urn*=activity] in main`);
  if (divActivity.length > 0) {
    diagLog.push(`fallback: using ${divActivity.length} div activity containers`);
    return { containers: divActivity, log: diagLog.join(" | ") };
  }

  // ── Step 4: last-resort named class selectors ──────────────────────────────
  for (const sel of POST_CONTAINERS) {
    const found = [...document.querySelectorAll(sel)];
    if (found.length > 0) {
      diagLog.push(`fallback-sel:${sel} → ${found.length}`);
      return { containers: found, log: diagLog.join(" | ") };
    }
  }

  diagLog.push("FAILED: no containers found");
  return { containers: [], log: diagLog.join(" | ") };
}

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
  // Current markup
  '.update-components-actor__name span[aria-hidden="true"]',
  '.update-components-actor__name span',
  '.update-components-actor__name',
  // Older markup
  '.feed-shared-actor__name span[aria-hidden="true"]',
  '.feed-shared-actor__name span',
  '.feed-shared-actor__name',
  // Broader: any actor title/name text
  '[class*="actor__name"] span[aria-hidden="true"]',
  '[class*="actor__name"] span',
  '[class*="actor__name"]',
  '[class*="actor__title"] span[aria-hidden="true"]',
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
    if (found) {
      // Use .href for href attrs — gives absolute URL, no relative/absolute confusion
      const val = attr === "href" ? (found.href || found.getAttribute(attr)) : found.getAttribute(attr);
      if (val) return val;
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
// Scroll-only (no scraping) — used by the standalone Scroll button
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
      if (unchanged >= 2) break;
    } else {
      unchanged = 0;
    }
    lastHeight = newHeight;
  }
  window.scrollTo(0, 0);
}

// Rolling scrape — scrape visible posts at each scroll step before LinkedIn
// occludes them. LinkedIn's virtual DOM removes off-screen posts so scraping
// only at the end misses everything above the current viewport.
// ---------------------------------------------------------------------------

async function scrollAndScrapeRolling(maxScrolls = 20, delayMs = 1500,
                                      expandAll = true, maxPosts = 0) {
  const accumulated = new Map(); // key → post object (dedup by post_url or text prefix)
  const runLog = [];

  async function scrapeAndAccumulate(label) {
    const { posts } = await scrapePosts({ expandAll });
    let added = 0;
    for (const p of posts) {
      const key = p.post_url || p.text.slice(0, 80);
      if (key && !accumulated.has(key)) {
        accumulated.set(key, p);
        added++;
      }
    }
    runLog.push(`${label}: +${added} new (total ${accumulated.size})`);
    return added;
  }

  // Capture initial viewport
  await scrapeAndAccumulate("initial");

  let lastHeight = 0;
  let unchanged = 0;

  for (let i = 0; i < maxScrolls; i++) {
    if (maxPosts > 0 && accumulated.size >= maxPosts) break;

    window.scrollTo(0, document.body.scrollHeight);
    await sleep(delayMs);

    const newHeight = document.body.scrollHeight;
    if (newHeight === lastHeight) {
      unchanged++;
      if (unchanged >= 2) { runLog.push("scroll: no new content, stopping"); break; }
    } else {
      unchanged = 0;
    }
    lastHeight = newHeight;

    await scrapeAndAccumulate(`scroll ${i + 1}`);
  }

  window.scrollTo(0, 0);
  const posts = [...accumulated.values()];
  runLog.push(`result: ${posts.length} total posts collected`);
  return { posts, log: runLog };
}

// ---------------------------------------------------------------------------
// Scrape all posts currently in the DOM
// ---------------------------------------------------------------------------

async function scrapePosts(options = {}) {
  const { expandAll = true } = options;

  const { containers, log: containerLog } = findPostContainers();

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

  const runLog = [];
  runLog.push(`containers: ${containerLog}`);
  runLog.push(`dedup: ${containers.length} found → ${unique.length} unique`);

  const posts = [];
  for (let idx = 0; idx < unique.length; idx++) {
    const el = unique[idx];
    // When containers are <li> elements, content lives inside the activity div.
    // Resolve it so findForkNode starts at the right depth.
    const contentEl = el.querySelector('[data-urn*="activity"]') || el;
    const urn = contentEl.getAttribute("data-urn") || el.getAttribute("data-urn") || `idx-${idx}`;

    // Text extraction — all operations on contentEl (activity div), not li
    let text = "", textVia = "none";
    const fromSel = firstText(contentEl, TEXT_SELECTORS);
    if (fromSel) {
      text = fromSel; textVia = "selector";
    } else {
      const fork = findForkNode(contentEl);
      const forkDepth = (() => { let n = contentEl, d = 0; while (n !== fork) { n = n.children[0]; d++; } return d; })();
      runLog.push(`[${idx}] urn=${urn.slice(-12)} fork_depth=${forkDepth} fork_children=${fork.children.length}`);
      if (fork.children.length >= 2) {
        const t = (fork.children[1].innerText || fork.children[1].textContent || "").trim();
        if (t.length > 20) { text = t; textVia = "fork.children[1]"; }
      }
      if (!text) {
        const raw = (contentEl.innerText || contentEl.textContent || "");
        const lines = raw.split("\n").map(l => l.trim()).filter(l => l.length > 30);
        if (lines.length) { text = lines.join("\n").slice(0, 8000); textVia = `innerText(${lines.length}lines)`; }
      }
    }

    const images = extractImagesFromFork(contentEl);
    const kept = !!(text || images.length);
    const preview = text.slice(0, 60).replace(/\n/g, " ");
    runLog.push(`[${idx}] text=${text.length}ch(${textVia}) images=${images.length} → ${kept ? "KEPT" : "SKIPPED"}${kept ? ` | "${preview}"` : ""}`);
    if (!kept) continue;

    // Author — must skip reaction attribution line ("Brandt Pileggi likes this")
    const REACTION_VERBS = ["likes", "reacted", "commented", "reshared",
                            "celebrated", "shared", "posted", "follows"];
    let author = firstText(contentEl, AUTHOR_SELECTORS);
    if (!author) {
      // Try author link title attribute or aria-label
      const authorLink = contentEl.querySelector(
        AUTHOR_URL_SELECTORS.join(", ") + ', a[href*="/in/"], a[href*="/company/"]'
      );
      if (authorLink) {
        author = authorLink.title || authorLink.getAttribute("aria-label") || "";
        if (!author) {
          // Read the first short text node inside the link
          const t = (authorLink.innerText || authorLink.textContent || "").trim().split("\n")[0].trim();
          if (t.length > 1 && t.length < 80 && !REACTION_VERBS.some(v => t.toLowerCase().includes(v))) {
            author = t;
          }
        }
      }
    }
    if (!author) {
      const fork = findForkNode(contentEl);
      const headerText = (fork.children[0]?.innerText || "").trim();
      const nameLine = headerText.split("\n")
        .map(l => l.trim())
        .find(l => l.length > 2 && l.length < 80 &&
              !l.includes("•") &&
              !l.match(/^\d/) &&
              !l.toLowerCase().includes("follow") &&
              !REACTION_VERBS.some(v => l.toLowerCase().includes(v)));
      if (nameLine) author = nameLine;
    }

    const authorHref = firstAttr(contentEl, AUTHOR_URL_SELECTORS, "href");
    const authorUrl = authorHref
      ? (authorHref.startsWith("http") ? authorHref : `https://www.linkedin.com${authorHref}`)
      : "";

    const timestamp = firstText(contentEl, TIMESTAMP_SELECTORS);
    runLog.push(`[${idx}] author="${author}" ts="${timestamp}"`);
    const postUrl = extractPostUrl(contentEl);
    const articleUrl = extractArticleUrl(contentEl);
    const postType = detectPostType(contentEl);

    // Extract all link URLs from post text (external references)
    const links = [...el.querySelectorAll("a[href]")]
      .map(a => a.href)
      .filter(h => h && !h.includes("linkedin.com") && !h.startsWith("javascript"));

    posts.push({
      post_url: postUrl || articleUrl,
      author,
      author_url: authorUrl,
      timestamp,
      post_type: postType,
      text,
      images,
      external_links: [...new Set(links)],
      article_url: articleUrl,
    });
  }

  runLog.push(`result: ${posts.length} posts kept of ${unique.length} containers`);
  return { posts, log: runLog };
}

// ---------------------------------------------------------------------------
// Message listener (popup → content script)
// ---------------------------------------------------------------------------

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "ping") {
    sendResponse({ ok: true, url: window.location.href, version: AAA_CONTENT_VERSION });
    return true;
  }

  // Version gate: if the popup sends a required version, ignore mismatches.
  // This prevents stale injected scripts from responding when a newer script
  // has been injected on top of them (both run; only the right one responds).
  if (message.requireVersion && message.requireVersion !== AAA_CONTENT_VERSION) {
    return false;
  }

  if (message.action === "scroll") {
    scrollToLoadAll(message.maxScrolls || 15, message.delay || 1500).then(() => {
      sendResponse({ ok: true, message: "Scrolling complete" });
    });
    return true;
  }

  if (message.action === "scrape") {
    scrapePosts({ expandAll: message.expandAll !== false }).then(({ posts, log }) => {
      sendResponse({
        ok: true, posts, log,
        page_url: window.location.href,
        scraped_at: new Date().toISOString(),
        count: posts.length,
      });
    }).catch(err => {
      sendResponse({ ok: false, error: err.message, log: [`ERROR: ${err.message}`] });
    });
    return true;
  }

  if (message.action === "scroll_then_scrape") {
    (async () => {
      const { posts, log } = await scrollAndScrapeRolling(
        message.maxScrolls || 15,
        message.delay || 1500,
        message.expandAll !== false,
        message.maxPosts || 0,
      );
      sendResponse({
        ok: true, posts, log,
        page_url: window.location.href,
        scraped_at: new Date().toISOString(),
        count: posts.length,
      });
    })().catch(err => sendResponse({ ok: false, error: err.message, log: [`ERROR: ${err.message}`] }));
    return true;
  }

  return false;
});

const AAA_CONTENT_VERSION = "11";
console.log("[AAA LinkedIn Exporter] Content script v" + AAA_CONTENT_VERSION + " loaded on", window.location.href);
