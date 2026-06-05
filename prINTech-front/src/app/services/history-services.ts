import { Injectable } from '@angular/core';
import { HistoryItem } from '../history/history.model';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { Print } from '../print/print';


const Prints: HistoryItem[] = [
    {
    id: 1,
    modelName: 'cat_PLA_67.29g.stl',
    printerName: 'SnapMaker U1',
    material: 'PLA',
    status: 'done',
    duration: 32,
    date: '09/03/2026',
    },
    {
    id: 2,
    modelName: 'dog_PLA_37.52g.stl',
    printerName: 'Creality K1C',
    material: 'PETG',
    status: 'queued',
    duration: 18,
    date: '05/04/2026',
    }
  ]

@Injectable({
  providedIn: 'root',
})


export class HistoryServices {
  private apiUrl = 'http://localhost:8000/api/history'
  private USE_MOCK: boolean = true
  

    constructor(private http: HttpClient) {}

  getHistory(): Observable<HistoryItem[]> {
    if (this.USE_MOCK == true) {
      return of(Prints);
    }
    return this.http.get<HistoryItem[]>(this.apiUrl);
  }
}
