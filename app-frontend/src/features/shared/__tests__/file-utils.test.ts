import { resolveUploadUrl } from '../file/utils/url';
import { validateFiles, ValidationOptions } from '../file/utils/validation';

describe('resolveUploadUrl', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    delete process.env.NEXT_PUBLIC_STORAGE_URL;
    delete process.env.NEXT_PUBLIC_API_URL;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it('빈 값이면 빈 문자열 반환', () => {
    expect(resolveUploadUrl()).toBe('');
    expect(resolveUploadUrl('')).toBe('');
  });

  it('http/https URL은 그대로 반환', () => {
    expect(resolveUploadUrl('https://r2.example.com/file.jpg')).toBe('https://r2.example.com/file.jpg');
    expect(resolveUploadUrl('http://localhost/file.jpg')).toBe('http://localhost/file.jpg');
  });

  describe('R2 모드', () => {
    it('NEXT_PUBLIC_STORAGE_URL 설정 시 R2 URL 반환', () => {
      process.env.NEXT_PUBLIC_STORAGE_URL = 'https://pub-abc.r2.dev';
      expect(resolveUploadUrl('profile/avatar.png')).toBe('https://pub-abc.r2.dev/profile/avatar.png');
    });

    it('슬래시 정규화', () => {
      process.env.NEXT_PUBLIC_STORAGE_URL = 'https://pub-abc.r2.dev/';
      expect(resolveUploadUrl('/profile/avatar.png')).toBe('https://pub-abc.r2.dev/profile/avatar.png');
    });
  });

  describe('로컬 모드', () => {
    it('NEXT_PUBLIC_API_URL 기반 로컬 URL', () => {
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
      expect(resolveUploadUrl('profile/avatar.png')).toBe('http://localhost:8000/api/uploads/profile/avatar.png');
    });

    it('api/uploads/ 프리픽스 중복 제거', () => {
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
      expect(resolveUploadUrl('api/uploads/profile/avatar.png')).toBe('http://localhost:8000/api/uploads/profile/avatar.png');
    });

    it('기본값 localhost:8000', () => {
      expect(resolveUploadUrl('profile/test.png')).toBe('http://localhost:8000/api/uploads/profile/test.png');
    });
  });
});

describe('validateFiles', () => {
  const defaultOpts: ValidationOptions = {
    extensions: new Set(['.jpg', '.png']),
    maxSizeMB: 5,
    maxCount: 3,
    maxTotalMB: 10,
  };

  function mockFile(name: string, size: number, type = ''): File {
    const file = new File(['x'.repeat(size)], name, { type });
    Object.defineProperty(file, 'size', { value: size });
    return file;
  }

  it('유효한 파일 전부 accepted', () => {
    const files = [mockFile('a.jpg', 1000), mockFile('b.png', 2000)];
    const { accepted, rejected } = validateFiles(files, defaultOpts);
    expect(accepted).toHaveLength(2);
    expect(rejected).toHaveLength(0);
  });

  it('최대 개수 초과 시 전부 rejected', () => {
    const files = [mockFile('a.jpg', 100), mockFile('b.jpg', 100), mockFile('c.jpg', 100), mockFile('d.jpg', 100)];
    const { accepted, rejected } = validateFiles(files, defaultOpts);
    expect(accepted).toHaveLength(0);
    expect(rejected[0]).toContain('3개');
  });

  it('허용되지 않은 확장자 rejected', () => {
    const files = [mockFile('a.gif', 100)];
    const { accepted, rejected } = validateFiles(files, defaultOpts);
    expect(accepted).toHaveLength(0);
    expect(rejected[0]).toContain('허용되지 않은 파일 형식');
  });

  it('개별 파일 크기 초과 rejected', () => {
    const files = [mockFile('a.jpg', 6 * 1024 * 1024)];
    const { accepted, rejected } = validateFiles(files, defaultOpts);
    expect(accepted).toHaveLength(0);
    expect(rejected[0]).toContain('5MB 초과');
  });

  it('전체 용량 초과 시 해당 파일만 rejected', () => {
    const files = [mockFile('a.jpg', 4 * 1024 * 1024), mockFile('b.jpg', 4 * 1024 * 1024), mockFile('c.jpg', 4 * 1024 * 1024)];
    const { accepted, rejected } = validateFiles(files, defaultOpts);
    expect(accepted).toHaveLength(2);
    expect(rejected).toHaveLength(1);
    expect(rejected[0]).toContain('전체 첨부');
  });

  it('MIME 타입 검사', () => {
    const opts: ValidationOptions = { ...defaultOpts, checkMimePrefix: 'image/' };
    const files = [mockFile('a.jpg', 100, 'application/pdf')];
    const { accepted, rejected } = validateFiles(files, opts);
    expect(accepted).toHaveLength(0);
    expect(rejected[0]).toContain('허용되지 않은 파일 형식');
  });

  it('currentTotalBytes 고려', () => {
    const opts: ValidationOptions = { ...defaultOpts, currentTotalBytes: 9 * 1024 * 1024 };
    const files = [mockFile('a.jpg', 2 * 1024 * 1024)];
    const { accepted, rejected } = validateFiles(files, opts);
    expect(accepted).toHaveLength(0);
    expect(rejected[0]).toContain('전체 첨부');
  });
});
