# 🤝 Contribuyendo a Batan 3

¡Gracias por tu interés en contribuir al Sistema de Gestión Condominial Batan 3! 

## 🌟 Filosofía del Proyecto

Batan 3 busca simplificar la administración de condominios en Ecuador, proporcionando una herramienta tecnológica accesible, transparente y eficiente.

## 🚀 Cómo Contribuir

### 1. Reportar Problemas 🐞

- Usa GitHub Issues para reportar bugs
- Describe detalladamente el problema
- Incluye:
  - Versión del sistema
  - Pasos para reproducir
  - Mensaje de error completo
  - Captura de pantalla (si aplica)

### 2. Sugerir Mejoras ✨

- Abre un Issue con la etiqueta "enhancement"
- Explica claramente la mejora propuesta
- Describe el valor añadido para los usuarios

### 3. Contribuir con Código 💻

#### Configuración del Entorno

1. Haz fork del repositorio
2. Clona tu fork
```bash
git clone https://github.com/rtufino/batan3.git
cd batan3
```

3. Crea un entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Crea una rama para tu contribución
```bash
git checkout -b feature/nombre-de-tu-mejora
```

#### Guía de Estilo de Código

- Sigue PEP 8 para Python
- Usa type hints
- Escribe docstrings descriptivos
- Mantén la consistencia con el código existente

#### Pruebas

- Escribe pruebas unitarias para nuevas funcionalidades
- Asegúrate de que todas las pruebas pasen
```bash
python -m pytest
```

#### Commits

- Usa commits descriptivos
- Formato recomendado: `tipo(alcance): descripción`
  - Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Ejemplo: `feat(finanzas): agregar generación de PDF de estado de cuenta`

### 4. Pull Requests 🔀

1. Actualiza tu rama con el último `main`
```bash
git fetch origin
git rebase origin/main
```

2. Resuelve cualquier conflicto

3. Abre un Pull Request
- Describe los cambios
- Referencia issues relacionados
- Explica la motivación de los cambios

## 🛠 Desarrollo

### Herramientas Recomendadas

- Editor: VSCode, PyCharm
- Linter: flake8
- Formateador: black
- Gestor de dependencias: pip
- Base de datos: PostgreSQL 16

### Comandos Útiles

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar tests
python -m pytest

# Ejecutar linter
flake8 .

# Formatear código
black .
```

## 🌐 Localización

- El proyecto está en español
- Usa `gettext` para traducciones futuras
- Mantén consistencia en terminología

## 📋 Proceso de Revisión

- Un revisor verificará tu PR
- Se requiere al menos una revisión aprobatoria
- Se harán pruebas de integración
- Se verificará cobertura de código

## 🚫 Lo Que Evitar

- No incluyas archivos de configuración personal
- Evita cambios que rompan la compatibilidad
- No modifiques archivos de migración existentes sin consultar

## 📞 Contacto

- **Email**: rodrigo.tufio@gmail.com

## 💖 Código de Conducta

- Sé respetuoso
- Colabora constructivamente
- Acepta retroalimentación
- Mantén un ambiente inclusivo

---

**¡Gracias por hacer de Batan 3 un proyecto mejor!**