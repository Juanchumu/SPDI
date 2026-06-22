import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InformeRiesgo } from './informe-riesgo';

describe('InformeRiesgo', () => {
  let component: InformeRiesgo;
  let fixture: ComponentFixture<InformeRiesgo>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InformeRiesgo],
    }).compileComponents();

    fixture = TestBed.createComponent(InformeRiesgo);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
