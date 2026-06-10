import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MapaSectorizado } from './mapa-sectorizado';

describe('MapaSectorizado', () => {
  let component: MapaSectorizado;
  let fixture: ComponentFixture<MapaSectorizado>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MapaSectorizado],
    }).compileComponents();

    fixture = TestBed.createComponent(MapaSectorizado);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
