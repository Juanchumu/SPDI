import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Healt } from './healt';

describe('Healt', () => {
  let component: Healt;
  let fixture: ComponentFixture<Healt>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Healt],
    }).compileComponents();

    fixture = TestBed.createComponent(Healt);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
