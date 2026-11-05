# ⚓ BATTLESHIP - Hundir la Flota
**Proyecto Final - Asignatura: Acceso a Datos**  
*Ciclo DAM2 (Desarrollo de Aplicaciones Multiplataforma) - CES Juan Pablo II*

---

## 🚀 Requisitos e Instalación

Para ejecutar este juego en cualquier ordenador (Windows, Linux o Mac), necesitas tener **Python 3.10 o superior**.

### 1. Clonar el repositorio
```bash
git clone https://github.com/JuanReifs/Hundir-la-flota-.git
cd Hundir-la-flota-
```

### 2. Crear y activar un entorno virtual (recomendado)

- **En Windows:**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate
  ```

- **En Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```
> **Nota importante:** Se utiliza `pygame-ce` (*Community Edition*) en lugar de la librería clásica `pygame` para garantizar compatibilidad total sin fallos con las versiones más recientes de Python (3.11, 3.12, 3.13 y 3.14).

### 4. Ejecutar el juego
```bash
python main.py
```

---

## 🛠️ Ejecución desde Entornos Visuales (IDEs)

### En PyCharm:
1. Abre la carpeta del proyecto en PyCharm (`File -> Open`).
2. Ve a **Settings / Preferences -> Project -> Python Interpreter**.
3. Añade o selecciona un intérprete (Virtualenv).
4. Abre la terminal integrada de PyCharm y ejecuta:
   ```bash
   pip install -r requirements.txt
   ```
5. Haz clic derecho sobre `main.py` y selecciona **Run 'main'**.

### En Visual Studio Code:
1. Abre la carpeta del proyecto en VS Code.
2. Pulsa `Ctrl+Shift+P` (o `Cmd+Shift+P` en Mac) y selecciona **Python: Select Interpreter**.
3. Selecciona tu intérprete de Python o el entorno `.venv`.
4. Abre la terminal (`Ctrl+ñ` o `Terminal -> New Terminal`) y ejecuta:
   ```bash
   pip install -r requirements.txt
   ```
5. Pulsa `F5` o ejecuta `python main.py`.

---

## 🧪 Ejecutar los Tests Unitarios
Para verificar que toda la lógica de flota, turnos y radar funciona correctamente:
```bash
python -m unittest test_juego.py -v
```

---

## 📁 Estructura del Proyecto
- `main.py`: Interfaz gráfica con Pygame (menús, combate, sprites y audio).
- `flota.py`: Generación aleatoria de barcos (10x10) y recepción de impactos.
- `ataques.py`: Registro de ataques al rival sin propagación automática.
- `pistas.py`: Radar probabilístico con modos Caza y Objetivo.
- `partida.py`: Controlador de la partida, turnos y persistencia en JSON.
- `constantes.py`: Constantes y reglas compartidas.
- `test_juego.py`: Tests unitarios.
- `requirements.txt`: Dependencias del proyecto.
