# Din kodbas

Lägg dina källkodsfiler här innan du indexerar eller ställer frågor.

## Snabbstart

1. Kopiera in din egen kodbas till den här mappen, **eller**
2. Testa med demo-projektet:
   ```bash
   # Windows (PowerShell)
   Copy-Item -Recurse test_project\* repo\

   # macOS / Linux
   cp -r test_project/. repo/
   ```

3. Bygg index och ställ frågor:
   ```bash
   python scripts/build_index.py --repo repo
   python scripts/ask.py "Var hanteras autentisering?"
   ```

## Docker

Med Docker monteras `./repo` automatiskt in i containern.
Lägg bara in din kod här och kör:

```bash
docker compose up --build
```

Om index saknas byggs det automatiskt från filerna i den här mappen.
