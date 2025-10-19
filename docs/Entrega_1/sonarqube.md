## Análisis de Calidad de Código con SonarCloud

El proyecto utiliza **SonarCloud** para análisis automático de calidad de código, detectando bugs, vulnerabilidades de seguridad, code smells y midiendo la cobertura de tests.

### 📊 Ver Reportes de SonarCloud

Puedes acceder a los reportes de calidad de código en:

**[https://sonarcloud.io/organizations/misw4204-202515-grupo-7/projects](https://sonarcloud.io/organizations/misw4204-202515-grupo-7/projects)**

O directamente al proyecto específico:

**[https://sonarcloud.io/project/overview?id=misw4204-202515-grupo-7](https://sonarcloud.io/project/overview?id=misw4204-202515-grupo-7)**

### 🔄 Análisis Automático

El análisis de SonarCloud se ejecuta **automáticamente** mediante GitHub Actions en los siguientes casos:

- ✅ Cada `push` a la rama `main` o `develop`
- ✅ Cada `pull request` (abierto, sincronizado o reabierto)

Después de cada push a `main`, se genera un nuevo reporte con las métricas actualizadas del proyecto, incluyendo:
- Bugs detectados
- Vulnerabilidades de seguridad
- Code smells (problemas de mantenibilidad)
- Cobertura de tests
- Duplicación de código