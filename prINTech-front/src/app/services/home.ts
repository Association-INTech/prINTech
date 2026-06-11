import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal, } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class HomeService {
  private readonly http = inject(HttpClient)
  private readonly ApiBase = '/api/v1'

  userCredit = signal<number | null>(null);
  active_printers = signal<number>(0);
  total_printers = signal<number>(67);
  username = signal<string>('John Doe');
  printers_status = signal<string>('Disponible');
  email = signal<string>('johndoe@gmail.com');
  is_active = signal<boolean>(true);
  queue_size = signal<number>(67);

  getActivePrinters(){
    this.http.get<Printer[]>(`${this.ApiBase}/printers/`)
    .subscribe(
      (res) => {
        this.total_printers.set(res.length)
        const active = res.filter( (stat) => stat.status == "UP").length
        this.active_printers.set(active)
        if (active == res.length){
          this.printers_status.set('Complet')
        } else {
          this.printers_status.set('Disponible')
        }
      }
    )
  }

  loadUserInfo(){
    this.http.get< User >(`${this.ApiBase}/user/me`)
    .subscribe(
      (res) => {
        this.username.set(res.username)
        this.email.set(res.email)
        this.userCredit.set(res.credit)
        this.is_active.set(res.is_active)
      }
    )
  }

GetQueue() {
    this.http.get<Request[]>(`${this.ApiBase}/requests/`)
    .subscribe(
      (res) => {
        // Filter out requests that are done, cancelled, or failed
        const inProgressRequests = res.filter(request => 
          request.status !== 'PICKED_UP' && 
          request.status !== 'CANCELED' && 
          request.status !== 'FAILED'
        );
        
        // Set the queue size to only show active requests
        this.queue_size.set(inProgressRequests.length);
      }
    );
  }  
}

export interface Printer {
  name: string,
  status: string,
}

export interface User {
  id: string,
  username: string,
  email: string,
  credit: number,
  is_active: boolean;

}

export interface Request{
  id: string,
  user: string,
  file: {
    path: string,
    number_of_printing: number,
    filament: number //weird as fuck
    para_slicer: string
  },
  printer: string,
  comment: string,
  created_at: Date,
  status: string,
}

// export interface Request{
//   id: string,
//   user: string,
//   file_path: string,
//   number: number,
//   filament: string,
//   comment: string,
//   created_at: Date,
//   status: string,
// }
