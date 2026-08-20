import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Print } from './print';

describe('Print', () => {
  let component: Print;
  let fixture: ComponentFixture<Print>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Print],
    }).compileComponents();

    fixture = TestBed.createComponent(Print);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
