#!/usr/bin/env python3
"""
HTB Writeup Engine - Season 11
Author:St4r
Descripción: Motor unificado para gestión de writeups HTB con integración Obsidian.
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# ANSI Colors
# ─────────────────────────────────────────────
GREEN  = "\033[1;32m"
BLUE   = "\033[1;34m"
YELLOW = "\033[1;33m"
RED    = "\033[1;31m"
CYAN   = "\033[1;36m"
MAGENTA= "\033[1;35m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# ─────────────────────────────────────────────
# CONFIG - Persiste en disco
# ─────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".htb_helper_config.json"

DEFAULT_CONFIG = {
    "base_htb":       str(Path.home() / "HTB"),
    "writeups_dir":   str(Path.home() / "HTB" / "WRITEUPS"),
    "author":         "St4r",
    "season":         11,
    "obsidian_vault": "",           # ruta al vault de Obsidian (opcional)
    "open_after_gen": False,        # abrir automáticamente en nvim/nano
    "editor":         "nvim",       # editor para abrir el .md generado
}

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                # Mezcla con defaults para que campos nuevos aparezcan aunque el config sea viejo
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"{GREEN}[+] Configuración guardada en {CONFIG_FILE}{RESET}")

# ─────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────
def clear():
    os.system("clear")

def pause():
    input(f"\n{CYAN}[ Presiona Enter para continuar... ]{RESET}")

def print_ok(msg):   print(f"{GREEN}[+] {msg}{RESET}")
def print_info(msg): print(f"{BLUE}[*] {msg}{RESET}")
def print_warn(msg): print(f"{YELLOW}[!] {msg}{RESET}")
def print_err(msg):  print(f"{RED}[-] {msg}{RESET}")

def read_file(path: Path) -> str:
    """Lee un archivo de texto de forma segura."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception as e:
        return f"[Error al leer archivo: {e}]"

