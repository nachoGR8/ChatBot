import re
from main import SessionLocal, Business

def clean(s: str) -> str:
    if s is None:
        return ''
    # Remove control characters, replace with space
    s2 = re.sub(r'[\r\n\t\x0b\x0c]+', ' ', s)
    # Replace any other unicode whitespace sequences with single space
    s2 = re.sub(r'\s+', ' ', s2)
    return s2.strip()

def main():
    db = SessionLocal()
    try:
        businesses = db.query(Business).all()
        updated = 0
        for b in businesses:
            original = b.name or ''
            cleaned = clean(original)
            if cleaned != original:
                print(f"Actualizar id={b.id}: '{original}' -> '{cleaned}'")
                b.name = cleaned
                db.add(b)
                updated += 1
        if updated:
            db.commit()
        print(f"Hecho. Registros actualizados: {updated}")
    finally:
        db.close()

if __name__ == '__main__':
    main()
