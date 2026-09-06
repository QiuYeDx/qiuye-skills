import Lenis from "lenis";
import { installNativeScrollHandoff } from "./native-scroll-handoff";

const SCROLL_KEYS = new Set([
  "ArrowUp",
  "ArrowDown",
  "PageUp",
  "PageDown",
  "Home",
  "End",
  " ",
  "Tab",
]);

/** Smooth wheel input on the real document, preserving native scroll coordinates. */
export function createSmoothPageScroll({ nativeScrollInterop = false } = {}) {
  const root = document.documentElement;
  const body = document.body;
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  let lenis: Lenis | null = null;
  let frame = 0;
  let advancing = false;

  const cancelFrame = () => {
    cancelAnimationFrame(frame);
    frame = 0;
  };

  // stop/start resets inertia to actualScroll without issuing a scrollTo call.
  // In particular, don't cancel a native smooth scroll started by another component.
  const release = () => {
    cancelFrame();
    if (lenis?.isScrolling === "smooth") {
      lenis.stop();
      lenis.start();
    }
  };

  const tick = (time: number) => {
    frame = 0;
    if (!lenis) return;
    // An external scrollTo, scrollIntoView, focus, or history restoration wins.
    // Compare before writing the next frame, allowing native pixel rounding.
    if (Math.abs(lenis.actualScroll - lenis.animatedScroll) > 1) {
      release();
      return;
    }
    advancing = true;
    try {
      lenis.raf(time);
    } finally {
      advancing = false;
    }
    if (lenis.isScrolling === "smooth") frame = requestAnimationFrame(tick);
  };

  const wake = () => {
    if (!frame && lenis) {
      // The RAF clock must restart after idle so the first frame cannot jump.
      // RAF's timestamp can precede performance.now() within the same frame.
      // Let Lenis establish its origin from the first RAF instead of mixing clocks.
      lenis.time = 0;
      frame = requestAnimationFrame(tick);
    }
  };

  const sync = () => {
    const locked =
      body.hasAttribute("data-scroll-locked") ||
      body.hasAttribute("data-smooth-scroll-locked") ||
      [root, body].some((node) =>
        ["hidden", "clip"].includes(getComputedStyle(node).overflowY),
      );
    if (reducedMotion.matches || document.hidden || locked) {
      cancelFrame();
      lenis?.destroy();
      lenis = null;
      return;
    }
    if (lenis) return;
    lenis = new Lenis({
      autoRaf: false,
      smoothWheel: true,
      syncTouch: false,
      lerp: 0.16,
      wheelMultiplier: 1,
      allowNestedScroll: true,
      // Anchors remain browser-owned: URL, focus, scroll-margin and history work
      // exactly like native links. Capture listeners below first release inertia.
      anchors: false,
      virtualScroll: ({ event, deltaX, deltaY }) => {
        if (
          event.defaultPrevented ||
          event.ctrlKey ||
          event.shiftKey ||
          Math.abs(deltaX) > Math.abs(deltaY)
        ) {
          release();
          return false;
        }
        if (event.type === "wheel") {
          // Lenis decides whether a nested scroller owns this event after this
          // callback. Only animate a consumed wheel; native containers take over.
          queueMicrotask(() => {
            if (event.defaultPrevented) wake();
            else release();
          });
        }
        return true;
      },
    });
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (SCROLL_KEYS.has(event.key)) release();
  };
  const restoreNativeScroll = nativeScrollInterop ? installNativeScrollHandoff(() => {
    // Lenis itself writes through window.scrollTo; only external calls hand off.
    if (!advancing) release();
  }) : () => {};
  // These run before React handlers and browser default actions; they do not
  // preventDefault or stopPropagation, so keyboard/selection/navigation stay native.
  window.addEventListener("pointerdown", release, true);
  window.addEventListener("touchstart", release, {
    capture: true,
    passive: true,
  });
  window.addEventListener("click", release, true);
  window.addEventListener("keydown", onKeyDown, true);
  window.addEventListener("popstate", release);
  window.addEventListener("hashchange", release);
  window.addEventListener("pageshow", sync);
  document.addEventListener("visibilitychange", sync);
  reducedMotion.addEventListener("change", sync);

  // Radix/react-remove-scroll, custom lightboxes, and fullscreen Mermaid all
  // lock differently. Observe only root attributes, never the animated subtree.
  const observer = new MutationObserver(sync);
  const options = {
    attributes: true,
    attributeFilter: [
      "style",
      "class",
      "data-scroll-locked",
      "data-smooth-scroll-locked",
    ],
  };
  observer.observe(body, options);
  observer.observe(root, options);
  sync();

  return () => {
    restoreNativeScroll();
    observer.disconnect();
    cancelFrame();
    lenis?.destroy();
    lenis = null;
    window.removeEventListener("pointerdown", release, true);
    window.removeEventListener("touchstart", release, true);
    window.removeEventListener("click", release, true);
    window.removeEventListener("keydown", onKeyDown, true);
    window.removeEventListener("popstate", release);
    window.removeEventListener("hashchange", release);
    window.removeEventListener("pageshow", sync);
    document.removeEventListener("visibilitychange", sync);
    reducedMotion.removeEventListener("change", sync);
  };
}

