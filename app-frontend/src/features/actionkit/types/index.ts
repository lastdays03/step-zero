export interface LawItem {
    name: string;
    ext: string;
    size: string;
    summary: string;
    path: string;
    highlights?: string[];
}

export interface LawChapter {
    title: string;
    items: LawItem[];
}

export interface RelatedLaw {
    name: string;
    summary?: string;
    snippet?: string;
}

export interface ActionKitHighlight {
    id: number;
    content: string;
}

export interface ActionKitFileRecord {
    id: number;
    version: number;
    is_current: boolean;
    original_filename?: string;
    size_bytes?: number;
}

export interface ActionKitItem {
    id?: number;
    tag?: string;
    name: string;
    summary: string;
    type: string;
    path: string;
    ext?: string;
    relatedLaws?: (string | RelatedLaw)[];
    dday?: string;
    previewImageUrl?: string;
    usageTips?: string[];
    complianceChecklist?: string[];
    highlights?: ActionKitHighlight[];
    files?: ActionKitFileRecord[];
}

export interface ActionKitCategory {
    title: string;
    items: ActionKitItem[];
}

export type LawData = Record<string, LawChapter>;
export type ActionKitData = Record<string, ActionKitCategory>;
