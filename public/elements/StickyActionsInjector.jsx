/**
 * StickyActionsInjector - Injects CSS to make action buttons sticky
 *
 * This component injects CSS into the page to make the action buttons
 * float above the chat input. Render this once at chat start.
 */

import { useEffect } from 'react'

export default function StickyActionsInjector() {
  useEffect(() => {
    // Check if CSS already injected
    if (document.getElementById('mindrian-sticky-actions-css')) {
      return
    }

    // Create and inject the CSS
    const style = document.createElement('style')
    style.id = 'mindrian-sticky-actions-css'
    style.textContent = `
      /* Sticky Action Buttons - Mindrian */

      /* Make last message's actions float above chat input */
      [class*="message"]:last-child [class*="actions"],
      .MuiBox-root:last-child [class*="actions"] {
        position: fixed !important;
        bottom: 90px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        z-index: 1000 !important;
        background: rgba(255, 255, 255, 0.97) !important;
        backdrop-filter: blur(12px) !important;
        padding: 10px 20px !important;
        border-radius: 28px !important;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12), 0 1px 3px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(0, 0, 0, 0.06) !important;
        max-width: calc(100vw - 40px) !important;
        display: flex !important;
        gap: 8px !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
      }

      /* Dark mode */
      @media (prefers-color-scheme: dark) {
        [class*="message"]:last-child [class*="actions"],
        .MuiBox-root:last-child [class*="actions"] {
          background: rgba(26, 26, 46, 0.97) !important;
          border-color: rgba(255, 255, 255, 0.08) !important;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3) !important;
        }
      }

      /* Button styling in sticky bar */
      [class*="message"]:last-child [class*="actions"] button,
      .MuiBox-root:last-child [class*="actions"] button {
        border-radius: 18px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        white-space: nowrap !important;
      }

      [class*="message"]:last-child [class*="actions"] button:hover,
      .MuiBox-root:last-child [class*="actions"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
      }

      /* Add padding to chat container to prevent overlap */
      [class*="chatContainer"],
      [class*="messages-container"],
      .MuiBox-root[style*="overflow"] {
        padding-bottom: 140px !important;
      }

      /* Fade out actions on older messages */
      [class*="message"]:not(:last-child) [class*="actions"],
      .MuiBox-root:not(:last-child) [class*="actions"] {
        opacity: 0.25 !important;
        transition: opacity 0.3s ease !important;
      }

      [class*="message"]:not(:last-child):hover [class*="actions"],
      .MuiBox-root:not(:last-child):hover [class*="actions"] {
        opacity: 0.8 !important;
      }

      /* Mobile adjustments */
      @media (max-width: 640px) {
        [class*="message"]:last-child [class*="actions"],
        .MuiBox-root:last-child [class*="actions"] {
          bottom: 80px !important;
          padding: 8px 12px !important;
          gap: 6px !important;
          max-width: calc(100vw - 20px) !important;
        }

        [class*="message"]:last-child [class*="actions"] button,
        .MuiBox-root:last-child [class*="actions"] button {
          padding: 6px 12px !important;
          font-size: 12px !important;
        }
      }
    `
    document.head.appendChild(style)

    // Cleanup on unmount
    return () => {
      const existingStyle = document.getElementById('mindrian-sticky-actions-css')
      if (existingStyle) {
        existingStyle.remove()
      }
    }
  }, [])

  // This component renders nothing visible
  return null
}
