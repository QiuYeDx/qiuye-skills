/**
 * Case 9 — Continuous flow transitions / 连续布局过渡.
 *
 * Integration template, not an automatic fix for every layout. Keep padding and
 * conditional spacing INSIDE the measured inner box; keep height/max-height and
 * CSS transitions OFF the outer box. Callers own lazy mounting, focus management,
 * scroll limits and any modal shell. Mount expensive children on the first open,
 * then retain them when drafts/state must survive a close.
 *
 * Requires React 19+ and motion/react (no Tailwind or application utilities).
 */
import {
  Children,
  forwardRef,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type Key,
  type ReactNode,
} from 'react';
import { AnimatePresence, motion, usePresence } from 'motion/react';

export const flowSizeTransition = { type: 'spring', duration: 0.3, bounce: 0 } as const;
export const flowContentTransition = { duration: 0.18, ease: [0.25, 0.1, 0.25, 1] } as const;

const reducedMotionQuery = '(prefers-reduced-motion: reduce)';
const getServerSnapshot = () => false;
const getReducedMotionSnapshot = () =>
  typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia(reducedMotionQuery).matches
    : false;
const subscribeReducedMotion = (notify: () => void) => {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return () => {};
  const media = window.matchMedia(reducedMotionQuery);
  media.addEventListener('change', notify);
  return () => media.removeEventListener('change', notify);
};
const useClientLayoutEffect = typeof window === 'undefined' ? useEffect : useLayoutEffect;

/** Reacts to preference changes while mounted, including mid-transition changes. */
export function useReducedMotionPreference() {
  return useSyncExternalStore(subscribeReducedMotion, getReducedMotionSnapshot, getServerSnapshot);
}

/** Only moving descendants that still contribute to the live document flow. */
export function hasMovingFlow(element: Element) {
  return Array.from(element.querySelectorAll('[data-flow-animating="true"]')).some(
    region => !region.closest('[data-flow-exiting="true"], [data-dialog-exiting="true"]')
      && region.getClientRects().length > 0,
  );
}

/** Measure the natural inner box, never the box whose height is being animated. */
export function useNaturalHeight() {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<{ height: number; following: boolean } | null>(null);

  useClientLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    const measure = () => setSize(previous => {
      const height = element.getBoundingClientRect().height;
      const following = hasMovingFlow(element);
      return previous !== null && Math.abs(previous.height - height) < 0.1
        && previous.following === following ? previous : { height, following };
    });
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  // null means not measured; an actual 0 is a valid measurement.
  return { ref, height: size?.height ?? null, following: size?.following ?? false };
}

export interface FlowRegionProps {
  children: ReactNode;
  className?: string;
  innerClassName?: string;
  open?: boolean;
  fade?: boolean;
  /** Use for a newly inserted region; initial page/dialog content usually stays false. */
  enterFromZero?: boolean;
  onHeightComplete?: () => void;
}

/**
 * Animate the actual flow footprint. Siblings move through ordinary layout,
 * without scaling text or adding layout projection to every element.
 * Keep children mounted during close; `open && children` defeats the exit.
 */
export function FlowRegion({
  children, className, innerClassName, open = true, fade = false,
  enterFromZero = false, onHeightComplete,
}: FlowRegionProps) {
  const { ref, height, following } = useNaturalHeight();
  const outer = useRef<HTMLDivElement>(null);
  const completionFrame = useRef<number | null>(null);
  useEffect(() => () => {
    if (completionFrame.current !== null) cancelAnimationFrame(completionFrame.current);
  }, []);
  const reduce = useReducedMotionPreference();
  const [visibility, setVisibility] = useState({ open, moving: false });
  if (visibility.open !== open) setVisibility({ open, moving: true });

  // An explicit local open/close (including reversal) owns its interpolation.
  // Only steady open ancestors follow already-interpolated descendant geometry.
  const follow = open && following && !visibility.moving;
  const target = open ? height ?? (enterFromZero ? 0 : 'auto') : 0;
  const latestTarget = useRef(target);
  latestTarget.current = target;

  // Mark before ResizeObserver runs. Re-springing every child frame creates lag.
  useClientLayoutEffect(() => {
    const element = outer.current;
    if (!element) return;
    if (!reduce && !follow && typeof target === 'number'
      && Math.abs(element.getBoundingClientRect().height - target) > 0.1) {
      element.dataset.flowAnimating = 'true';
    } else {
      delete element.dataset.flowAnimating;
    }
  }, [target, reduce, follow]);

  return (
    <motion.div
      ref={outer}
      data-flow-motion="true"
      inert={!open}
      aria-hidden={open ? undefined : true}
      className={className}
      style={{ minWidth: 0, overflow: 'hidden', transition: 'none' }}
      initial={enterFromZero ? { height: 0 } : false}
      // Equal target keyframes explicitly cancel a running spring when the user
      // enables reduced motion. Updating transition alone leaves it running.
      animate={{ height: reduce ? [target, target] : target }}
      transition={reduce || follow ? { duration: 0 } : flowSizeTransition}
      onAnimationComplete={() => {
        // Zero-duration completion may precede the DOM style write. Verify on
        // the next frame, and never let a superseded target finish a new one.
        const completedTarget = latestTarget.current;
        if (completionFrame.current !== null) cancelAnimationFrame(completionFrame.current);
        completionFrame.current = requestAnimationFrame(() => {
          completionFrame.current = null;
          if (!outer.current || completedTarget !== latestTarget.current) return;
          if (typeof completedTarget === 'number'
            && Math.abs(outer.current.getBoundingClientRect().height - completedTarget) > 0.5) return;
          delete outer.current.dataset.flowAnimating;
          setVisibility(previous => previous.moving ? { ...previous, moving: false } : previous);
          onHeightComplete?.();
        });
      }}
    >
      <motion.div
        ref={ref}
        data-flow-motion-inner="true"
        className={innerClassName}
        style={{
          display: 'flow-root', minWidth: 0, transition: 'none',
          visibility: fade && !open && !visibility.moving ? 'hidden' : undefined,
        }}
        initial={false}
        animate={{ opacity: reduce ? [fade && !open ? 0 : 1, fade && !open ? 0 : 1] : fade && !open ? 0 : 1 }}
        transition={reduce ? { duration: 0 } : { ...flowContentTransition, duration: open ? 0.18 : 0.16 }}
      >
        {children}
      </motion.div>
    </motion.div>
  );
}

