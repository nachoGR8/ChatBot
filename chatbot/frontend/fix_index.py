#!/usr/bin/env python3
"""
Script para arreglar index.html con la función renderMarkdown correcta
"""

# La función correcta que funciona en demo.html
CORRECT_RENDER_MARKDOWN = '''        // Renderizador de Markdown
        function renderMarkdown(text) {
            let html = text;

            // Limpiar símbolos problemáticos del PDF
            html = html.replace(/■/g, '-');
            
            // PASO 1: Guardar tablas temporalmente (antes de procesar párrafos)
            const tables = [];
            
            // Regex más flexible que acepta tanto \\n como saltos de línea reales
            const tableRegex = /\\|(.+?)\\|[\\s\\r\\n]*\\|[\\s\\-:]+\\|[\\s\\r\\n]+((?:[\\s\\r\\n]*\\|.+?\\|[\\s\\r\\n]*)+)/g;
            
            html = html.replace(tableRegex, (match, header, rows) => {
                try {
                    const headerCells = header.split('|')
                        .map(cell => cell.trim())
                        .filter(cell => cell && !cell.match(/^[\\-:]+$/));
                    
                    const rowsArray = rows.trim().split('\\n')
                        .map(row => row.split('|')
                            .map(cell => cell.trim())
                            .filter(cell => cell)
                        )
                        .filter(row => row.length > 0 && !row.every(cell => cell.match(/^[\\s\\-:]+$/)));

                    if (headerCells.length === 0 || rowsArray.length === 0) return match;

                    let tableHtml = '<table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:0.85em;background:rgba(255,255,255,0.95);border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1)">';
                    
                    // Header
                    tableHtml += '<thead><tr style="background:linear-gradient(135deg, #6366f1, #8b5cf6);color:white;text-align:left;font-weight:600">';
                    headerCells.forEach(cell => {
                        tableHtml += `<th style="padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.2);white-space:nowrap">${cell}</th>`;
                    });
                    tableHtml += '</tr></thead>';

                    // Body
                    tableHtml += '<tbody>';
                    rowsArray.forEach((row, idx) => {
                        const bgColor = idx % 2 === 0 ? 'rgba(99,102,241,0.05)' : 'white';
                        tableHtml += `<tr style="background:${bgColor};transition:background 0.2s" onmouseover="this.style.background='rgba(99,102,241,0.1)'" onmouseout="this.style.background='${bgColor}'">`;
                        row.forEach((cell, cellIdx) => {
                            if (cellIdx < headerCells.length) {
                                tableHtml += `<td style="padding:10px 12px;border-bottom:1px solid rgba(0,0,0,0.05);color:#333">${cell}</td>`;
                            }
                        });
                        tableHtml += '</tr>';
                    });
                    tableHtml += '</tbody></table>';

                    // Guardar la tabla y reemplazar con un marcador
                    const placeholder = `__TABLE_${tables.length}__`;
                    tables.push(tableHtml);
                    return placeholder;
                } catch (e) {
                    console.error('Error rendering table:', e);
                    return match;
                }
            });

            // PASO 2: Limpiar pipes sueltos
            html = html.replace(/(\\|\\s*){5,}$/gm, '');

            // PASO 3: Bold
            html = html.replace(/\\*\\*(.+?)\\*\\*/g, '<strong style="color:#6366f1;font-weight:600">$1</strong>');

            // PASO 4: Listas
            html = html.replace(/^[\\*\\-] (.+)$/gm, '<li style="margin:4px 0;line-height:1.5">$1</li>');
            html = html.replace(/((?:<li[^>]*>.*?<\\/li>\\s*)+)/g, '<ul style="margin:8px 0;padding-left:20px;list-style-type:disc">$1</ul>');

            // PASO 5: Saltos de línea simples = <br>
            html = html.replace(/\\n/g, '<br>');

            // PASO 6: Restaurar las tablas
            tables.forEach((table, idx) => {
                html = html.replace(`__TABLE_${idx}__`, table);
            });

            return html;
        }'''

def fix_index_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Buscar donde empieza y termina renderMarkdown
    start_idx = None
    end_idx = None
    brace_count = 0
    
    for i, line in enumerate(lines):
        if 'function renderMarkdown(text)' in line:
            start_idx = i - 1  # Incluir el comentario anterior
            brace_count = 0
        elif start_idx is not None:
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '}' in line:
                end_idx = i + 1
                break
    
    if start_idx is None or end_idx is None:
        print("❌ No se encontró la función renderMarkdown")
        return False
    
    print(f"📍 Encontrada en líneas {start_idx + 1} - {end_idx + 1}")
    print(f"🗑️  Eliminando {end_idx - start_idx} líneas corruptas")
    
    # Reemplazar la sección
    new_lines = lines[:start_idx] + [CORRECT_RENDER_MARKDOWN + '\n'] + lines[end_idx:]
    
    # Guardar
    with open('index.html', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ Archivo arreglado! {len(lines)} → {len(new_lines)} líneas")
    return True

if __name__ == '__main__':
    fix_index_html()