def cmd_available(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def check_dependencies() -> list[str]:
    return [c for c in ["pandoc", "xelatex"] if not cmd_available(c)]

def get_machines(base: Path, ignore=("WRITEUPS", "MARKDOWNS", "PDFS")) -> list[Path]:
    """Devuelve lista de directorios de máquinas, ordenada alfabéticamente."""
    if not base.exists():
        return []
    return sorted(
        [d for d in base.iterdir()
         if d.is_dir() and d.name not in ignore and not d.name.startswith(".")],
        key=lambda x: x.name.lower()
    )

def select_menu(items: list[Path], prompt: str, attr: str = "name") -> Path | None:
    """Menú de selección numerado con validación. Devuelve None si el usuario cancela."""
    if not items:
        print_err("No hay elementos disponibles.")
        return None

    print(f"\n{BLUE}{'─'*50}{RESET}")
    for i, item in enumerate(items):
        print(f"  {GREEN}[{i:2}]{RESET}  {getattr(item, attr)}")
    print(f"  {DIM}[ c]  Cancelar{RESET}")
    print(f"{BLUE}{'─'*50}{RESET}")

    raw = input(f"{YELLOW}{prompt}: {RESET}").strip().lower()
    if raw == "c":
        return None
    try:
        sel = int(raw)
        if 0 <= sel < len(items):
            return items[sel]
        print_err("Número fuera de rango.")
    except ValueError:
        print_err("Entrada inválida.")
    return None

def confirm(question: str, default: bool = False) -> bool:
    hint = "[S/n]" if default else "[s/N]"
    raw = input(f"{YELLOW}{question} {hint}: {RESET}").strip().lower()
    if not raw:
        return default
    return raw in ("s", "si", "sí", "y", "yes")

def init_paths(cfg: dict):
    """Crea los directorios base si no existen."""
    md_dir  = Path(cfg["writeups_dir"]) / "MARKDOWNS"
    pdf_dir = Path(cfg["writeups_dir"]) / "PDFS"
    md_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────
def banner(cfg: dict):
    season  = cfg.get("season", "?")
    author  = cfg.get("author", "?")
    base    = cfg.get("base_htb", "~/HTB")
    print(f"""{CYAN}
  ██╗  ██╗████████╗██████╗     ██╗  ██╗███████╗██╗     ██████╗ ███████╗██████╗
  ██║  ██║╚══██╔══╝██╔══██╗    ██║  ██║██╔════╝██║     ██╔══██╗██╔════╝██╔══██╗
  ███████║   ██║   ██████╔╝    ███████║█████╗  ██║     ██████╔╝█████╗  ██████╔╝
  ██╔══██║   ██║   ██╔══██╗    ██╔══██║██╔══╝  ██║     ██╔═══╝ ██╔══╝  ██╔══██╗
  ██║  ██║   ██║   ██████╔╝    ██║  ██║███████╗███████╗██║     ███████╗██║  ██║
  ╚═╝  ╚═╝   ╚═╝   ╚═════╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
{RESET}{DIM}  Season {season} · Autor: {author} · Base: {base}{RESET}
""")

# ─────────────────────────────────────────────
# OPCIONES DEL MENÚ
# ─────────────────────────────────────────────

# ── 1. INICIALIZAR MÁQUINA ──────────────────
def init_machine(cfg: dict):
    base = Path(cfg["base_htb"])
    print_info("Configurando nuevo entorno de laboratorio...\n")

    name = input(f"{YELLOW}Nombre de la máquina (ej. Reactor): {RESET}").strip()
    if not name:
        print_err("Nombre vacío. Cancelado.")
        return

    machine_path = base / name
    if machine_path.exists():
        print_warn(f"El directorio '{machine_path}' ya existe.")
        if not confirm("¿Continuar de todas formas?"):
            return

    folders = ["nmap", "content", "exploits", "scripts", "loot"]
    for folder in folders:
        (machine_path / folder).mkdir(parents=True, exist_ok=True)

    # Crear un notes.md inicial dentro de la carpeta de la máquina
    notes_file = machine_path / "notes.md"
    if not notes_file.exists():
        notes_file.write_text(
            f"# {name} - Notas de campo\n\n"
            "## To-Do\n- [ ] Enumeración\n- [ ] Explotación\n- [ ] Privesc\n\n"
            "## Credenciales encontradas\n| Usuario | Contraseña | Servicio |\n|---------|-----------|----------|\n| | | |\n\n"
            "## Puertos abiertos (resumen rápido)\n```\n\n```\n",
            encoding="utf-8"
        )
        print_ok(f"Creado notes.md en {machine_path}")

    print_ok(f"Estructura lista en: {machine_path}")
    print(f"\n{DIM}  Carpetas creadas: {', '.join(folders)} + notes.md{RESET}")


# ── 2. GENERAR MARKDOWN ─────────────────────
def _collect_section(folder: Path, label: str, code_exts: set, binary_msg: str) -> str:
    """Lee todos los archivos de una carpeta y genera sección Markdown."""
    if not folder.exists() or not any(folder.iterdir()):
        return f"\n> [!NOTE] No hay archivos en `/{folder.name}` todavía.\n"

    section = ""
    for f in sorted(folder.iterdir()):
        if not f.is_file():
            continue
        section += f"\n#### `{folder.name}/{f.name}`\n"
        ext = f.suffix.lower()
        if ext in code_exts:
            lang_map = {".py": "python", ".sh": "bash", ".ps1": "powershell",
                        ".js": "javascript", ".go": "go", ".c": "c", ".cpp": "cpp",
                        ".pl": "perl", ".rb": "ruby", ".json": "json",
                        ".xml": "xml", ".html": "html", ".yaml": "yaml",
                        ".yml": "yaml", ".txt": "text", ".csv": "text"}
            lang = lang_map.get(ext, "text")
            content = read_file(f)
            if content:
                section += f"```{lang}\n{content}\n```\n"
        else:
            section += f"*{binary_msg}*\n"
    return section


def generate_markdown(cfg: dict):
    base    = Path(cfg["base_htb"])
    md_dir  = Path(cfg["writeups_dir"]) / "MARKDOWNS"
    author  = cfg["author"]
    season  = cfg["season"]

    print_info(f"Escaneando laboratorios en {base}...")
    machines = get_machines(base)
    if not machines:
        print_err(f"No se encontraron máquinas en {base}")
        return

    selected = select_menu(machines, "Elige la máquina a procesar")
    if not selected:
        return

    name = selected.name
    print_info(f"Procesando: {name}\n")

    ip         = input(f"{YELLOW}IP del objetivo (Enter para dejar vacío): {RESET}").strip() or "X.X.X.X"
    os_target  = input(f"{YELLOW}OS (Linux/Windows): {RESET}").strip() or "Linux"
    difficulty = input(f"{YELLOW}Dificultad (Easy/Medium/Hard/Insane): {RESET}").strip() or "Medium"
    tags_raw   = input(f"{YELLOW}Tags Obsidian (ej: web, privesc — separados por coma): {RESET}").strip()
    tags       = ", ".join(f"#{t.strip()}" for t in tags_raw.split(",") if t.strip()) if tags_raw else "#htb"

    # Leer notas de campo si existen
    notes_md_path = selected / "notes.md"
    field_notes = read_file(notes_md_path) if notes_md_path.exists() else ""

    # Colecciones de archivos por carpeta
    text_exts = {".txt", ".json", ".xml", ".html", ".yaml", ".yml", ".csv",
                 ".js", ".py", ".sh", ".go", ".c", ".cpp", ".pl", ".rb", ".ps1"}
    code_exts = {".py", ".sh", ".js", ".go", ".pl", ".c", ".cpp", ".ps1", ".rb",
                 ".txt", ".json", ".xml", ".html", ".yaml", ".yml", ".csv"}

    nmap_section     = _collect_section(selected / "nmap",    "nmap",    text_exts,  "Archivo no legible como texto plano")
    content_section  = _collect_section(selected / "content", "content", text_exts,  "Archivo binario — adjuntar manualmente en Obsidian")
    exploits_section = _collect_section(selected / "exploits","exploits", code_exts, "Binario o extensión desconocida")
    scripts_section  = _collect_section(selected / "scripts", "scripts",  code_exts, "Binario o extensión desconocida")
    loot_section     = _collect_section(selected / "loot",    "loot",    text_exts,  "Archivo binario")

    # ── Plantilla Obsidian-friendly ──────────
    # Usa callouts nativos de Obsidian y placeholders de imagen claros
    date_str = datetime.now().strftime("%Y-%m-%d")
    md_content = f"""---
title: "HTB - {name}"
author: "{author}"
date: {date_str}
ip: "{ip}"
os: "{os_target}"
difficulty: "{difficulty}"
season: {season}
status: "en-progreso"
tags: [htb, season{season}, {os_target.lower()}, {difficulty.lower()}]
---

#[+]HTB[+] — {name}

| Campo | Valor |
|-------|-------|
| **IP** | `{ip}` |
| **OS** | {os_target} |
| **Dificultad** | {difficulty} |
| **Temporada** | {season} |
| **Fecha** | {date_str} |
| **Tags** | {tags} |

---

##  Resumen 

> [!SUMMARY] TL;DR
> _Completa este resumen al terminar la máquina._

---

##  Enumeración

### Reconocimiento de Red (Nmap / Fuzzing)

{nmap_section}

### Servicios y Hallazgos Relevantes

> [!INFO] Servicios detectados
> _Anota aquí los servicios y versiones relevantes encontrados._

<!-- Ejemplo de imágenes: arrastra tus capturas a Obsidian -->
<!-- ![[{name.lower()}_nmap.png]] -->

### Contenido y Evidencias (`/content`)

{content_section}

---

##  Explotación — User Flag

### Vectores de Ataque (`/exploits`)

{exploits_section}

> [!WARNING] Vector principal
> _Describe aquí el vector de entrada principal._

**User Flag:**
```
HTB{{AQUÍ_VA_EL_FLAG}}
```

<!-- Captura de la flag de usuario -->
<!-- ![[{name.lower()}_user_flag.png]] -->

---

##  Escalada de Privilegios — Root Flag

### Scripts de Post-Explotación (`/scripts`)

{scripts_section}

> [!WARNING] Técnica de escalada
> _Describe el vector de privesc utilizado._

**Root Flag:**
```
HTB{{AQUÍ_VA_EL_FLAG}}
```

<!-- Captura de la flag root -->
<!-- ![[{name.lower()}_root_flag.png]] -->

---

##  Loot y Credenciales

{loot_section}

| Usuario | Contraseña / Hash | Servicio | Válida |
|---------|------------------|----------|--------|
| | | | ☐ |

---

##  Notas de Campo

{field_notes if field_notes else "> [!NOTE]\\n> _Importado automáticamente desde notes.md. Completa aquí tus anotaciones._"}

---

##  Referencias

- [HTB Machine Page](https://app.hackthebox.com/machines/{name})
- _Añade aquí los recursos que usaste_

---
*Generado por HTB Helper Engine · {date_str}*
"""

    # Guardar en bóveda central
    dest_folder = md_dir / name
    dest_folder.mkdir(parents=True, exist_ok=True)
    md_file = dest_folder / f"{name.lower()}_writeup.md"

    # Advertir si ya existe
    if md_file.exists():
        print_warn(f"Ya existe un writeup para '{name}'.")
        if not confirm("¿Sobreescribir?", default=False):
            return

    md_file.write_text(md_content, encoding="utf-8")
    print_ok(f"Markdown exportado a:\n  {md_file}")

    # Copiar también al vault de Obsidian si está configurado
    vault = cfg.get("obsidian_vault", "")
    if vault:
        vault_path = Path(vault)
        if vault_path.exists():
            vault_dest = vault_path / f"HTB/{name}"
            vault_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, vault_dest / md_file.name)
            print_ok(f"Copiado al vault de Obsidian:\n  {vault_dest / md_file.name}")
        else:
            print_warn(f"Vault de Obsidian no encontrado: {vault}")

    # Abrir en editor si está configurado
    if cfg.get("open_after_gen") and cmd_available(cfg.get("editor", "nvim")):
        print_info(f"Abriendo en {cfg['editor']}...")
        subprocess.run([cfg["editor"], str(md_file)])