// popLayout needs a ref to the actual DOM child, not an intervening component.
const FlowStage = forwardRef<HTMLDivElement, { children: ReactNode; className?: string }>(
  function FlowStage({ children, className }, ref) {
    const [present, safeToRemove] = usePresence();
    const reduce = useReducedMotionPreference();
    return (
      <motion.div
        ref={ref}
        className={className}
        style={{ minWidth: 0, transition: 'none' }}
        data-flow-exiting={present ? undefined : 'true'}
        inert={!present}
        aria-hidden={present ? undefined : true}
        initial={{ opacity: 0, y: reduce ? 0 : 4 }}
        animate={present ? 'present' : 'exiting'}
        variants={{
          present: { opacity: reduce ? [1, 1] : 1, y: reduce ? [0, 0] : 0 },
          exiting: { opacity: reduce ? [0, 0] : 0, y: reduce ? [0, 0] : -3,
            transition: { ...flowContentTransition, duration: reduce ? 0 : 0.16 } },
        }}
        transition={reduce ? { duration: 0 } : flowContentTransition}
        // Own the presence completion so a live preference change can retarget
        // an exit already in progress, rather than waiting for its old tween.
        onAnimationComplete={definition => {
          if (definition === 'exiting' && !present) safeToRemove?.();
        }}
      >
        {children}
      </motion.div>
    );
  },
);

export interface FlowSwapProps {
  transitionKey: Key;
  children: ReactNode;
  className?: string;
  stageClassName?: string;
  /** False when an existing shell owns a fixed-height layout; keep presence only. */
  animateHeight?: boolean;
}

/**
 * Key semantic stages (preview/error/step), never live form values. Preserve the
 * wrapper until BOTH height collapse and the outgoing stage's exit complete.
 * Persistent form tabs need retained panels; do not re-key them on every switch.
 */
export function FlowSwap({
  transitionKey, children, className, stageClassName, animateHeight = true,
}: FlowSwapProps) {
  const hasContent = Children.toArray(children).some(child => child !== '');
  const currentContent = useRef(hasContent);
  currentContent.current = hasContent;
  const [retained, setRetained] = useState(hasContent);
  const [heightDone, setHeightDone] = useState(false);
  const [exitDone, setExitDone] = useState(false);
  const mounted = useRef(false);
  useEffect(() => { mounted.current = true; }, []);
  useEffect(() => {
    if (hasContent) {
      setRetained(true);
      setHeightDone(false);
      setExitDone(false);
    } else if (exitDone && (heightDone || !animateHeight)) {
      setRetained(false);
    }
  }, [hasContent, exitDone, heightDone, animateHeight]);

  // Empty wrappers must eventually leave gap/space-y/:last-child calculations.
  // Their disappearing spacing must be owned inside the region, not by a gap.
  if (!hasContent && !retained) return null;
  const content = (
    <AnimatePresence
      initial={mounted.current}
      mode="popLayout"
      onExitComplete={() => { if (!currentContent.current) setExitDone(true); }}
    >
      {hasContent && <FlowStage key={transitionKey} className={stageClassName}>{children}</FlowStage>}
    </AnimatePresence>
  );

  return animateHeight ? (
    <FlowRegion
      className={className}
      open={hasContent}
      enterFromZero={mounted.current && !retained}
      onHeightComplete={() => { if (!currentContent.current) setHeightDone(true); }}
    >
      {/* This relative natural box is popLayout's containing block. */}
      <div style={{ position: 'relative', minWidth: 0 }}>{content}</div>
    </FlowRegion>
  ) : (
    <div className={className} style={{ position: 'relative', minWidth: 0 }}>{content}</div>
  );
}
