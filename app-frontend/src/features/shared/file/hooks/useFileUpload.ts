'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface UploadResult {
  key: string;
  publicUrl: string;
}

export function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const xhrRef = useRef<XMLHttpRequest | null>(null);

  useEffect(() => {
    return () => {
      xhrRef.current?.abort();
    };
  }, []);

  const upload = useCallback(async (file: File, opts: { kind: string }): Promise<UploadResult> => {
    // Abort any in-flight upload
    xhrRef.current?.abort();

    setUploading(true);
    setProgress(0);

    // Presigned URL 발급
    const { data } = await apiClient.post('/storage/presign', {
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      kind: opts.kind,
    });

    // R2 직접 업로드 (진행률 추적)
    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhrRef.current = xhr;
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 100));
      };
      xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(`Upload failed: ${xhr.status}`)));
      xhr.onerror = () => reject(new Error('Upload failed'));
      xhr.onabort = () => reject(new Error('Upload aborted'));
      xhr.open('PUT', data.upload_url);
      xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
      xhr.send(file);
    });

    xhrRef.current = null;
    setUploading(false);
    setProgress(100);
    return { key: data.key, publicUrl: data.public_url };
  }, []);

  return { upload, uploading, progress };
}
