"use client";

import { useEffect } from "react";
import { ToastContainer, toast } from "react-toastify";

export function ToastProvider() {
  useEffect(() => {
    const handler = ((e: CustomEvent) => {
      const detail = e.detail as { title?: string; paymentRequired?: boolean };
      const title = detail?.title ?? "an event";

      if (detail?.paymentRequired) {
        toast.warn(`Payment required: ${title}`);
      } else {
        toast.success(`Applied to ${title}`);
      }
    }) as EventListener;

    window.addEventListener("event:applied", handler);
    return () => window.removeEventListener("event:applied", handler);
  }, []);

  return (
    <ToastContainer
      position="bottom-right"
      autoClose={4000}
      hideProgressBar={false}
      newestOnTop
      closeOnClick
      pauseOnFocusLoss={false}
      draggable
      pauseOnHover
      theme="light"
      toastStyle={{
        borderRadius: "16px",
        boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
        fontSize: "13px",
        fontWeight: 500,
      }}
    />
  );
}
