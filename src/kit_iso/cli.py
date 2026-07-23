"""CLI de kit-iso: `kit-iso auditar <directorio> [--formato json|markdown] [--salida ARCHIVO]`."""

import argparse
import json
import sys
from pathlib import Path

from kit_iso import __version__
from kit_iso._auditoria import ejecutar_auditoria, generar_markdown


def _print(texto: str) -> None:
    """Imprime en UTF-8 aunque el terminal Windows use cp1252."""
    try:
        print(texto)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(texto.encode("utf-8") + b"\n")


def cmd_auditar(args: argparse.Namespace) -> None:
    directorio = Path(args.directorio)
    if not directorio.exists():
        print(f"Error: '{directorio}' no existe.", file=sys.stderr)
        sys.exit(2)

    resultados = ejecutar_auditoria(
        directorio,
        umbral_complejidad=args.umbral_complejidad,
        excluir=args.excluir or None,
    )

    if args.formato == "json":
        texto = json.dumps(resultados, ensure_ascii=False, indent=2, default=str)
    else:
        texto = generar_markdown(resultados)

    if args.salida:
        Path(args.salida).write_text(texto, encoding="utf-8")
        print(f"Informe guardado en: {args.salida}")
    else:
        _print(texto)

    sys.exit(1 if resultados["resumen"]["fallidos"] > 0 else 0)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kit-iso",
        description="Controles técnicos automatizables para cumplimiento normativo.",
    )
    parser.add_argument("--version", action="version", version=f"kit-iso {__version__}")

    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser(
        "auditar",
        help="Ejecuta todos los controles sobre un directorio y emite un informe.",
    )
    p.add_argument("directorio", help="Directorio a auditar (p.ej. src/ o .)")
    p.add_argument(
        "--formato",
        choices=["markdown", "json"],
        default="markdown",
        help="Formato del informe (default: markdown)",
    )
    p.add_argument(
        "--salida",
        metavar="ARCHIVO",
        help="Guardar el informe en un archivo en vez de imprimirlo por stdout",
    )
    p.add_argument(
        "--umbral-complejidad",
        type=int,
        default=10,
        metavar="N",
        help="Complejidad ciclomática máxima aceptable (default: 10)",
    )
    p.add_argument(
        "--excluir",
        action="append",
        metavar="GLOB",
        default=[],
        help="Glob de rutas relativas a saltar (repetible): --excluir 'ejemplos/*' --excluir '*_demo.py'",
    )
    p.set_defaults(func=cmd_auditar)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
