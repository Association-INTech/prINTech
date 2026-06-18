import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class Print {
  private readonly http = inject(HttpClient);
  private readonly ApiBase = '/api/v1';

  getFilaments(): Observable<Filament[]> {
    return this.http.get<Filament[]>(`${this.ApiBase}/filaments/`);
  }

  SendRequest(payload: PrintRequestPayload): Observable<PrintRequestResponse> {
    const formData = new FormData();

    formData.append('filament', String(payload.filament));
    formData.append('comment', payload.comment ?? '');
    formData.append('path', payload.path);
    formData.append('number_of_printing', String(payload.number_of_printing));

    if (payload.para_slicer !== undefined) {
      formData.append('para_slicer', JSON.stringify(payload.para_slicer));
    }

    return this.http.post<PrintRequestResponse>(`${this.ApiBase}/requests/`, formData);
  }

}

export interface Filament {
  id: number;
  color: string;
  color_name: string;
  type: string;
  quantity: number;
}

export interface PrintRequestPayload {
  filament: number;
  comment: string;
  path: File;
  number_of_printing: number;
  para_slicer?: Record<string, unknown>;
}

export interface PrintRequestResponse {
  id: string;
  user: string;
  printer: string | null;
  filament: number;
  comment: string | null;
  created_at: string;
  status: string;
}