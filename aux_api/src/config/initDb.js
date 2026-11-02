// Crea las tablas ejecutando schema.sql:  npm run init-db   |   tablas + datos de ejemplo:  npm run seed
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
  // npm run seed -> usa script_mysql.sql (tablas + datos de ejemplo) sin las lineas CREATE DATABASE / USE,
  // para cargar los datos en la base que indique DB_NAME (la de la nube tiene otro nombre).
  const conDatos = process.argv.includes('--datos');
  let sql = fs.readFileSync(path.join(__dirname, '..', '..', conDatos ? 'script_mysql.sql' : 'schema.sql'), 'utf8');
  if (conDatos) sql = sql.split('\n').filter((l) => !/^\s*(CREATE DATABASE|USE)\b/i.test(l)).join('\n');
  await c.query(sql);
  const [t] = await c.query('SHOW TABLES');
  console.log('Tablas listas:', t.map((r) => Object.values(r)[0]).join(', '));
  await c.end();
})().catch((e) => { console.error(e.message); process.exit(1); });
