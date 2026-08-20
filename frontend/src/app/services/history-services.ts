import { Injectable, inject } from '@angular/core';
import { HistoryItem } from '../history/history.model';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import id from '@angular/common/locales/extra/id';
export interface Filament {
  id: number;
  color: string;
  color_name: string;
  type: string;
  quantity: number;
}

export interface Printer {
  name: string; 
  status: string;
}

@Injectable({
  providedIn: 'root',
})
export class HistoryServices {
  private readonly apiBase = 'http://127.0.0.1:8000/api/v1';
  private readonly http = inject(HttpClient)

  getHistory(): Observable<HistoryItem[]> {
    return this.http.get<HistoryItem[]>(`${this.apiBase}/requests/`)
  }

  getFilaments(): Observable<Filament[]> {
    return this.http.get<Filament[]>(`${this.apiBase}/filaments/`)
  }
  
  getPrinters(): Observable<Printer[]> {
    return this.http.get<Printer[]>(`${this.apiBase}/printers/`)
  }

  relaunchRequest(requestId: string): Observable<HistoryItem> {
    return this.http.post<HistoryItem>(`${this.apiBase}/requests/${requestId}/relaunch/`, {});
  }
  
  payRequest(id: string): Observable<any> {
    return this.http.post(`/api/v1/requests/${id}/pay/`, {});
  }
}

