// Crea las tablas ejecutando schema.sql:  npm run init-db
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');
const { ssl } = require('./dbConfig');

(async () => {
  const c = await mysql.createConnection({
    host: process.env.DB_HOST || 'localhost', port: Number(process.env.DB_PORT || 3306),
    user: process.env.DB_USER || 'root', password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'conexion_escolar_aux',
    ssl: ssl(),
    multipleStatements: true,
  });
  await c.query(fs.readFileSync(path.join(__dirname, '..', 'schema.sql'), 'utf8'));
  const [t] = await c.query('SHOW TABLES');
  console.log('Tablas listas:', t.map((r) => Object.values(r)[0]).join(', '));
  await c.end();
})().catch((e) => { console.error(e.message); process.exit(1); });
