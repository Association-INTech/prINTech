import { Component, OnInit } from '@angular/core';
import { HistoryServices } from '../services/history-services';
import { HistoryItem } from './history.model';

@Component({
  selector: 'app-history',
  imports: [],
  templateUrl: './history.html',
  styleUrl: './history.css',
})
export class History implements OnInit{
  fullHistory: HistoryItem[] = [];
  filteredHistory: HistoryItem[] = [];
  SearchQuery = '';
  SelectedStatus = '';
  SelectedMaterial = ';'

  ngOnInit(): void {
    
  }
}
