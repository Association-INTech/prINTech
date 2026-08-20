import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';

import { Home } from './home';
import { HomeService } from '../services/home';

describe('Home', () => {
  let component: Home;
  let fixture: ComponentFixture<Home>;
  const homeServiceMock = {
    userCredit: signal<number | null>(10),
    active_printers: signal(1),
    total_printers: signal(2),
    username: signal('alice'),
    printers_status: signal('Disponible'),
    email: signal('alice@example.com'),
    is_active: signal(true),
    queue_size: signal(0),
    loadUserInfo: vi.fn(),
    getActivePrinters: vi.fn(),
    GetQueue: vi.fn(),
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: HomeService, useValue: homeServiceMock },
      ],
      imports: [Home],
    }).compileComponents();

    fixture = TestBed.createComponent(Home);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
