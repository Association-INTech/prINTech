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

  errorMessage = '';
  successMessage = '';
  relaunchingIds = new Set<string>();

  ngOnInit(): void {
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
    this.cdr.detectChanges();
  }

  private loadFilaments(): void {
    this.historyService.getFilaments().subscribe({
      next: (filaments) => {
        this.filaments = filaments;
        this.cdr.detectChanges();
      },
      error: () => {
        this.filaments = [];
      },
    });
  }

  private loadHistory(): void {
    this.historyService.getHistory().subscribe({
      next: (response: any) => {
        const items = response?.results ? response.results : (Array.isArray(response) ? response : []);
        this.fullHistory = items;
        if (items.length === 0 && !Array.isArray(response)) {
            this.errorMessage = 'Parsed items is empty but response was ' + JSON.stringify(response);
        }
        this.applyFilters();
      },
      error: (err) => {
        this.errorMessage = err.message || 'Error occurred';
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

  onRelaunch(item: HistoryItem): void {
    if (this.relaunchingIds.has(item.id)) {
      return;
    }

    this.errorMessage = '';
    this.successMessage = '';
    this.relaunchingIds.add(item.id);

    this.historyService.relaunchRequest(item.id).subscribe({
      next: () => {
        this.successMessage = 'Demande relancée avec succès.';
        this.relaunchingIds.delete(item.id);
        this.loadHistory();
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err?.error?.error || 'Impossible de relancer cette impression.';
        this.relaunchingIds.delete(item.id);
        this.cdr.detectChanges();
      },
    });
  }

  isRelaunching(id: string): boolean {
    return this.relaunchingIds.has(id);
  }
}

