# Aiven PostgreSQL Setup Guide

## Why Use Aiven PostgreSQL?

### Benefits:
1. **Data Persistence**: Your data survives local PC shutdowns/restarts
2. **Automatic Backups**: Daily backups with point-in-time recovery
3. **High Availability**: 99.99% uptime SLA
4. **Security**: SSL/TLS encryption, firewall rules, VPC support
5. **Scalability**: Easy to upgrade resources as you grow
6. **Monitoring**: Built-in metrics and alerting
7. **Free Tier**: $300 free credits to start

### Current Local Setup Issues:
- ❌ Data lost when PC shuts down (unless PostgreSQL configured for persistence)
- ❌ No automatic backups
- ❌ Can't access from other machines
- ❌ Manual maintenance required

## Step-by-Step Setup

### 1. Create Aiven Account

1. Go to https://aiven.io
2. Sign up for free account
3. Get $300 in free credits (no credit card required initially)
4. Verify your email

### 2. Create PostgreSQL Service

1. Click "Create Service"
2. Select "PostgreSQL"
3. Choose plan:
   - **Hobbyist** (Free tier): 1 CPU, 1GB RAM, 5GB storage - Perfect for development
   - **Startup** ($25/month): 2 CPU, 4GB RAM, 80GB storage - Good for production
4. Select cloud provider: AWS, Google Cloud, or Azure
5. Select region: Choose closest to your location (e.g., us-east-1, eu-west-1)
6. Name your service: e.g., "voice-assistant-db"
7. Click "Create Service"
8. Wait 5-10 minutes for service to start

### 3. Get Connection Details

Once service is running:

1. Click on your service name
2. Go to "Overview" tab
3. Copy connection details:
   - **Host**: `your-service-name.aivencloud.com`
   - **Port**: `12345` (Aiven uses custom ports)
   - **Database**: `defaultdb`
   - **User**: `avnadmin`
   - **Password**: (shown in UI)
   - **SSL Mode**: `require`

4. Download SSL certificate:
   - Click "Download CA cert"
   - Save as `ca.pem` in your project root

### 4. Update .env File

Replace your local PostgreSQL settings:

```bash
# OLD - Local PostgreSQL
# DATABASE_URL=postgresql://madhavchaturvedi@localhost:5432/voice_automation

# NEW - Aiven PostgreSQL
DATABASE_URL=postgresql://avnadmin:YOUR_PASSWORD@your-service-name.aivencloud.com:12345/defaultdb?sslmode=require

# Alternative format (if using separate variables)
DB_HOST=your-service-name.aivencloud.com
DB_PORT=12345
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=YOUR_PASSWORD
DB_SSLMODE=require
```

**Important**: Replace:
- `YOUR_PASSWORD` with actual password from Aiven
- `your-service-name` with your actual service name

### 5. Update database.py (if needed)

Check if your database.py uses SSL properly:

```python
# In database.py - ensure SSL is configured
async def initialize_pool(self):
    """Initialize database connection pool."""
    try:
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=2,
            max_size=10,
            command_timeout=60,
            # SSL configuration for Aiven
            ssl='require'  # or ssl=True
        )
        print("✅ Connected to PostgreSQL database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        raise
```

### 6. Run Migrations

Run all migrations on the new Aiven database:

```bash
# Set environment variable
export DATABASE_URL="postgresql://avnadmin:YOUR_PASSWORD@your-service-name.aivencloud.com:12345/defaultdb?sslmode=require"

# Run migrations
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
psql "$DATABASE_URL" -f migrations/002_knowledge_base.sql
psql "$DATABASE_URL" -f migrations/003_company_description.sql

# Verify tables were created
psql "$DATABASE_URL" -c "\dt"
```

Expected output:
```
                List of relations
 Schema |       Name        | Type  |  Owner   
--------+-------------------+-------+----------
 public | appointments      | table | avnadmin
 public | business_config   | table | avnadmin
 public | call_analytics    | table | avnadmin
 public | calls             | table | avnadmin
 public | crm_sync_log      | table | avnadmin
 public | knowledge_base    | table | avnadmin
 public | leads             | table | avnadmin
 public | transcripts       | table | avnadmin
```

### 7. Test Connection

Test the connection from your application:

```bash
# Start your server
python3 main.py
```

Look for:
```
✅ Connected to PostgreSQL database
```

If you see connection errors, check:
- Password is correct
- SSL mode is set to `require`
- Firewall allows your IP (Aiven allows all IPs by default)

### 8. Migrate Existing Data (Optional)

If you have data in local PostgreSQL you want to keep:

```bash
# Export from local database
pg_dump -U madhavchaturvedi voice_automation > local_backup.sql

# Import to Aiven (remove CREATE DATABASE commands first)
sed '/CREATE DATABASE/d' local_backup.sql > aiven_import.sql
psql "$DATABASE_URL" -f aiven_import.sql
```

## Configuration Options

### Option 1: Single DATABASE_URL (Recommended)
```bash
DATABASE_URL=postgresql://avnadmin:password@host:port/defaultdb?sslmode=require
```

### Option 2: Separate Variables
```bash
DB_HOST=your-service-name.aivencloud.com
DB_PORT=12345
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=your_password
DB_SSLMODE=require
```

