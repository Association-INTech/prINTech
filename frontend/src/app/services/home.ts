import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal, computed} from '@angular/core';
import { Observable } from 'rxjs';
import { AuthService } from './auth';

@Injectable({
  providedIn: 'root',
})
export class HomeService {
  private readonly http = inject(HttpClient)
  private readonly authService = inject(AuthService);
  private readonly ApiBase = 'http://127.0.0.1:8000/api/v1'

  username = computed(() => this.authService.currentUser()?.username ?? 'John Doe');
  email = computed(() => this.authService.currentUser()?.email ?? 'johndoe@gmail.com');
  userCredit = computed(() => this.authService.currentUser()?.credit ?? null);

  active_printers = signal<number>(0);
  total_printers = signal<number>(67);
  printers_status = signal<string>('Disponible');
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

  getPrinters(): Observable<Printer[]> {
    return this.http.get<Printer[]>(`${this.ApiBase}/printers/`);
  }

  loadUserInfo(){
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
  id: number;
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
