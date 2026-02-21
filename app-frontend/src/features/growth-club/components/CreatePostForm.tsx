'use client';

import React, { useState, useRef } from 'react';
import { Camera, Paperclip, Send, X, FileText, Hash } from 'lucide-react';
import { AxiosError } from 'axios';
import { growthClubApi } from '../api';

interface CreatePostFormProps {
    onSuccess: () => void;
}

const MAX_IMAGE_MB = 20;
const MAX_FILE_MB = 50;
const MAX_TOTAL_MB = 200;
const MAX_IMAGE_COUNT = 10;
const MAX_FILE_COUNT = 10;
const MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024;
const MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024;
const MAX_TOTAL_BYTES = MAX_TOTAL_MB * 1024 * 1024;
const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".webp"]);
const FILE_EXTENSIONS = new Set([".pdf", ".doc", ".docx", ".hwp", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"]);

const getExt = (name: string) => {
    const idx = name.lastIndexOf(".");
    return idx >= 0 ? name.slice(idx).toLowerCase() : "";
};

export const CreatePostForm: React.FC<CreatePostFormProps> = ({ onSuccess }) => {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [category, setCategory] = useState('free');
    const [tagInput, setTagInput] = useState('');
    const [tags, setTags] = useState<string[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // 파일 업로드 상태
    const [imageFiles, setImageFiles] = useState<File[]>([]);
    const [imagePreviews, setImagePreviews] = useState<string[]>([]);
    const [otherFiles, setOtherFiles] = useState<File[]>([]);

    const imageInputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const incoming = Array.from(e.target.files || []);
        if (incoming.length === 0) return;

        if (imageFiles.length + incoming.length > MAX_IMAGE_COUNT) {
            alert(`이미지는 최대 ${MAX_IMAGE_COUNT}개까지 첨부할 수 있습니다.`);
            if (imageInputRef.current) imageInputRef.current.value = '';
            return;
        }

        const currentTotalBytes = imageFiles.reduce((sum, file) => sum + file.size, 0)
            + otherFiles.reduce((sum, file) => sum + file.size, 0);
        let totalBytes = currentTotalBytes;

        const accepted: File[] = [];
        const rejected: string[] = [];
        incoming.forEach((file) => {
            const ext = getExt(file.name);
            const isImageType = (file.type || "").startsWith("image/");
            if (!isImageType || !IMAGE_EXTENSIONS.has(ext)) {
                rejected.push(`${file.name}: 허용되지 않은 이미지 형식`);
                return;
            }
            if (file.size > MAX_IMAGE_BYTES) {
                rejected.push(`${file.name}: ${MAX_IMAGE_MB}MB 초과`);
                return;
            }
            if (totalBytes + file.size > MAX_TOTAL_BYTES) {
                rejected.push(`${file.name}: 전체 첨부 ${MAX_TOTAL_MB}MB 초과`);
                return;
            }
            totalBytes += file.size;
            accepted.push(file);
        });

        if (rejected.length > 0) {
            alert(rejected.join("\n"));
        }
        if (accepted.length === 0) {
            if (imageInputRef.current) imageInputRef.current.value = '';
            return;
        }

        setImageFiles((prev) => [...prev, ...accepted]);
        accepted.forEach((file) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreviews((prev) => [...prev, String(reader.result || "")]);
            };
            reader.readAsDataURL(file);
        });
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const incoming = Array.from(e.target.files || []);
        if (incoming.length === 0) return;

        if (otherFiles.length + incoming.length > MAX_FILE_COUNT) {
            alert(`일반 파일은 최대 ${MAX_FILE_COUNT}개까지 첨부할 수 있습니다.`);
            if (fileInputRef.current) fileInputRef.current.value = '';
            return;
        }

        const currentTotalBytes = imageFiles.reduce((sum, file) => sum + file.size, 0)
            + otherFiles.reduce((sum, file) => sum + file.size, 0);
        let totalBytes = currentTotalBytes;

        const accepted: File[] = [];
        const rejected: string[] = [];
        incoming.forEach((file) => {
            const ext = getExt(file.name);
            if (!FILE_EXTENSIONS.has(ext)) {
                rejected.push(`${file.name}: 허용되지 않은 파일 형식`);
                return;
            }
            if (file.size > MAX_FILE_BYTES) {
                rejected.push(`${file.name}: ${MAX_FILE_MB}MB 초과`);
                return;
            }
            if (totalBytes + file.size > MAX_TOTAL_BYTES) {
                rejected.push(`${file.name}: 전체 첨부 ${MAX_TOTAL_MB}MB 초과`);
                return;
            }
            totalBytes += file.size;
            accepted.push(file);
        });

        if (rejected.length > 0) {
            alert(rejected.join("\n"));
        }
        if (accepted.length === 0) {
            if (fileInputRef.current) fileInputRef.current.value = '';
            return;
        }

        setOtherFiles((prev) => [...prev, ...accepted]);
    };

    const removeImage = (index: number) => {
        setImageFiles((prev) => prev.filter((_, i) => i !== index));
        setImagePreviews((prev) => prev.filter((_, i) => i !== index));
        if (imageInputRef.current) imageInputRef.current.value = '';
    };

    const removeFile = (index: number) => {
        setOtherFiles((prev) => prev.filter((_, i) => i !== index));
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const val = tagInput.trim().replace(/^#/, '').replace(/,$/, '');
            if (val && !tags.includes(val)) {
                setTags([...tags, val]);
            }
            setTagInput('');
        } else if (e.key === 'Backspace' && !tagInput && tags.length > 0) {
            setTags(tags.slice(0, -1));
        }
    };

    const removeTag = (tagToRemove: string) => {
        setTags(tags.filter(t => t !== tagToRemove));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title || !content) return;

        setIsSubmitting(true);
        try {
            const formData = new FormData();
            formData.append('title', title);
            formData.append('content', content);
            formData.append('category', category);
            if (tags.length > 0) {
                formData.append('tags', tags.join(','));
            }

            imageFiles.forEach((it) => formData.append('images', it));
            otherFiles.forEach((it) => formData.append('files', it));

            await growthClubApi.createPost(formData);
            setTitle('');
            setContent('');
            setImageFiles([]);
            setImagePreviews([]);
            setOtherFiles([]);
            setTags([]);
            if (imageInputRef.current) imageInputRef.current.value = '';
            if (fileInputRef.current) fileInputRef.current.value = '';
            onSuccess();
        } catch (error: unknown) {
            console.error('Failed to create post:', error);
            const status = error instanceof AxiosError ? error.response?.status : undefined;
            if (status === 401) {
                alert('인증이 만료되었습니다. 다시 로그인해주세요.');
            } else {
                alert('게시글 작성에 실패했습니다. 네트워크 상태를 확인해주세요.');
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800 p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex gap-2">
                    {['free', 'neighborhood', 'industry'].map((cat) => (
                        <button
                            key={cat}
                            type="button"
                            onClick={() => setCategory(cat)}
                            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${category === cat
                                ? 'bg-blue-600 text-white'
                                : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                                }`}
                        >
                            {cat === 'free' ? '자유게시판' : cat === 'neighborhood' ? '동네 소식' : '업종 이야기'}
                        </button>
                    ))}
                </div>

                <input
                    type="text"
                    placeholder="제목을 입력하세요"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full bg-transparent text-lg font-bold placeholder:text-zinc-400 focus:outline-none dark:text-white"
                />

                <textarea
                    placeholder="오늘 어떤 일이 있었나요? 다른 창업자들과 나눠보세요."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={4}
                    className="w-full bg-transparent text-sm placeholder:text-zinc-400 focus:outline-none resize-none dark:text-zinc-300"
                />

                {/* 태그 입력 영역 */}
                <div className="flex flex-wrap items-center gap-2 p-2 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-dashed border-zinc-200 dark:border-zinc-700">
                    <div className="flex items-center gap-1 text-zinc-400">
                        <Hash size={16} />
                    </div>
                    {tags.map((tag) => (
                        <span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-md">
                            #{tag}
                            <button type="button" onClick={() => removeTag(tag)} className="hover:text-blue-800">
                                <X size={10} />
                            </button>
                        </span>
                    ))}
                    <input
                        type="text"
                        placeholder="태그 입력 (엔터 또는 쉼표)"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyDown={handleTagKeyDown}
                        className="flex-1 bg-transparent text-xs focus:outline-none placeholder:text-zinc-400 min-w-[120px]"
                    />
                </div>

                {/* 이미지 미리보기 및 파일 목록 */}
                {(imagePreviews.length > 0 || otherFiles.length > 0) && (
                    <div className="flex flex-wrap gap-3 py-2">
                        {imagePreviews.map((preview, index) => (
                            <div key={`img-${index}`} className="relative group w-24 h-24">
                                <img src={preview} alt="Preview" className="w-full h-full object-cover rounded-lg border border-zinc-100 dark:border-zinc-800" />
                                <button
                                    type="button"
                                    onClick={() => removeImage(index)}
                                    className="absolute -top-2 -right-2 bg-zinc-900/80 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                    <X size={12} />
                                </button>
                            </div>
                        ))}
                        {otherFiles.map((otherFile, index) => (
                            <div key={`file-${index}-${otherFile.name}`} className="flex items-center gap-2 bg-zinc-50 dark:bg-zinc-800 px-3 py-2 rounded-lg border border-zinc-100 dark:border-zinc-700 group">
                                <FileText size={16} className="text-zinc-400" />
                                <span className="text-xs text-zinc-600 dark:text-zinc-400 max-w-[150px] truncate">
                                    {otherFile.name}
                                </span>
                                <button
                                    type="button"
                                    onClick={() => removeFile(index)}
                                    className="text-zinc-400 hover:text-red-500 transition-colors"
                                >
                                    <X size={14} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                <div className="flex items-center justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800">
                    <div className="flex items-center gap-4">
                        <input
                            type="file"
                            accept=".jpg,.jpeg,.png,.webp,image/*"
                            multiple
                            className="hidden"
                            ref={imageInputRef}
                            onChange={handleImageChange}
                        />
                        <button
                            type="button"
                            onClick={() => imageInputRef.current?.click()}
                            className={`text-zinc-400 hover:text-blue-500 transition-colors ${imageFiles.length > 0 ? 'text-blue-500' : ''}`}
                            title="이미지 추가"
                        >
                            <Camera size={20} />
                        </button>

                        <input
                            type="file"
                            accept=".pdf,.doc,.docx,.hwp,.xls,.xlsx,.ppt,.pptx,.txt"
                            multiple
                            className="hidden"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                        />
                        <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            className={`text-zinc-400 hover:text-blue-500 transition-colors ${otherFiles.length > 0 ? 'text-blue-500' : ''}`}
                            title="파일 추가"
                        >
                            <Paperclip size={20} />
                        </button>
                    </div>
                    <button
                        type="submit"
                        disabled={isSubmitting || !title || !content}
                        className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-blue-500/20"
                    >
                        <Send size={16} />
                        <span>{isSubmitting ? '게시 중...' : '등록하기'}</span>
                    </button>
                </div>
            </form>
        </div>
    );
};
