export type HistoryStatus =
    | 'SUBMITTED'
    | 'AWAITING_PAYMENT'
    | 'PENDING'
    | 'PRINTING'
    | 'DONE'
    | 'FAILED'
    | 'CANCELED';

export interface HistoryFile {
    path: string;
    number_of_printing: number;
    filament: number;
    para_slicer: string | Record<string, unknown>;
}

export interface HistoryItem {
    id: string;
    user: string;
    file: HistoryFile | null;
    printer: string | null;
    comment: string;
    created_at: string;
    status: HistoryStatus;
}
