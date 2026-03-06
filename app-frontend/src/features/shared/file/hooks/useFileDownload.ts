'use client';

import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';

export function useFileDownload() {
  const [downloading, setDownloading] = useState(false);

  const download = useCallback(async (opts: { apiPath?: string; url?: string; filename: string }) => {
    setDownloading(true);
    try {
      let blob: Blob;
      if (opts.apiPath) {
        const res = await apiClient.get(opts.apiPath, { responseType: 'blob' });
        blob = new Blob([res.data]);
      } else if (opts.url) {
        const res = await fetch(opts.url);
        if (!res.ok) {
          throw new Error(`Download failed: ${res.status} ${res.statusText}`);
        }
        blob = await res.blob();
      } else {
        throw new Error('apiPath or url required');
      }

      const objUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objUrl;
      link.download = opts.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(objUrl);
    } finally {
      setDownloading(false);
    }
  }, []);

  return { download, downloading };
}
