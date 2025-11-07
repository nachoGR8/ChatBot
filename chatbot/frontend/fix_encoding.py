#!/usr/bin/env python3
import re

# Leer archivo
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Remover los literales `n que insertó PowerShell
content = content.replace('`n', '\n')

# Fix 2: Arreglar el carácter corrupto
content = content.replace('/â– /g', '/■/g')
content = content.replace('sÃ­mbolos problemÃ¡ticos', 'símbolos problemáticos')
content = content.replace('pÃ¡rrafos', 'párrafos')
content = content.replace('mÃ¡s flexible', 'más flexible')
content = content.replace('lÃ­nea', 'línea')
content = content.replace('lÃ­nea', 'línea')

# Guardar
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo arreglado!")
