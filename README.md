
# Spatial Data Resource management framework
This is the repository for the SDR database code used by the Wildlife Conservation Society for urban historical 
ecology projects such as the Welikia Project. Example deployments include:  
project.sfb4.org  
data.shanghaiproject.org  
data.jerusalemproject.org
## Requirements
 - PostgreSQL database
 - AWS S3 for SDR files and database backups
 - Zotero group library
 - Docker for local development, Elastic Beanstalk for deployment
 - local development environment with Python and the fabric and dotenv libraries
 - AWS CLI installed in local development environment and an 'sdr' profile set up with the AWS credentials below
## Environment settings
The following (example) settings must be set either in a root .env file or in EB configuration:  
ENV=local  
DB_NAME=sdr  
DB_USER=postgres  
PGPASSWORD=postgres  
DB_PASSWORD=postgres  
DB_HOST=sdr_db  
DB_PORT=5432  
RESTORE=local  
BACKUP=local  
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE  
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY  
AWS_REGION=us-east-1  
AWS_BACKUP_BUCKET=\<S3 db backup bucket name string like shanghai-sdr-db-backups\>  
AWS_STORAGE_BUCKET_NAME=\<S3 SDR file bucket name string like shanghai-sdr-files\>  
ADMINS=email@domain.com,email2@domain.com  
SU_PASS=str0ngP@ssw0rdForDjangoSuperUser  
ALLOWED_HOSTS=\<comma-separated list for Django admin like .shanghaiproject.org\>  
PROJECT_NAME="The Shanghai Project"  
ZOTERO_GROUP=shanghai_historical_ecology  
DEFAULT_LAT=\<integer in "web Mercator" (EPSG ) meters, e.g. 3661290\>  
DEFAULT_LON=13488600  
DEFAULT_ZOOM=9