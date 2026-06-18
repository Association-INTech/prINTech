import { TestBed } from '@angular/core/testing';

import { Print } from './print';

describe('Print', () => {
  let service: Print;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Print);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
