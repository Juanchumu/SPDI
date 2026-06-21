import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-alerta-dialog',
  standalone: true,
  imports: [
    MatDialogModule,
    MatButtonModule
  ],
  templateUrl: './mensaje-alerta.html'
})
export class MensajeAlerta {
  constructor(
    public dialogRef: MatDialogRef<MensajeAlerta>,
    @Inject(MAT_DIALOG_DATA) public data: { titulo: string; mensaje: string }
  ) {}

  aceptar(): void {
    this.dialogRef.close(true);
  }
}

