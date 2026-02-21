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
}

export interface ActionKitItem {
    tag?: string;
    name: string;
    summary: string;
    type: string;
    path: string;
    relatedLaws?: (string | RelatedLaw)[];
    dday?: string;
    previewImageUrl?: string;
    usageTips?: string[];
}

export interface ActionKitCategory {
    title: string;
    items: ActionKitItem[];
}

export type LawData = Record<string, LawChapter>;
export type ActionKitData = Record<string, ActionKitCategory>;
