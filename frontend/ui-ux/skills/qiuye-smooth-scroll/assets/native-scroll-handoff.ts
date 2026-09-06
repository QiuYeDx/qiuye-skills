/** Let native programmatic scrolling interrupt wheel inertia before its first
 * frame. A scroll event is too late: the smoother could overwrite that frame. */
export function installNativeScrollHandoff(beforeScroll: () => void) {
  const restore: (() => void)[] = [];
  const bridge = (target: Window | typeof Element.prototype, key: string) => {
    const native = Reflect.get(target, key);
    if (typeof native !== "function") return;
    const descriptor = Object.getOwnPropertyDescriptor(target, key);
    const wrapped = function (this: Window | Element, ...args: unknown[]) {
      if (
        target === window ||
        key === "scrollIntoView" ||
        this === document.scrollingElement ||
        this === document.body
      )
        beforeScroll();
      return Reflect.apply(native, this, args);
    };
    Object.defineProperty(target, key, {
      configurable: true,
      enumerable: descriptor?.enumerable ?? true,
      writable: true,
      value: wrapped,
    });
    restore.push(() => {
      // Don't overwrite a replacement installed by another integration later.
      if (Reflect.get(target, key) !== wrapped) return;
      if (descriptor) Object.defineProperty(target, key, descriptor);
      else Reflect.deleteProperty(target, key);
    });
  };
  for (const key of ["scroll", "scrollTo", "scrollBy"]) {
    bridge(window, key);
    bridge(Element.prototype, key);
  }
  bridge(Element.prototype, "scrollIntoView");
  return () => restore.reverse().forEach((cleanup) => cleanup());
}
