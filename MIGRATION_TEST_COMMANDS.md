# Migration Testing Commands

## Prerequisites

1. PostgreSQL instance running and accessible
2. `.env` file configured with database credentials
3. Python virtual environment activated
4. Alembic installed (`pip install alembic`)

## Current Configuration

```bash
# Database connection (from .env)
DATABASE_HOST=aws-1-us-east-2.pooler.supabase.com
DATABASE_PORT=6543
DATABASE_USERNAME=postgres.fmdnrdtqqouqbvekfalz
DATABASE_DBNAME=postgres
```

## Test Sequence (After Resolving Naming Conflict)

### Step 1: Check Current Migration Version

```bash
python -m alembic current
```

Expected output: Shows current migration revision ID

### Step 2: Apply All Migrations (Upgrade to Head)

```bash
python -m alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade h8c9d0e1f2a3 -> i9d0e1f2a3b4, create branches table
INFO  [alembic.runtime.migration] Running upgrade i9d0e1f2a3b4 -> j0e1f2a3b4c5, create terminals table
INFO  [alembic.runtime.migration] Running upgrade j0e1f2a3b4c5 -> k1f2a3b4c5d6, create sessions table
INFO  [alembic.runtime.migration] Running upgrade k1f2a3b4c5d6 -> l2a3b4c5d6e7, create assignments table
INFO  [alembic.runtime.migration] Running upgrade l2a3b4c5d6e7 -> m3b4c5d6e7f8, create closings table
```

### Step 3: Verify Tables Were Created

```bash
python check_tables.py
```

Expected output:
```
Checking for new tables:
  ✓ EXISTS: branches
  ✓ EXISTS: terminals
  ✓ EXISTS: sessions (or sales_sessions)
  ✓ EXISTS: assignments
  ✓ EXISTS: closings

Current Alembic version: m3b4c5d6e7f8
```

### Step 4: Test Rollback (Downgrade to Base)

```bash
python -m alembic downgrade base
```

Expected output:
```
INFO  [alembic.runtime.migration] Running downgrade m3b4c5d6e7f8 -> l2a3b4c5d6e7, drop closings table
INFO  [alembic.runtime.migration] Running downgrade l2a3b4c5d6e7 -> k1f2a3b4c5d6, drop assignments table
INFO  [alembic.runtime.migration] Running downgrade k1f2a3b4c5d6 -> j0e1f2a3b4c5, drop sessions table
INFO  [alembic.runtime.migration] Running downgrade j0e1f2a3b4c5 -> i9d0e1f2a3b4, drop terminals table
INFO  [alembic.runtime.migration] Running downgrade i9d0e1f2a3b4 -> h8c9d0e1f2a3, drop branches table
```

### Step 5: Verify Tables Were Dropped

```bash
python check_tables.py
```

Expected output:
```
Checking for new tables:
  ✗ MISSING: branches
  ✗ MISSING: terminals
  ✗ MISSING: sessions (or sales_sessions)
  ✗ MISSING: assignments
  ✗ MISSING: closings

Current Alembic version: h8c9d0e1f2a3
```

### Step 6: Test Idempotency (Upgrade Again)

```bash
python -m alembic upgrade head
```

Expected output: Same as Step 2 - all migrations should run successfully again

### Step 7: Final Verification

```bash
python check_tables.py
```

Expected output: Same as Step 3 - all tables should exist

## Additional Verification Queries

### Check Table Structures

```bash
# Branches table
python -c "from dotenv import load_dotenv; load_dotenv(); from app.configuration.database_connection import DatabaseConnection; from sqlalchemy import text; engine = DatabaseConnection._create_engine(); conn = engine.connect(); result = conn.execute(text('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ''branches'' ORDER BY ordinal_position')); print('\\n'.join([f'{r[0]}: {r[1]}' for r in result])); conn.close()"

# Terminals table
python -c "from dotenv import load_dotenv; load_dotenv(); from app.configuration.database_connection import DatabaseConnection; from sqlalchemy import text; engine = DatabaseConnection._create_engine(); conn = engine.connect(); result = conn.execute(text('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ''terminals'' ORDER BY ordinal_position')); print('\\n'.join([f'{r[0]}: {r[1]}' for r in result])); conn.close()"
```

### Check Foreign Key Constraints

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from app.configuration.database_connection import DatabaseConnection; from sqlalchemy import text; engine = DatabaseConnection._create_engine(); conn = engine.connect(); result = conn.execute(text('SELECT tc.table_name, tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name FROM information_schema.table_constraints AS tc JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name WHERE tc.constraint_type = ''FOREIGN KEY'' AND tc.table_name IN (''branches'', ''terminals'', ''sessions'', ''assignments'', ''closings'')')); print('\\n'.join([f'{r[0]}.{r[2]} -> {r[3]}.{r[4]}' for r in result])); conn.close()"
```

### Check Indexes

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from app.configuration.database_connection import DatabaseConnection; from sqlalchemy import text; engine = DatabaseConnection._create_engine(); conn = engine.connect(); result = conn.execute(text('SELECT tablename, indexname FROM pg_indexes WHERE schemaname = ''public'' AND tablename IN (''branches'', ''terminals'', ''sessions'', ''assignments'', ''closings'') ORDER BY tablename, indexname')); print('\\n'.join([f'{r[0]}: {r[1]}' for r in result])); conn.close()"
```

## Troubleshooting

### If migrations fail with "relation already exists"

This means a table wasn't properly cleaned up. Manually drop the table:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from app.configuration.database_connection import DatabaseConnection; from sqlalchemy import text; engine = DatabaseConnection._create_engine(); conn = engine.connect(); conn.execute(text('DROP TABLE IF EXISTS <table_name> CASCADE')); conn.commit(); conn.close()"
```

### If migrations fail with "foreign key constraint"

Check that referenced tables exist:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from app.configuration.database_connection import DatabaseConnection; from sqlalchemy import text; engine = DatabaseConnection._create_engine(); conn = engine.connect(); result = conn.execute(text('SELECT tablename FROM pg_tables WHERE schemaname = ''public'' AND tablename IN (''organizations'', ''users'') ORDER BY tablename')); print('\\n'.join([r[0] for r in result])); conn.close()"
```

### If connection fails

Verify environment variables are loaded:

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DATABASE_HOST:', os.getenv('DATABASE_HOST')); print('DATABASE_PORT:', os.getenv('DATABASE_PORT')); print('DATABASE_USERNAME:', os.getenv('DATABASE_USERNAME')); print('DATABASE_DBNAME:', os.getenv('DATABASE_DBNAME'))"
```

## Success Criteria

✅ All migrations run without errors  
✅ All 5 tables created (branches, terminals, sessions/sales_sessions, assignments, closings)  
✅ All foreign key constraints created  
✅ All indexes created  
✅ Downgrade removes all tables cleanly  
✅ Re-upgrade works (idempotency verified)  

## Notes

- The database is a **shared Supabase instance** with multiple services
- The `sessions` table naming conflict must be resolved before testing
- All migrations use PostgreSQL-specific features (UUID, gen_random_uuid(), etc.)
- Migrations are designed to be idempotent and reversible
