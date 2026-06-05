import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { HistoryServices, Filament } from '../services/history-services';
import { HistoryItem } from './history.model';

@Component({
  selector: 'app-history',
  imports: [CommonModule],
  templateUrl: './history.html',
  styleUrl: './history.css',
})
export class History implements OnInit{
  private readonly historyService = inject(HistoryServices);
  private readonly cdr = inject(ChangeDetectorRef);

  fullHistory: HistoryItem[] = [];
  filteredHistory: HistoryItem[] = [];
  filaments: Filament[] = [];
  SearchQuery = '';

  ngOnInit(): void {
    console.log("HISTORY COMPONENT INIT");
    this.loadFilaments();
    this.loadHistory();
  }

  onSearch(event: Event) {
    this.SearchQuery = (event.target as HTMLInputElement).value;
    this.applyFilters();
  }

  private applyFilters(): void {
    const query = this.SearchQuery.toLowerCase();
    if (!query) {
      this.filteredHistory = this.fullHistory;
    } else {
      this.filteredHistory = this.fullHistory.filter(item => {
        const fileName = this.getFileName(item.file?.path).toLowerCase();
        return fileName.includes(query);
      });
    }
    console.log("FILTERED HISTORY:", this.filteredHistory);
    this.cdr.detectChanges();
  }

  private loadFilaments(): void {
    this.historyService.getFilaments().subscribe({
      next: (filaments) => {
        this.filaments = filaments;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error("ERROR LOADING FILAMENTS:", err);
        this.filaments = [];
      },
    });
  }

  private loadHistory(): void {
    this.historyService.getHistory().subscribe({
      next: (response: any) => {
        console.log("RAW HISTORY RESPONSE:", response);
        const items = response?.results ? response.results : (Array.isArray(response) ? response : []);
        console.log("PROCESSED ITEMS:", items);
        this.fullHistory = items;
        this.applyFilters();
      },
      error: (err) => {
        console.error("ERROR LOADING HISTORY:", err);
        this.fullHistory = [];
        this.applyFilters();
      },
    });
  }

  getFilamentName(filamentId: number | null | undefined): string {
    if (filamentId == null) return '-';
    const filament = this.filaments.find(f => f.id === filamentId);
    if (!filament) return `ID: ${filamentId}`;
    return `${filament.type} (${filament.color_name})`;
  }

  getFileName(path: string | null | undefined): string {
    if (!path) return '-';
    return path.split('/').pop() || path;
  }
}
