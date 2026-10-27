const app = require('./src/app');   // carga el .env (dotenv)
const port = process.env.PORT || 4000;

// Sin SECRET_KEY no se puede validar ningun JWT: mejor no arrancar que aceptar peticiones que siempre fallarian.
// Tambien se rechaza el valor de ejemplo de .env.example (una clave publica no protege nada).
const clave = (process.env.SECRET_KEY || '').trim();
if (!clave || clave === 'cambia-esto') {
  console.error('ERROR: falta SECRET_KEY (o tiene el valor de ejemplo "cambia-esto").\n'
    + 'Debe ser exactamente la misma SECRET_KEY de la API principal (FastAPI). Configúrala en el .env o en las variables de Render.');
  process.exit(1);
}

app.listen(port, () => console.log(`API auxiliar escuchando en el puerto ${port}`));
