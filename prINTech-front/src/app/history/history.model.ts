export type HistoryStatus = 'queued' | 'running' | 'done' | 'failed';

export interface HistoryItem {
    id: number;
    modelName: string;
    printerName: string;
    material: string;
    status: HistoryStatus;
    duration: number;
    date: string;
}

export interface HistoryListResponse {
    results: HistoryItem[];
    count: number;
}