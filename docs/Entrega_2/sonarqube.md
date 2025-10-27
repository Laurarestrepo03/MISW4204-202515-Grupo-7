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
<img width="1919" height="850" alt="Captura de pantalla 2025-10-26 201705" src="https://github.com/user-attachments/assets/3760dd81-8e40-4fd8-a9ab-3c8100affdc9" />

<img width="1919" height="852" alt="Captura de pantalla 2025-10-26 200837" src="https://github.com/user-attachments/assets/9187d3ea-6255-4963-a072-f0a5bc69f8cd" />

<img width="1919" height="847" alt="Captura de pantalla 2025-10-26 201630" src="https://github.com/user-attachments/assets/7991f1ff-5c0f-46be-9b95-b5257b3125ee" />

<img width="1919" height="851" alt="Captura de pantalla 2025-10-26 201644" src="https://github.com/user-attachments/assets/15472998-61d6-4f51-8df6-b69b5cc86cb9" />

<img width="1919" height="847" alt="Captura de pantalla 2025-10-26 201654" src="https://github.com/user-attachments/assets/011fb766-e6f1-4399-ad64-bd1b42481924" />


