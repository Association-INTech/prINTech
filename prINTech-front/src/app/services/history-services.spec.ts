import { TestBed } from '@angular/core/testing';

import { HistoryServices } from './history-services';

describe('HistoryServices', () => {
  let service: HistoryServices;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(HistoryServices);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
