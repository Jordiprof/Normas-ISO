### README.md más detallado
Copia-pega en README.md: Expandido con instalación, uso, módulos, contribuciones y licencia.
```markdown
# Kit Cumplimiento ISO

Toolkit modular en Python para implementar y auditar normas ISO en apps full-stack (seguridad, calidad, usabilidad, accesibilidad, IA). Gratuito, open-source, enfocado en desarrollo seguro con LangChain, PyTorch y DBs (PostgreSQL/MySQL).

## Instalación
1. Clona el repo: `git clone <url>`.
2. Crea/activa venv: `python -m venv venv` y `.\venv\Scripts\Activate.ps1`.
3. Instala deps: `pip install -r requirements.txt` (o usa pyproject.toml para build).
4. Instala como paquete editable: `pip install -e .`.

## Uso
Importa módulos desde `kit_iso`:
```python
from kit_iso.seguridad import HerramientasSeguridad
from kit_iso.base_datos import BaseDatosSegura

# Ejemplo: Valida código
seg = HerramientasSeguridad()
errores = seg.analizar_codigo("password = '123'")  # Detecta secreto hardcoded

# Ejemplo: Conexión DB segura
db = BaseDatosSegura('postgres', 'localhost', 'user', 'pass', 'mydb')
db.almacenar_encriptado('users', 'email', 'test@example.com')