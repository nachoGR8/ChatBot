from main import SessionLocal, Business, FAQ, Conversation
from collections import defaultdict

def dedupe():
    db = SessionLocal()
    try:
        # Agrupar por nombre normalizado (trim + lower)
        businesses = db.query(Business).all()
        groups = defaultdict(list)
        for b in businesses:
            key = (b.name or '').strip().lower()
            groups[key].append(b)

        merged = 0
        for key, items in groups.items():
            if not key or len(items) < 2:
                continue
            # Elegir canonical: menor id
            items.sort(key=lambda x: x.id)
            canonical = items[0]
            duplicates = items[1:]
            print(f"Fusionando {len(duplicates)} duplicados en '{canonical.name}' (id={canonical.id})")
            for dup in duplicates:
                # mover FAQs
                faqs = db.query(FAQ).filter(FAQ.business_id == dup.id).all()
                for f in faqs:
                    f.business_id = canonical.id
                    db.add(f)
                # mover conversaciones
                convs = db.query(Conversation).filter(Conversation.business_id == dup.id).all()
                for c in convs:
                    c.business_id = canonical.id
                    db.add(c)
                # borrar el duplicado
                db.delete(dup)
                merged += 1
            db.commit()

        print(f"Dedupe completado. Registros fusionados: {merged}")
    finally:
        db.close()

if __name__ == '__main__':
    dedupe()
