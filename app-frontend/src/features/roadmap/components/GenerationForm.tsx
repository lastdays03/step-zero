"use client";

import React, { useState } from 'react';
import { useGenerateRoadmap } from '../hooks/useGenerateRoadmap';

interface GenerationFormProps {
    onSuccess: (data: any) => void;
    onCancel: () => void;
}

export const GenerationForm = ({ onSuccess, onCancel }: GenerationFormProps) => {
    const { generate, loading, error } = useGenerateRoadmap();
    const [formData, setFormData] = useState({
        business_type: '',
        location: '',
        description: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const result = await generate(formData);
        if (result) {
            onSuccess(result);
        }
    };

    return (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-100 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">새로운 로드맵 생성</h2>
            <p className="text-gray-500 mb-6 text-sm">사업 아이디어를 입력하면 맞춤형 창업 로드맵을 생성합니다. (Mock 모드)</p>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">업종</label>
                    <input
                        type="text"
                        required
                        className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        placeholder="예: 카페, IT 스타트업, 음식점"
                        value={formData.business_type}
                        onChange={(e) => setFormData({ ...formData, business_type: e.target.value })}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">위치</label>
                    <input
                        type="text"
                        required
                        className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        placeholder="예: 서울 강남구, 경기도 판교"
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">사업 설명 (선택)</label>
                    <textarea
                        className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all min-h-[100px]"
                        placeholder="추가적인 요구사항이나 특징을 적어주세요."
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    />
                </div>

                {error && <p className="text-red-500 text-sm">{error}</p>}

                <div className="flex gap-3 pt-4">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="flex-1 px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                        취소
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-indigo-300"
                    >
                        {loading ? '생성 중...' : '로드맵 생성'}
                    </button>
                </div>
            </form>
        </div>
    );
};
