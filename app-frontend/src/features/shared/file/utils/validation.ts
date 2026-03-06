export interface ValidationOptions {
  extensions: Set<string>;
  maxSizeMB: number;
  maxCount: number;
  maxTotalMB: number;
  currentTotalBytes?: number;
  checkMimePrefix?: string; // e.g. "image/"
}

const getExt = (name: string) => {
  const idx = name.lastIndexOf(".");
  return idx >= 0 ? name.slice(idx).toLowerCase() : "";
};

export function validateFiles(
  files: File[],
  opts: ValidationOptions
): { accepted: File[]; rejected: string[] } {
  const maxSizeBytes = opts.maxSizeMB * 1024 * 1024;
  const maxTotalBytes = opts.maxTotalMB * 1024 * 1024;

  if (files.length > opts.maxCount) {
    return {
      accepted: [],
      rejected: [`최대 ${opts.maxCount}개까지 첨부할 수 있습니다.`],
    };
  }

  let totalBytes = opts.currentTotalBytes ?? 0;
  const accepted: File[] = [];
  const rejected: string[] = [];

  files.forEach((file) => {
    const ext = getExt(file.name);

    if (!opts.extensions.has(ext)) {
      rejected.push(`${file.name}: 허용되지 않은 파일 형식`);
      return;
    }

    if (opts.checkMimePrefix) {
      const mimeType = file.type || "";
      if (!mimeType.startsWith(opts.checkMimePrefix)) {
        rejected.push(`${file.name}: 허용되지 않은 파일 형식`);
        return;
      }
    }

    if (file.size > maxSizeBytes) {
      rejected.push(`${file.name}: ${opts.maxSizeMB}MB 초과`);
      return;
    }

    if (totalBytes + file.size > maxTotalBytes) {
      rejected.push(`${file.name}: 전체 첨부 ${opts.maxTotalMB}MB 초과`);
      return;
    }

    totalBytes += file.size;
    accepted.push(file);
  });

  return { accepted, rejected };
}
