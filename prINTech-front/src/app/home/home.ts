import { Component, inject, OnInit } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HomeService } from '../services/home';
import { MetricCard } from './components/metric-card/metric-card';

@Component({
  selector: 'app-home',
  imports: [RouterLink, NgOptimizedImage, MetricCard],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit{
  private readonly homeService = inject(HomeService);

  ngOnInit(): void {
    this.homeService.loadUserInfo();
    this.homeService.getActivePrinters();
  }

  Username = this.homeService.username
}