# ── 3. COMPILAR A PDF ────────────────────────
def compile_to_pdf(cfg: dict):
    missing = check_dependencies()
    if missing:
        print_err(f"Faltan dependencias: {', '.join(missing)}")
        print_warn("Instálalos con:\n  sudo apt update && sudo apt install pandoc texlive-xetex -y")
        return

    md_dir  = Path(cfg["writeups_dir"]) / "MARKDOWNS"
    pdf_dir = Path(cfg["writeups_dir"]) / "PDFS"

    print_info("Escaneando writeups disponibles...")
    machines = [d for d in sorted(md_dir.iterdir()) if d.is_dir()] if md_dir.exists() else []
    if not machines:
        print_err(f"No hay carpetas en {md_dir}")
        return

    selected = select_menu(machines, "Elige el writeup a compilar")
    if not selected:
        return

    md_files = list(selected.glob("*.md"))
    if not md_files:
        print_err(f"No se encontró ningún .md en {selected}")
        return

    src_md = md_files[0]
    dest_dir = pdf_dir / selected.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_pdf = dest_dir / f"{selected.name.lower()}_writeup.pdf"

    print_info(f"Compilando {src_md.name} → PDF...")

    cmd = [
        "pandoc", str(src_md),
        "-o", str(dest_pdf),
        "--pdf-engine=xelatex",
        "--highlight-style=breezedark",
        "--toc",
        "--toc-depth=3",
        "-V", "colorlinks=true",
        "-V", "linkcolor=cyan",
        "-V", "urlcolor=cyan",
        "-V", "geometry:margin=2cm",
        "-V", "fontsize=11pt",
        # Wrap largo de líneas de código
        "--include-in-header=-",
    ]

    latex_header = (
        r"\usepackage{fvextra}"
        r"\DefineVerbatimEnvironment{Highlighting}{Verbatim}"
        r"{commandchars=\\\{\},breaklines,breakanywhere}"
    )

    result = subprocess.run(
        cmd[:-1],  # Quitamos el "--include-in-header=-" y usamos el parámetro directamente
        input=latex_header,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(selected)
    )

    # Retry sin el header extra si falla (por si el sistema tiene pandoc viejo)
    if result.returncode != 0:
        simple_cmd = [
            "pandoc", str(src_md),
            "-o", str(dest_pdf),
            "--pdf-engine=xelatex",
            "--highlight-style=breezedark",
            "--toc",
            "-V", "colorlinks=true",
            "-V", "linkcolor=cyan",
            "-V", "geometry:margin=2cm",
        ]
        result = subprocess.run(
            simple_cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=str(selected)
        )

    if result.returncode == 0:
        print_ok(f"PDF generado exitosamente:\n  {dest_pdf}")
        size_kb = dest_pdf.stat().st_size // 1024
        print(f"{DIM}  Tamaño: {size_kb} KB{RESET}")
    else:
        print_err("Error de compilación Pandoc/LaTeX:")
        print(f"{DIM}{result.stderr[:1200]}{RESET}")


