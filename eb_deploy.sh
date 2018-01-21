#!/bin/bash

# Warning: This script must be run from project root

ENV="sdr-dev-shanghai"
BUCKET="sdr-app-versions"

while getopts ":e:" opt; do
  case $opt in
    e)
      ENV=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

echo $ENV


echo "Creating archive..."
# Make sure to commit local changes first; this will create zip of latest commit, respecting .gitignore
git archive -o sdr.zip HEAD

STAMP=$(date +%Y%m%d%H%M%S)
COMMIT=`git rev-parse --verify HEAD`

echo "Uploading..."
aws s3 cp sdr.zip s3://$BUCKET/$ENV-$COMMIT-$STAMP.zip --profile=sdr

echo "Updating Elastic Beanstalk..."
aws elasticbeanstalk create-application-version --profile=sdr --application-name "sdr" \
    --version-label "$ENV-$COMMIT-$STAMP.zip" \
    --source-bundle S3Bucket="$BUCKET",S3Key="$ENV-$COMMIT-$STAMP.zip"

aws elasticbeanstalk update-environment --profile=sdr --environment-name "$ENV" \
    --version-label "$ENV-$COMMIT-$STAMP.zip"

echo "Cleaning up"
rm sdr.zip
cd ../
