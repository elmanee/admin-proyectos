# Conexión a TiDB Cloud

Estado: conexión verificada el 23/11/2026. El backend arrancó con el perfil tidb, validó el esquema y respondió HTTP 200 en /buscarProyectos. Contraseña guardada en .secrets/tidb.properties, excluida de Git.

## DBeaver

Crear una conexión de tipo **MariaDB** (compatible con el controlador actual del proyecto):

- Host: `gateway01.us-west-2.prod.aws.tidbcloud.com`
- Puerto: `4000`
- Base de datos: `dbgestor`
- Usuario: `3kUbuHArr2Cbpgi.root`
- Contraseña: la generada desde TiDB Cloud → Connect → Generate Password.
- En propiedades del controlador: `sslMode=verify-full` (TLS con validación del certificado y hostname).

Pulsar **Test Connection** antes de guardar. No desactivar la verificación TLS.

## Backend

Seleccionar en IntelliJ **Backend TiDB - Java 21**, detener primero la instancia local que ocupa 8081 y ejecutar esta configuración. El perfil `tidb` utiliza `.secrets/tidb.properties` para la contraseña privada. Esta carpeta está excluida de Git.

Alternativa desde la raíz de la API:

```powershell
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.profiles=tidb"
```

La configuración **Backend local - Java 21** conserva su conexión local. El frontend continúa usando `http://localhost:8081`.

TiDB contiene las seis tablas del dump, sin los registros personales antiguos. La tabla heredada hibernate_sequence se conserva para reflejar el esquema original; los identificadores de la aplicación actual usan IDENTITY.

