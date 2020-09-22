#!/usr/bin/env bash

ROLE=`aws cloudformation describe-stacks --stack-name stack01 --query "Stacks[0].Outputs[?OutputKey=='alexaskillskitnodejsfactskillRole'].OutputValue" --output text`

echo "ROLE is ${ROLE}"

sam package \
  --template-file templates/template.yaml \
  --output-template-file package.yaml \
  --s3-bucket octank-news-translate-lambda

sam deploy \
  --template-file package.yaml \
  --stack-name octank-news-translate-lambda \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides ROLE=$ROLE 