# ── 4. VER ESTADO DE MÁQUINAS ────────────────
def show_status(cfg: dict):
    base   = Path(cfg["base_htb"])
    md_dir = Path(cfg["writeups_dir"]) / "MARKDOWNS"
    pdf_dir= Path(cfg["writeups_dir"]) / "PDFS"

    machines = get_machines(base)
    if not machines:
        print_err(f"No hay máquinas en {base}")
        return

    print(f"\n{BLUE}{'─'*62}{RESET}")
    print(f"  {'Máquina':<20} {'Local':<8} {'Markdown':<12} {'PDF':<8}")
    print(f"{BLUE}{'─'*62}{RESET}")

    for m in machines:
        has_md  = any((md_dir / m.name).glob("*.md"))
        has_pdf = any((pdf_dir / m.name).glob("*.pdf"))

        local_ok = f"{GREEN}✓{RESET}" if m.exists() else f"{RED}✗{RESET}"
        md_ok    = f"{GREEN}✓{RESET}" if has_md  else f"{YELLOW}○{RESET}"
        pdf_ok   = f"{GREEN}✓{RESET}" if has_pdf else f"{YELLOW}○{RESET}"

        print(f"  {m.name:<20} {local_ok:<17} {md_ok:<21} {pdf_ok}")

    print(f"{BLUE}{'─'*62}{RESET}")
    print(f"{DIM}  ✓ Existe   ○ Pendiente{RESET}\n")


