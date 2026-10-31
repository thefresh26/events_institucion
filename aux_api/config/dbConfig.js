require('dotenv').config();
const mysql = require('mysql2/promise');

// DB_SSL=true  -> SSL verificando el certificado (TiDB Cloud, Railway...)
// DB_SSL=insecure -> SSL sin verificar la CA (Aiven, que usa su propia CA)
function ssl() {
  if (process.env.DB_SSL === 'true') return { rejectUnauthorized: true };
  if (process.env.DB_SSL === 'insecure') return { rejectUnauthorized: false };
  return undefined;
}

// Pool de conexiones.
const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT || 3306),
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'conexion_escolar_aux',
  ssl: ssl(),
  waitForConnections: true,
  connectionLimit: 5,
  charset: 'utf8mb4',
  namedPlaceholders: false,
});

pool.ssl = ssl;
module.exports = pool;
