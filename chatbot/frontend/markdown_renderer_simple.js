// RENDERIZADOR DE MARKDOWN SIMPLE - Usar este en vez del embebido
function renderMarkdownSimple(text) {
    let html = text;
    
    // Limpiar símbolos raros
    html = html.replace(/■/g, '-');
    
    // ESTRATEGIA: Procesar línea por línea
    const lines = html.split('\n');
    const result = [];
    let i = 0;
    
    while (i < lines.length) {
        const line = lines[i];
        
        // ¿Es inicio de tabla? (tiene pipes y siguiente línea tiene ---)
        if (line.includes('|') && i + 1 < lines.length && lines[i + 1].includes('---')) {
            // Construir tabla
            const headerLine = line;
            const sepLine = lines[i + 1];
            i += 2; // Saltar header y separador
            
            const headerCells = headerLine.split('|').map(c => c.trim()).filter(c => c);
            const tableRows = [];
            
            // Recoger filas de datos
            while (i < lines.length && lines[i].includes('|')) {
                const cells = lines[i].split('|').map(c => c.trim()).filter(c => c);
                if (cells.length > 0) tableRows.push(cells);
                i++;
            }
            
            // Generar HTML de tabla
            let tableHtml = '<table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:0.85em;background:white;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1)">';
            
            // Header
            tableHtml += '<thead><tr style="background:linear-gradient(135deg, #6366f1, #8b5cf6);color:white">';
            headerCells.forEach(cell => {
                tableHtml += `<th style="padding:10px 12px">${cell}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';
            
            // Rows
            tableRows.forEach((row, idx) => {
                const bg = idx % 2 === 0 ? 'rgba(99,102,241,0.05)' : 'white';
                tableHtml += `<tr style="background:${bg}">`;
                row.forEach(cell => {
                    tableHtml += `<td style="padding:10px 12px">${cell}</td>`;
                });
                tableHtml += '</tr>';
            });
            
            tableHtml += '</tbody></table>';
            result.push(tableHtml);
        } else {
            // Línea normal
            result.push(line);
            i++;
        }
    }
    
    html = result.join('\n');
    
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong style="color:#6366f1;font-weight:600">$1</strong>');
    
    // Listas
    html = html.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\s*)+)/g, '<ul style="margin:8px 0;padding-left:20px">$1</ul>');
    
    // Saltos de línea
    html = html.replace(/\n/g, '<br>');
    
    return html;
}
