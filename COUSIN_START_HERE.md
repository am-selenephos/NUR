# Start NUR

## Linux: one click

1. Extract the ZIP.
2. Open the `NUR` folder.
3. Double-click `START_NUR.desktop` and choose **Launch** if asked.
4. On first launch, enter your own OpenAI API key in the hidden prompt.
5. Wait for all health checks; NUR opens at `http://localhost:5173`.

Later launches use the same file and do not ask again.

## Terminal fallback

```bash
bash START_NUR.sh
```

## Stop or inspect

```bash
bash START_NUR.sh status
bash START_NUR.sh logs
bash START_NUR.sh stop
```

## Important

- The ZIP contains no OpenAI key.
- The key is stored only on the receiving computer in `.env.local` with mode 600.
- Real Talk refuses to fake an answer when OpenAI is not configured.
- Docker Engine/Desktop, Node.js, npm, Python 3, and PostgreSQL client tools are required.
