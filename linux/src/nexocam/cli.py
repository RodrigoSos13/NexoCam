import argparse
from threading import Event


def main():
    parser = argparse.ArgumentParser(description="NexoCam — fundação Linux")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("diagnostics", help="Verificar o ambiente sem modificá-lo")
    synthetic = sub.add_parser("synthetic", help="Enviar padrão real para v4l2loopback")
    synthetic.add_argument("--device", required=True)
    synthetic.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    if args.command == "diagnostics":
        from nexocam.diagnostics.environment import main as diagnostics

        return diagnostics()
    if args.command == "synthetic":
        if not 0 < args.seconds <= 3600:
            parser.error("--seconds deve estar entre 0 e 3600.")
        from nexocam.video.stream import run_pattern

        try:
            run_pattern(Event(), args.device, duration=args.seconds)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"Não foi possível iniciar a webcam: {exc}")
            return 1
        except KeyboardInterrupt:
            return 130
        return 0
    from nexocam.ui.window import launch

    return launch()
