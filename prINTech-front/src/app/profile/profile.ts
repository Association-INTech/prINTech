import { Component, inject, OnInit } from '@angular/core';
import { HomeService } from '../services/home';
import { ChangePassword } from './change-password/change-password';

@Component({
  selector: 'app-profile',
  imports: [ChangePassword],
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class Profile implements OnInit{
  private readonly homeService = inject(HomeService)
  ngOnInit(): void {
    this.homeService.loadUserInfo();
  }

  username = this.homeService.username
  email = this.homeService.email
  credit = this.homeService.userCredit
}