Then update database.py to build connection string:
```python
if os.getenv('DATABASE_URL'):
    self.connection_string = os.getenv('DATABASE_URL')
else:
    # Build from separate variables
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    name = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    sslmode = os.getenv('DB_SSLMODE', 'require')
    self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode={sslmode}"
```

## Security Best Practices

### 1. Use Environment Variables
Never commit credentials to git:
```bash
# .gitignore should include:
.env
ca.pem
*.pem
```

### 2. Rotate Passwords Regularly
In Aiven console:
1. Go to service → Users
2. Click on user → Reset password
3. Update .env file

### 3. Restrict IP Access (Optional)
In Aiven console:
1. Go to service → Overview
2. Scroll to "Allowed IP Addresses"
3. Add your IP addresses
4. Remove 0.0.0.0/0 (all IPs)

### 4. Use Connection Pooling
Already configured in database.py:
```python
min_size=2,
max_size=10,
```

## Monitoring & Maintenance

### View Metrics in Aiven Console
1. Go to your service
2. Click "Metrics" tab
3. Monitor:
   - CPU usage
   - Memory usage
   - Disk usage
   - Connection count
   - Query performance

### Set Up Alerts
1. Go to service → Integrations
2. Add email/Slack integration
3. Configure alerts for:
   - High CPU (> 80%)
   - High memory (> 80%)
   - High disk usage (> 80%)
   - Connection limit reached

### Backups
Aiven automatically backs up your database:
- **Frequency**: Every 24 hours
- **Retention**: 2 days (Hobbyist), 14 days (Startup+)
- **Point-in-time recovery**: Available on paid plans

To restore from backup:
1. Go to service → Backups
2. Select backup
3. Click "Fork" to create new service from backup

## Cost Estimation

### Free Tier (Hobbyist)
- **Cost**: $0 (uses free credits)
- **Resources**: 1 CPU, 1GB RAM, 5GB storage
- **Good for**: Development, testing, small projects
- **Credits**: $300 free credits last ~12 months

### Startup Plan
- **Cost**: ~$25/month
- **Resources**: 2 CPU, 4GB RAM, 80GB storage
- **Good for**: Production, 100-1000 calls/day
- **Backups**: 14 days retention

### Business Plan
- **Cost**: ~$100/month
- **Resources**: 4 CPU, 16GB RAM, 320GB storage
- **Good for**: High volume, 1000+ calls/day
- **Features**: High availability, read replicas

## Troubleshooting

### Connection Refused
```
Error: connection refused
```
**Solution**: Check if service is running in Aiven console

### SSL Error
```
Error: SSL connection required
```
**Solution**: Add `?sslmode=require` to connection string

### Authentication Failed
```
Error: password authentication failed
```
**Solution**: 
1. Verify password in Aiven console
2. Copy password exactly (no extra spaces)
3. Update .env file

### Timeout Errors
```
Error: connection timeout
```
**Solution**:
1. Check your internet connection
2. Verify firewall allows outbound connections on port 12345
3. Try different region if persistent

### Too Many Connections
```
Error: too many connections
```
**Solution**:
1. Check connection pool settings in database.py
2. Ensure connections are properly closed
3. Upgrade to larger plan if needed

## Migration Checklist

- [ ] Create Aiven account
- [ ] Create PostgreSQL service
- [ ] Copy connection details
- [ ] Download SSL certificate (if using file-based SSL)
- [ ] Update .env with new DATABASE_URL
- [ ] Test connection locally
- [ ] Run all migrations
- [ ] Verify tables created
- [ ] Test application functionality
- [ ] Migrate existing data (if any)
- [ ] Update production deployment
- [ ] Set up monitoring alerts
- [ ] Document credentials securely
- [ ] Remove local PostgreSQL dependency (optional)

## Comparison: Local vs Aiven

| Feature | Local PostgreSQL | Aiven PostgreSQL |
|---------|-----------------|------------------|
| Data Persistence | ❌ Lost on PC shutdown | ✅ Always available |
| Backups | ❌ Manual | ✅ Automatic daily |
| High Availability | ❌ Single point of failure | ✅ 99.99% uptime |
| Security | ⚠️ Local only | ✅ SSL, firewall, VPC |
| Monitoring | ❌ Manual | ✅ Built-in metrics |
| Scalability | ⚠️ Limited by PC | ✅ Easy upgrades |
| Cost | ✅ Free | ⚠️ $0-25/month |
| Setup | ✅ Quick | ⚠️ 10 minutes |
| Maintenance | ❌ Manual | ✅ Automatic |
| Access | ❌ Local only | ✅ From anywhere |

## Recommendation

**For Development**: Start with Aiven Hobbyist (free tier)
**For Production**: Use Aiven Startup plan ($25/month)

The free tier is perfect for development and testing. Once you're ready for production with real users, upgrade to Startup plan for better performance and longer backup retention.

## Next Steps

1. Create Aiven account and service (10 minutes)
2. Update .env file with new connection details
3. Run migrations
4. Test your application
5. Deploy to production

Your data will now persist across PC restarts and be professionally backed up!
