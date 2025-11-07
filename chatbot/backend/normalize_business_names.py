from main import SessionLocal, Business

def normalize_name(s: str) -> str:
    if s is None:
        return ''
    # Replace any whitespace sequence (including newlines) with single space and trim
    return ' '.join(s.split()).strip()

def main():
    db = SessionLocal()
    try:
        businesses = db.query(Business).all()
        updated = 0
        for b in businesses:
            clean = normalize_name(b.name)
            if clean != (b.name or ''):
                print(f"Actualizando id={b.id}: '{b.name}' -> '{clean}'")
                b.name = clean
                db.add(b)
                updated += 1
        if updated:
            db.commit()
        print(f"Normalización completada. Registros actualizados: {updated}")
    finally:
        db.close()

if __name__ == '__main__':
    main()
