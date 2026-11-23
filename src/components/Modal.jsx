/**
 * Accessible modal wrapper.
 * - role="dialog" + aria-modal + aria-labelledby
 * - Focus trap: Tab cycles within focusable elements
 * - Escape closes the modal
 * - Focus moves to first focusable element on open
 * - Focus restores to trigger element on close
 */
import { useEffect, useRef } from 'react';
import './Modal.css';

const FOCUSABLE = [
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  'a[href]',
].join(', ');

export default function Modal({ title, titleId = 'modal-title', onClose, children, size = 'md' }) {
  const overlayRef  = useRef(null);
  const triggerRef  = useRef(document.activeElement); // remember who opened us

  /* Move focus into the dialog on open */
  useEffect(() => {
    const first = overlayRef.current?.querySelector(FOCUSABLE);
    first?.focus();

    /* Restore focus on unmount */
    return () => {
      triggerRef.current?.focus();
    };
  }, []);

  /* Focus trap + Escape */
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key !== 'Tab') return;

      const dialog    = overlayRef.current?.querySelector('[role="dialog"]');
      if (!dialog) return;
      const focusables = Array.from(dialog.querySelectorAll(FOCUSABLE));
      if (!focusables.length) return;

      const first = focusables[0];
      const last  = focusables[focusables.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <div
      ref={overlayRef}
      className="adm-modal-overlay"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      aria-hidden="false"
    >
      <div
        className={`adm-modal adm-modal--${size} card`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="adm-modal__hd">
          <h3 className="adm-modal__title" id={titleId}>{title}</h3>
          <button
            className="adm-modal__close"
            onClick={onClose}
            aria-label={`Close ${title}`}
          >✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}
