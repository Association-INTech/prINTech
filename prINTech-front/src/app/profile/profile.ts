import { Component, inject, OnInit } from '@angular/core';
import { HomeService } from '../services/home';
import { Home } from '../home/home';

@Component({
  selector: 'app-profile',
  imports: [],
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class Profile implements OnInit{
  private readonly homeService = inject(HomeService)
  ngOnInit(): void {
    this.homeService.getUsername();
    this.homeService.getEmail();
    this.homeService.getCredit();
  }

  username = this.homeService.username
  email = this.homeService.email
  credit = this.homeService.userCredit
}
