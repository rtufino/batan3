# 🏢 Batan 3 - Sistema de Gestión Condominial

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.10+-blue)
![Flask Version](https://img.shields.io/badge/flask-3.1.2-green)
![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

## 🌟 Descripción del Proyecto

**Batan 3** es un sistema integral de gestión condominial desarrollado específicamente para edificios en Ecuador, diseñado para simplificar y optimizar la administración de condominios.

### 🎯 Objetivo Principal

Proporcionar una herramienta tecnológica que permita a administradores y juntas de condominio gestionar eficientemente:
- Finanzas
- Pagos de expensas
- Mantenimiento
- Comunicaciones
- Inventario

## ✨ Características Principales

### 💰 Gestión Financiera
- Registro detallado de ingresos y egresos
- Generación de estados de cuenta
- Control de pagos y deudas
- Reportes financieros personalizados

### 🏘️ Administración de Departamentos
- Registro y seguimiento de departamentos
- Control de ocupación (propietario/arrendatario)
- Gestión de alícuotas
- Notificaciones automáticas

### 🛠️ Mantenimiento
- Inventario de equipos
- Registro de mantenimientos
- Vinculación de gastos de mantenimiento
- Historial de reparaciones

### 📬 Notificaciones
- Envío automático de estados de cuenta
- Recordatorios de pagos
- Notificaciones por email
- Configuración personalizable

### ⚙️ Configuración Flexible
- Parámetros del sistema configurables
- Gestión de rubros de ingresos/egresos
- Administración de cuentas bancarias
- Registro de proveedores

## 🚀 Tecnologías Utilizadas

### Backend
- **Lenguaje**: Python 3.10+
- **Framework**: Flask 3.1.2
- **ORM**: SQLAlchemy
- **Base de Datos**: PostgreSQL 16

### Frontend
- **Templates**: Jinja2
- **Estilos**: Bootstrap 5.3.0
- **Iconografía**: Font Awesome
- **JavaScript**: ES6+

### Herramientas de Desarrollo
- Flask-Migrate (Alembic)
- Flask-WTF
- Flask-Mail
- python-dotenv

## 🔧 Instalación

### Requisitos Previos
- Sistema Operativo: Linux (Ubuntu/Debian) o macOS
- Python 3.10+ con pip y venv
- PostgreSQL 16
- Acceso a internet para instalación de dependencias

### Pasos de Instalación

1. Clonar el repositorio
```bash
git clone https://github.com/rtufino/batan3.git
cd batan3
```

2. Configurar entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install --upgrade pip
```

3. Instalar dependencias
```bash
pip install -r requirements.txt
```

4. Configurar base de datos PostgreSQL
```bash
# Crear base de datos
createdb batan3_db

# Configurar usuario (reemplazar con tus credenciales)
psql -U postgres
CREATE USER batan WITH PASSWORD 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE batan3_db TO batan;
```

5. Configurar variables de entorno
```bash
# Copiar ejemplo de configuración
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

6. Inicializar base de datos
```bash
# Aplicar migraciones
flask db upgrade

```

7. Ejecutar la aplicación
```bash
# Modo desarrollo
flask run --debug

# Modo producción (usar gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Configuración Docker (Opcional)
```bash
# Construir imagen
docker-compose build

# Levantar servicios
docker-compose up -d
```

## 📦 Estructura del Proyecto

```
batan3/
│
├── app/
│   ├── __init__.py
│   ├── models.py         # Modelos de datos
│   ├── routes/           # Rutas de la aplicación
│   ├── templates/        # Plantillas HTML
│   ├── static/           # Archivos estáticos
│   └── utils.py          # Funciones de utilidad
│
├── migrations/           # Migraciones de base de datos
├── tests/                # Pruebas unitarias
├── .env                  # Variables de entorno
├── config.py             # Configuraciones
├── run.py                # Punto de entrada
└── requirements.txt      # Dependencias
```

## 📊 Reportes

- Estado de cuenta PDF
- Historial de movimientos
- Reportes de gastos por categoría

## 🌐 Configuración Multilenguaje

- Soporte para español
- Fechas y montos localizados

## 🚧 Próximas Mejoras

- [ ] Autenticación de usuarios
- [ ] Control de roles y permisos
- [ ] Encriptación de contraseñas
- [ ] Protección contra CSRF
- [ ] Panel de administración avanzado
- [ ] Generación de gráficos financieros
- [ ] Módulo de reserva de áreas comunes

## 🤝 Contribuciones

1. Haz un fork del proyecto
2. Crea tu rama de características (`git checkout -b feature/nueva-caracteristica`)
3. Commitea tus cambios (`git commit -m 'Añadir nueva característica'`)
4. Sube tu rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

### Guía de Contribución

- Sigue el estilo de código PEP 8
- Escribe pruebas para nuevas funcionalidades
- Documenta los cambios en el README
- Mantén la compatibilidad con versiones anteriores

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## 📊 Métricas del Proyecto

![GitHub Stars](https://img.shields.io/github/stars/rtufino/batan3)
![GitHub Forks](https://img.shields.io/github/forks/rtufino/batan3)
![Contribuidores](https://img.shields.io/github/contributors/rtufino/batan3)

## 📞 Contacto

- **Organización:** Administración Batán III
- **Email:** edificio.batan3@gmail.com
- **Ubicación:** Quito, Ecuador 🇪🇨

## 🙏 Agradecimientos

- Comunidad de Flask
- Desarrolladores de librerías de código abierto
- Administradora que inspiro este proyecto

### Colaboradores Principales

- **Desarrollador Principal:** Rodrigo Tufiño
- **Diseñador UX/UI:** Rodrigo Tufiño
- **Consultor de Producto:** Mayra Araujo

### 🤖 Desarrollo Aumentado por IA (AI-Augmented)
Para optimizar la arquitectura, la lógica financiera y el flujo de trabajo, este proyecto integró capacidades avanzadas de co-creación con:
- **Modelos de Lenguaje:** Gemini (Google) y Claude (Anthropic).
- **Agente de Desarrollo:** RooCode (Extension para VS Code).

---

**Desarrollado con ❤️ para simplificar la administración condominial**

*Última actualización: Diciembre 2025*