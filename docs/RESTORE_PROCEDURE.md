# EsportsForge Database Restore Procedure

## SQLite (Development)
1. Stop the backend server
2. Copy backup file to `backend/esportsforge.db`
3. Restart the backend server

## PostgreSQL (Production)
1. Identify backup: `ls /tmp/esportsforge-backups/`
2. Create new database: `createdb esportsforge_restore`
3. Restore: `psql esportsforge_restore < backup_file.sql`
4. Verify: `psql esportsforge_restore -c "SELECT COUNT(*) FROM users;"`
5. Update DATABASE_URL to point to restored database
6. Restart application

## Recovery Objectives
- RTO (Recovery Time Objective): 2 hours
- RPO (Recovery Point Objective): 24 hours (daily backups)

## AWS S3 Backup (Production)
```bash
# Upload to S3
aws s3 cp backup.sql s3://esportsforge-backups/
# Download from S3
aws s3 cp s3://esportsforge-backups/[file] /tmp/restore.sql
```

Test this procedure quarterly.
