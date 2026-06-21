import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InformesDeRiesgo } from './informes-de-riesgo';

describe('InformesDeRiesgo', () => {
  let component: InformesDeRiesgo;
  let fixture: ComponentFixture<InformesDeRiesgo>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InformesDeRiesgo],
    }).compileComponents();

    fixture = TestBed.createComponent(InformesDeRiesgo);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
