#!/bin/sh

DB_HOST="mysql"
DB_PORT="3306"

# Wait for MySQL server to be available
echo "Checking for MySQL server at $DB_HOST:$DB_PORT..."
until nc -z $DB_HOST $DB_PORT; do
  echo "Waiting for MySQL server at $DB_HOST:$DB_PORT..."
  sleep 1
done

echo "MySQL server at $DB_HOST:$DB_PORT is available, migrating the data"

# Run Prisma migration
npx prisma migrate dev --name init

echo "Starting the application...."

# Start the application
NODE_ENV=production npm run start 