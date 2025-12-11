import argparse
import subprocess
import sys
from pathlib import Path


def ensure_pip() -> None:
    """Verifica que pip existe; intenta bootstrapping si falta."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:  # pip fallo de forma inesperada
        raise SystemExit(f"[ERROR] pip no responde correctamente: {exc}") from exc
    except FileNotFoundError:
        import ensurepip

        ensurepip.bootstrap()
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, stdout=subprocess.DEVNULL)


def collect_packages(dist_dir: Path, libs_dir: Path):
    lib_wheels = sorted(libs_dir.glob("*.whl")) if libs_dir.exists() else []
    dist_wheels = sorted(dist_dir.glob("*.whl")) if dist_dir.exists() else []
    return lib_wheels, dist_wheels


def install(args):
    script_dir = Path(__file__).resolve().parent  # aqui vive el script
    dist_dir = Path(args.dist).resolve() if args.dist else script_dir
    libs_dir = Path(args.libs).resolve() if args.libs else script_dir / "libs"

    print("=== Instalador MCP_GLPI ===")
    print("Este script instalara todas las dependencias locales necesarias.")
    input("Presiona Enter para continuar...")

    if not dist_dir.exists():
        raise SystemExit(f"[ERROR] Carpeta dist no encontrada: {dist_dir}")

    ensure_pip()

    lib_wheels, dist_wheels = collect_packages(dist_dir, libs_dir)

    if libs_dir.exists() and lib_wheels:
        print(f"Instalando dependencias desde {libs_dir} ...")
        cmd = [sys.executable, "-m", "pip", "install", "--no-index", "--find-links", str(libs_dir), "--upgrade"]
        cmd.extend(str(p) for p in lib_wheels)
        subprocess.run(cmd, check=True)
    elif libs_dir.exists():
        print(f"[INFO] No se encontraron wheels en {libs_dir}. Se continua.")
    else:
        print(f"[WARN] Carpeta libs no encontrada: {libs_dir}. Se omite.")

    if not dist_wheels:
        raise SystemExit(f"[ERROR] No hay archivos .whl en {dist_dir}.")

    print(f"Instalando paquetes desde {dist_dir} ...")
    find_links = ["--find-links", str(libs_dir)] if libs_dir.exists() else []
    cmd = [sys.executable, "-m", "pip", "install", "--no-index", *find_links, "--upgrade"]
    cmd.extend(str(p) for p in dist_wheels)
    subprocess.run(cmd, check=True)

    print("Listo.")


def main():
    parser = argparse.ArgumentParser(description="Instala paquetes locales desde dist/ (solo .whl) y opcionalmente libs/ sin internet.")
    parser.add_argument("--dist", help="Carpeta con los paquetes principales (.whl). Default: carpeta donde esta el script.")
    parser.add_argument("--libs", help="Carpeta con wheels de dependencias. Default: libs/ al lado del script.")
    args = parser.parse_args()
    install(args)


if __name__ == "__main__":
    main()
