import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'markdown'
})
export class MarkdownPipe implements PipeTransform {
  transform(value: string | undefined): string {
    if (!value) return '';
    
    // Convertir markdown básico a HTML
    let html = value;
    
    // Títulos
    html = html.replace(/^## (.*$)/gim, '<h2 class="text-2xl font-bold text-primary mt-8 mb-4">$1</h2>');
    html = html.replace(/^### (.*$)/gim, '<h3 class="text-xl font-bold text-primary mt-6 mb-3">$1</h3>');
    
    // Negritas
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Itálicas
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Listas
    html = html.replace(/^\- (.*$)/gim, '<li class="ml-4">$1</li>');
    html = html.replace(/^\* (.*$)/gim, '<li class="ml-4">$1</li>');
    
    // Párrafos
    html = html.replace(/\n\n/g, '</p><p class="mb-4">');
    html = '<p class="mb-4">' + html + '</p>';
    
    // Saltos de línea simples
    html = html.replace(/\n/g, '<br>');
    
    return html;
  }
}
