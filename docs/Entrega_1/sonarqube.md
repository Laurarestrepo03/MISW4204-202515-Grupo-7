## Análisis de Calidad de Código con SonarCloud - Entrega 2

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

  ## Pantallazos del reporte
  <img width="3289" height="1745" alt="image" src="https://github.com/user-attachments/assets/5eeaaae7-0830-4046-806d-95d78c2f13f8" />

  <img width="3302" height="1806" alt="image" src="https://github.com/user-attachments/assets/550be5ed-cce5-4fca-9a8e-e9a9e168616e" />

  <img width="3223" height="1747" alt="image" src="https://github.com/user-attachments/assets/41f1ef1a-3062-43ec-9a7a-29088a64bc66" />

  <img width="3157" height="1708" alt="image" src="https://github.com/user-attachments/assets/69ed0123-dbbc-439f-ab70-efde02280c58" />


