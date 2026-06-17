"""Entry point — APScheduler + Health Check HTTP."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog
from config import HEALTH_PORT, TIMEZONE, CRON_DIARIO, CRON_DOMINICAL

logger = structlog.get_logger()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "meditacao"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silence HTTP logs


def job_diario():
    """Job APScheduler: meditação diária."""
    logger.info("job_diario_disparado")
    try:
        from pipeline import executar_pipeline
        executar_pipeline("diario")
    except Exception as e:
        logger.error("job_diario_falhou", error=str(e))


def job_dominical():
    """Job APScheduler: meditação dominical."""
    logger.info("job_dominical_disparado")
    try:
        from pipeline import executar_pipeline
        executar_pipeline("dominical")
    except Exception as e:
        logger.error("job_dominical_falhou", error=str(e))


def main():
    logger.info("meditacao_swarm_iniciando", timezone=TIMEZONE)

    # Iniciar health check HTTP
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    import threading
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    logger.info("health_check_ok", port=HEALTH_PORT)

    # Configurar scheduler
    scheduler = BackgroundScheduler(timezone=TIMEZONE)

    scheduler.add_job(
        job_diario,
        trigger=CronTrigger(
            day_of_week=CRON_DIARIO["day_of_week"],
            hour=CRON_DIARIO["hour"],
            minute=CRON_DIARIO["minute"],
        ),
        id="diario",
        name="Meditação Diária",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.add_job(
        job_dominical,
        trigger=CronTrigger(
            day_of_week=CRON_DOMINICAL["day_of_week"],
            hour=CRON_DOMINICAL["hour"],
            minute=CRON_DOMINICAL["minute"],
        ),
        id="dominical",
        name="Meditação Dominical",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()
    logger.info("scheduler_iniciado", jobs=["diario", "dominical"])

    # Loop eterno
    try:
        import signal
        signal.pause()
    except KeyboardInterrupt:
        logger.info("meditacao_swarm_encerrando")
        scheduler.shutdown()
        server.shutdown()


if __name__ == "__main__":
    main()
