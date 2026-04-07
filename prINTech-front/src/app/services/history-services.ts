import { Injectable, inject } from '@angular/core';
import { HistoryItem } from '../history/history.model';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


@Injectable({
  providedIn: 'root',
})


export class HistoryServices {
  private readonly apiBase = '/api/v1';
  private readonly http = inject(HttpClient)

  getHistory(): Observable<HistoryItem[]> {
    return this.http.get<HistoryItem[]>(`${this.apiBase}/requests/`)
  }
}
