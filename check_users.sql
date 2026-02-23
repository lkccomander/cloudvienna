-- =========================================================
-- 1) GLOBALES (ejecutar en cualquier DB, por ejemplo postgres)
-- =========================================================

-- Roles y atributos globales
SELECT
  r.rolname,
  r.rolsuper,
  r.rolinherit,
  r.rolcreaterole,
  r.rolcreatedb,
  r.rolcanlogin,
  r.rolreplication,
  r.rolbypassrls,
  r.rolvaliduntil
FROM pg_roles r
ORDER BY r.rolname;

-- Membresías entre roles (quién pertenece a quién)
SELECT
  member.rolname   AS member_role,
  parent.rolname   AS granted_role,
  m.admin_option
FROM pg_auth_members m
JOIN pg_roles parent ON parent.oid = m.roleid
JOIN pg_roles member ON member.oid = m.member
ORDER BY member.rolname, parent.rolname;

-- Privilegios a nivel base de datos (CONNECT, CREATE, TEMP)
SELECT
  d.datname AS database_name,
  r.rolname AS role_name,
  has_database_privilege(r.rolname, d.datname, 'CONNECT') AS can_connect,
  has_database_privilege(r.rolname, d.datname, 'CREATE')  AS can_create,
  has_database_privilege(r.rolname, d.datname, 'TEMP')    AS can_temp
FROM pg_database d
CROSS JOIN pg_roles r
WHERE d.datistemplate = false
ORDER BY d.datname, r.rolname;
