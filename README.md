```markdown
# 🧬 ROSN-LR5 – Kernel LPE PoC & Mitigation Toolkit (CVE-2026-31431)

<img width="5072" height="1536" alt="banner" src="https://raw.githubusercontent.com/ROSNLR5/MitigationToolkit-ROSN-LR5-Full/main/assets/poc-af_alg-exploit.png" />

Herramienta ofensiva y defensiva para la vulnerabilidad **CVE-2026-31431** en sistemas Linux.  
Combina una prueba de concepto de escalada local de privilegios (LPE) con utilidades para **revisar y mitigar temporalmente** el vector de ataque basado en AF_ALG.

> ⚖️ **USO ÉTICO EXCLUSIVO**: Este software se distribuye únicamente con fines educativos y de auditoría de seguridad. Solo debe ejecutarse en sistemas propios o sobre los que se tenga autorización explícita. El autor no se responsabiliza del mal uso.

---

## ✳️ Funcionalidades

### 🔥 Explotación LPE
- PoC completa que eleva privilegios a **root** mediante manipulación del socket AF_ALG.
- Inyección de payload con `os.splice()` y descompresión `zlib` sobre `/usr/bin/su`.
- Shell root persistente una vez completado el exploit.

### 🛡️ Mitigación
- **Revisión de estado del sistema**:
  - Disponibilidad y carga del módulo `algif_aead`.
  - Presencia del archivo de bloqueo en `/etc/modprobe.d/disable-algif.conf`.
  - Información del SO y kernel.
- **Aplicación de mitigación temporal** (requiere root):
  - Crea el archivo de bloqueo `install algif_aead /bin/false`.
  - Intenta descargar el módulo con `rmmod`.
  - Contención mientras se aplica el parche oficial del kernel.
- **Eliminación de la mitigación** (requiere root):
  - Borra el archivo de bloqueo para restaurar la carga normal del módulo.

### 🔍 Auditoría de privilegios
- Muestra UID, usuario, grupos y membresía en `sudo` o `wheel`.

---

## 🧪 Requisitos

- **Sistema operativo**: Linux (cualquier distribución con kernel potencialmente vulnerable).
- **Python**: 3.8 o superior.
- **Permisos**:
  - Explotación: solo requiere acceso de lectura a `/usr/bin/su`.
  - Mitigación (aplicar/quitar): necesita **root** (`sudo`).

---

## 📦 Instalación

Clona el repositorio y entra en el directorio:

```bash
git clone https://github.com/ROSNLR5/ROSN-LR5-Full.git
cd ROSN-LR5-Full
chmod +x rosnlr5_full.py
```

---

## 🚀 Uso

Ejecuta el script con Python 3:

```bash
python3 rosnlr5_full.py
```

El menú principal ofrece cuatro opciones:

1. **Auditar privilegios del usuario** – información básica de la sesión actual.
2. **Ejecutar exploit ROOT (CVE-2026-31431)** – lanza la PoC de escalada.
3. **Herramientas de mitigación** – submenú con revisión, aplicar y quitar mitigación.
4. **Acerca de** – créditos y descripción de la herramienta.

---

## 🔧 Submenú de mitigación

Dentro de la opción 3 encontrarás:

- **Revisar estado del sistema** – muestra si el módulo `algif_aead` está disponible/cargado y si existe el archivo de bloqueo.
- **Aplicar mitigación temporal** – crea `/etc/modprobe.d/disable-algif.conf` y descarga el módulo. Requiere `sudo`.
- **Quitar mitigación temporal** – elimina el archivo de bloqueo. Requiere `sudo`.
- **Volver al menú principal**.

---

## ⚠️ Aviso importante sobre la mitigación

La mitigación temporal **no reemplaza un parche de kernel**. Solo bloquea la carga del módulo vulnerable mientras se actualiza el sistema.  
Después de aplicar la mitigación, se recomienda actualizar el kernel con los parches oficiales de tu distribución.

---

## 👤 Créditos

- **Investigación original de la vulnerabilidad y PoC base**: Copyfile
- **Desarrollo del script y ampliación con herramientas de mitigación**: **ROSNLR5**

---

## 📜 Licencia

Este proyecto se distribuye sin licencia explícita. El código se proporciona "tal cual", sin garantías. El uso queda bajo tu propia responsabilidad y debes respetar las leyes locales.

---

*ROSN LR5 – entendiendo y conteniendo CVE 2026 31431*
```
