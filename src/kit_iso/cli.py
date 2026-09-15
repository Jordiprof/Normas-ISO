"""CLI de kit-iso.

kit-iso init [dir] [--detectar] [--perfil P] [--si] [--agentes a,b] [--ci] ...
kit-iso auditar <dir> [--formato json|markdown] [--salida ARCHIVO] [--config kit-iso.toml]
kit-iso skill [dir] [--agentes a,b] [--global]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from kit_iso import __version__, instalador, perfiles
from kit_iso._auditoria import ejecutar_auditoria, generar_markdown


def _print(texto: str) -> None:
    """Imprime en UTF-8 aunque el terminal Windows use cp1252."""
    try:
        print(texto)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(texto.encode("utf-8") + b"\n")


def _error(mensaje: str, codigo: int = 2) -> None:
    print(f"Error: {mensaje}", file=sys.stderr)
    sys.exit(codigo)


def _lista_agentes(valor: str) -> list[str]:
    if valor in ("", "todos"):
        return list(instalador.IDS_AGENTES)
    ids = [v.strip() for v in valor.split(",") if v.strip()]
    for id_ in ids:
        instalador.agente(id_)  # valida
    return ids


# ── init ──────────────────────────────────────────────────────────────────────


def _preguntar(texto: str, por_defecto: bool) -> bool:
    sugerido = "S/n" if por_defecto else "s/N"
    while True:
        try:
            resp = input(f"{texto} [{sugerido}] ").strip().lower()
        except EOFError:
            return por_defecto
        if resp == "":
            return por_defecto
        if resp in ("s", "si", "sí", "y", "yes"):
            return True
        if resp in ("n", "no"):
            return False


def _triaje(args: argparse.Namespace, raiz: Path) -> dict[str, perfiles.Respuesta]:
    if args.perfil:
        return perfiles.respuestas_de_perfil(args.perfil)

    propuestas = (
        perfiles.detectar(raiz)
        if args.detectar
        else {p.id: perfiles.Respuesta(False, "") for p in perfiles.PREGUNTAS}
    )
    if args.si:
        return {
            k: perfiles.Respuesta(v.valor, v.justificacion or "aceptado sin revisar (--si)")
            for k, v in propuestas.items()
        }

    return _confirmar_triaje(propuestas, mostrar_propuesta=args.detectar)


def _confirmar_triaje(
    propuestas: dict[str, perfiles.Respuesta], *, mostrar_propuesta: bool
) -> dict[str, perfiles.Respuesta]:
    """Pregunta cada punto del triaje; la justificación registra quién decidió."""
    _print("Triaje: responde a cada pregunta (Enter acepta la propuesta).\n")
    respuestas: dict[str, perfiles.Respuesta] = {}
    for p in perfiles.PREGUNTAS:
        prop = propuestas[p.id]
        if mostrar_propuesta:
            _print(
                f"  · {p.texto}\n    propuesta: {'sí' if prop.valor else 'no'} — {prop.justificacion}"
            )
        valor = _preguntar(f"  {p.texto}", prop.valor)
        if valor == prop.valor and prop.justificacion:
            just = prop.justificacion
        else:
            just = "confirmado por el responsable del proyecto"
        respuestas[p.id] = perfiles.Respuesta(valor, just)
    return respuestas


def cmd_init(args: argparse.Namespace) -> None:
    raiz = Path(args.directorio).resolve()
    if not raiz.is_dir():
        _error(f"'{raiz}' no es un directorio.")

    respuestas = _triaje(args, raiz)
    cfg = perfiles.Configuracion.desde_respuestas(
        respuestas,
        perfil=args.perfil or "personalizado",
        umbral_complejidad=args.umbral_complejidad,
        excluir=args.excluir,
    )

    if args.solo_mostrar:
        _print(perfiles.a_toml(cfg))
        return

    ruta_cfg = raiz / perfiles.NOMBRE_CONFIG
    if ruta_cfg.exists() and not args.forzar:
        # Idempotente: el triaje ya hecho se respeta; solo se refrescan skill, AGENTS.md y CI.
        cfg = perfiles.cargar(ruta_cfg)
        _print(f"· {ruta_cfg.name} ya existe: se conserva (usa --forzar para regenerarlo)")
    else:
        perfiles.guardar(cfg, ruta_cfg)
        _print(f"✔ {ruta_cfg.name}: módulos activos → {', '.join(cfg.modulos)}")
    if cfg.pendientes:
        _print(f"  ⚠ Normas necesarias aún no implementadas en el kit: {', '.join(cfg.pendientes)}")

    _instalar_integraciones(args, raiz)
    _print("\nSiguiente paso: `kit-iso auditar .`")


def _instalar_integraciones(args: argparse.Namespace, raiz: Path) -> None:
    """Skill para agentes, AGENTS.md/CLAUDE.md y workflow de CI (todo idempotente)."""
    if not args.sin_skill:
        for ruta in instalador.instalar_skill(raiz, _lista_agentes(args.agentes)):
            _print(f"✔ skill → {ruta.relative_to(raiz)}")
    if not args.sin_agents_md:
        instalador.instalar_agents_md(raiz)
        _print("✔ AGENTS.md: bloque kit-iso insertado")
        instalador.instalar_claude_md(raiz)
        _print("✔ CLAUDE.md: importa AGENTS.md")
    if args.ci:
        ruta_ci = instalador.instalar_workflow(raiz, forzar=args.forzar)
        if ruta_ci:
            _print(f"✔ CI → {ruta_ci.relative_to(raiz)}")
        else:
            _print("· CI: .github/workflows/kit-iso.yml ya existe (usa --forzar para regenerarlo)")


# ── auditar ───────────────────────────────────────────────────────────────────


def _cargar_config(
    directorio: Path, ruta_explicita: str | None
) -> tuple[Path | None, perfiles.Configuracion | None]:
    """Localiza y lee kit-iso.toml. Sale con código 2 si la ruta dada no existe o no es válida."""
    ruta = Path(ruta_explicita) if ruta_explicita else perfiles.localizar(directorio)
    if ruta is None:
        return None, None
    if not ruta.is_file():
        _error(f"'{ruta}' no existe.")
    try:
        return ruta, perfiles.cargar(ruta)
    except ValueError as e:
        _error(str(e))
        return None, None  # no se alcanza: _error hace sys.exit


def _emitir(resultados: dict, formato: str, salida: str | None) -> None:
    if formato == "json":
        texto = json.dumps(resultados, ensure_ascii=False, indent=2, default=str)
    else:
        texto = generar_markdown(resultados)
    if salida:
        Path(salida).write_text(texto, encoding="utf-8")
        print(f"Informe guardado en: {salida}")
    else:
        _print(texto)


def cmd_auditar(args: argparse.Namespace) -> None:
    directorio = Path(args.directorio)
    if not directorio.exists():
        _error(f"'{directorio}' no existe.")

    ruta_cfg, cfg = _cargar_config(directorio, args.config)

    # Flags explícitos de la CLI tienen prioridad sobre el toml.
    umbral = args.umbral_complejidad
    if umbral is None:
        umbral = cfg.umbral_complejidad if cfg else 10
    excluir = args.excluir or (cfg.excluir if cfg else None) or None

    resultados = ejecutar_auditoria(
        directorio,
        umbral_complejidad=umbral,
        excluir=excluir,
        modulos=cfg.modulos if cfg else None,
    )
    if cfg is not None:
        resultados["config"] = str(ruta_cfg)
        resultados["pendientes"] = cfg.pendientes

    _emitir(resultados, args.formato, args.salida)
    sys.exit(1 if resultados["resumen"]["fallidos"] > 0 else 0)


# ── skill ─────────────────────────────────────────────────────────────────────


def cmd_skill(args: argparse.Namespace) -> None:
    raiz = Path(args.directorio).resolve()
    rutas = instalador.instalar_skill(raiz, _lista_agentes(args.agentes), global_=args.global_)
    for r in rutas:
        _print(f"✔ skill → {r}")


# ── parser ────────────────────────────────────────────────────────────────────


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kit-iso",
        description="Controles técnicos automatizables para cumplimiento normativo.",
    )
    parser.add_argument("--version", action="version", version=f"kit-iso {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    # init
    p = sub.add_parser(
        "init",
        help="Triaje del proyecto: genera kit-iso.toml, instala la skill para agentes y AGENTS.md.",
    )
    p.add_argument("directorio", nargs="?", default=".", help="Raíz del proyecto (default: .)")
    p.add_argument(
        "--detectar",
        action="store_true",
        help="Pre-rellena el triaje con heurísticas sobre el proyecto y muestra la evidencia",
    )
    p.add_argument(
        "--perfil",
        choices=list(perfiles.PERFILES),
        help="Usa un perfil predefinido en vez de preguntar",
    )
    p.add_argument("--si", action="store_true", help="No pregunta: acepta las propuestas")
    p.add_argument(
        "--solo-mostrar",
        action="store_true",
        help="Imprime el kit-iso.toml resultante sin escribir nada",
    )
    p.add_argument(
        "--agentes",
        default="todos",
        metavar="LISTA",
        help=f"Agentes para los que instalar la skill, separados por coma "
        f"({', '.join(instalador.IDS_AGENTES)}; default: todos)",
    )
    p.add_argument("--sin-skill", action="store_true", help="No instala la skill")
    p.add_argument("--sin-agents-md", action="store_true", help="No toca AGENTS.md ni CLAUDE.md")
    p.add_argument("--ci", action="store_true", help="Crea .github/workflows/kit-iso.yml")
    p.add_argument("--forzar", action="store_true", help="Regenera kit-iso.toml y el workflow")
    p.add_argument("--umbral-complejidad", type=int, default=10, metavar="N")
    p.add_argument("--excluir", action="append", metavar="GLOB", default=[])
    p.set_defaults(func=cmd_init)

    # auditar
    p = sub.add_parser(
        "auditar",
        help="Ejecuta los controles activos en kit-iso.toml (o todos) y emite un informe.",
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
        "--config",
        metavar="TOML",
        help="Ruta a kit-iso.toml (default: se busca en el directorio y sus padres)",
    )
    p.add_argument(
        "--umbral-complejidad",
        type=int,
        default=None,
        metavar="N",
        help="Complejidad ciclomática máxima aceptable (default: la del toml o 10)",
    )
    p.add_argument(
        "--excluir",
        action="append",
        metavar="GLOB",
        default=[],
        help="Glob de rutas relativas a saltar (repetible): --excluir 'ejemplos/*'",
    )
    p.set_defaults(func=cmd_auditar)

    # skill
    p = sub.add_parser("skill", help="Instala la skill kit-iso para agentes de IA.")
    p.add_argument("directorio", nargs="?", default=".", help="Raíz del proyecto (default: .)")
    p.add_argument("--agentes", default="todos", metavar="LISTA")
    p.add_argument(
        "--global",
        dest="global_",
        action="store_true",
        help="Instala en la carpeta de usuario (~) en vez de en el proyecto",
    )
    p.set_defaults(func=cmd_skill)
    return parser


def main() -> None:
    args = _parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
