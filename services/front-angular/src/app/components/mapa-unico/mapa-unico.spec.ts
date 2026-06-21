import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MapaUnico } from './mapa-unico';

describe('MapaUnico', () => {
  let component: MapaUnico;
  let fixture: ComponentFixture<MapaUnico>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MapaUnico],
    }).compileComponents();

    fixture = TestBed.createComponent(MapaUnico);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
