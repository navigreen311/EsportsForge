"use client";

import { useState, useEffect, useRef } from "react";
import { Download, FileText, Share2, Table2, Link as LinkIcon } from "lucide-react";

export default function ExportDropdown() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  function handleCopy() {
    setCopied(true);
    setOpen(false);
    setTimeout(() => setCopied(false), 2000);
  }

  function close() {
    setOpen(false);
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg border border-dark-600 bg-dark-800/50 text-sm font-medium text-dark-200 hover:border-dark-500 transition-colors"
      >
        <Download className="h-4 w-4" />
        Export
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-56 rounded-lg border border-dark-700 bg-dark-900 shadow-xl z-20 py-1">
          <button
            onClick={close}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-dark-200 hover:bg-dark-700/50 transition-colors"
          >
            <FileText className="h-4 w-4" />
            Download PDF Report
          </button>
          <button
            onClick={close}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-dark-200 hover:bg-dark-700/50 transition-colors"
          >
            <Share2 className="h-4 w-4" />
            Share Win Rate Chart
          </button>
          <button
            onClick={close}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-dark-200 hover:bg-dark-700/50 transition-colors"
          >
            <Table2 className="h-4 w-4" />
            Export Session History CSV
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-dark-200 hover:bg-dark-700/50 transition-colors"
          >
            <LinkIcon className="h-4 w-4" />
            {copied ? "Copied!" : "Copy Report Link"}
          </button>
        </div>
      )}
    </div>
  );
}
