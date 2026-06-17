# meditacao-swarm

Pipeline de meditação católica diária e dominical — Python puro no Docker Swarm.

## Arquitetura

- **Scheduler**: APScheduler interno (zero race condition)
- **Coleta**: APIs matos-soares em paralelo (calendário, santos, bíblia)
- **IA**: DeepSeek Chat (deepseek-chat) com prompt patrístico
- **PDF**: WeasyPrint (diário) / ReportLab (dominical)
- **Entrega**: Telegram (chunked + PDF) + Markdown fallback
- **Persistência**: Baserow (tabela 828)

## Deploy

```bash
docker build -t meditacao-swarm:latest .
docker stack deploy -c meditacao.yml meditacao
```

## Health Check

`GET :8660/health` → `{"status":"ok","service":"meditacao"}`