# ── 5. CONFIGURACIÓN ────────────────────────
def edit_config(cfg: dict) -> dict:
    print(f"\n{BLUE}Configuración actual:{RESET}")
    fields = [
        ("base_htb",       "Directorio base HTB"),
        ("writeups_dir",   "Directorio de writeups"),
        ("author",         "Nombre del autor"),
        ("season",         "Temporada HTB"),
        ("obsidian_vault", "Ruta al vault de Obsidian (vacío = no usar)"),
        ("editor",         "Editor para abrir .md (nvim, nano, code...)"),
        ("open_after_gen", "Abrir editor al generar Markdown (true/false)"),
    ]

    for key, label in fields:
        val = cfg.get(key, "")
        print(f"  {YELLOW}{label}{RESET}: {val}")

    print(f"\n{DIM}Deja vacío para mantener el valor actual.{RESET}")
    changed = False

    for key, label in fields:
        new_val = input(f"{YELLOW}{label} [{cfg.get(key,'')}]: {RESET}").strip()
        if new_val:
            if key == "open_after_gen":
                cfg[key] = new_val.lower() in ("true", "1", "sí", "si", "s", "y")
            elif key == "season":
                try:
                    cfg[key] = int(new_val)
                except ValueError:
                    print_warn("Valor inválido, se mantiene el anterior.")
            else:
                cfg[key] = new_val
            changed = True

    if changed:
        save_config(cfg)
    else:
        print_info("Sin cambios.")

    return cfg


# ── 6. LIMPIAR WORKSPACE ─────────────────────
def clean_workspace(cfg: dict):
    base = Path(cfg["base_htb"])
    machines = get_machines(base)
    if not machines:
        print_err("No hay máquinas disponibles.")
        return

    selected = select_menu(machines, "Elige la máquina a limpiar")
    if not selected:
        return

    print_warn(f"Esto BORRARÁ el contenido de las subcarpetas de: {selected.name}")
    print(f"{DIM}  (Las carpetas se recrean vacías; el notes.md se conserva){RESET}")
    if not confirm("¿Confirmar limpieza?", default=False):
        return

    folders = ["nmap", "content", "exploits", "scripts", "loot"]
    for folder in folders:
        folder_path = selected / folder
        if folder_path.exists():
            for f in folder_path.iterdir():
                if f.is_file():
                    f.unlink()
        else:
            folder_path.mkdir(parents=True, exist_ok=True)

    print_ok(f"Workspace de '{selected.name}' limpiado. Carpetas vacías recreadas.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    cfg = load_config()
    init_paths(cfg)

    while True:
        clear()
        banner(cfg)
        print(f"  {BLUE}[1]{RESET}  Inicializar entorno — nueva máquina")
        print(f"  {BLUE}[2]{RESET}  Generar Markdown (absorber datos locales → Obsidian)")
        print(f"  {BLUE}[3]{RESET}  Compilar Markdown → PDF profesional")
        print(f"  {BLUE}[4]{RESET}  Ver estado de máquinas")
        print(f"  {BLUE}[5]{RESET}  Limpiar workspace de una máquina")
        print(f"  {BLUE}[6]{RESET}  Configuración")
        print(f"  {RED}[0]{RESET}  Salir\n")

        try:
            choice = input(f"{YELLOW}Selección: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GREEN}[+] Salida. ¡Buena caza!{RESET}\n")
            sys.exit(0)

        match choice:
            case "1": init_machine(cfg)
            case "2": generate_markdown(cfg)
            case "3": compile_to_pdf(cfg)
            case "4": show_status(cfg)
            case "5": clean_workspace(cfg)
            case "6": cfg = edit_config(cfg)
            case "0":
                print(f"\n{GREEN}[+] ¡Hasta la próxima, {cfg['author']}!{RESET}\n")
                sys.exit(0)
            case _:
                print_err("Opción inválida.")

        pause()


if __name__ == "__main__":
    # Requiere Python 3.10+ por el match/case
    if sys.version_info < (3, 10):
        print(f"{RED}[-] Requiere Python 3.10 o superior.{RESET}")
        sys.exit(1)
    main()
