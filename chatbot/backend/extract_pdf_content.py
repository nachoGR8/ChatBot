import PyPDF2
import sys

pdf_path = r"C:\Users\nacho\Downloads\Gimnasio_FitZone_Empresa (1).pdf"

try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        print("=" * 80)
        print(f"CONTENIDO DEL PDF: {pdf_path}")
        print(f"Número de páginas: {len(pdf_reader.pages)}")
        print("=" * 80)
        
        for page_num in range(len(pdf_reader.pages)):
            print(f"\n{'='*80}")
            print(f"PÁGINA {page_num + 1}")
            print("=" * 80)
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            print(text)
            print()
            
except Exception as e:
    print(f"Error al leer el PDF: {e}")
