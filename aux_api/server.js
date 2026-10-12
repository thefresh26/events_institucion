const app = require('./src/app');
const port = process.env.PORT || 4000;
app.listen(port, () => console.log(`API auxiliar escuchando en el puerto ${port}`));
