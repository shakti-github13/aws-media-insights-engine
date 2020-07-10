# Requires a profile locally for the Media Insights account

# Profile = acg_media_insights

# Create Bucket
aws s3api create-bucket --bucket acg-media-insights-modelfiles --region us-east-1 --profile acg_media_insights

# Dry Run Copy Files
aws s3 sync --dryrun trainingfiles s3://acg-media-insights-modelfiles/comprehend/aws_services_entity_recogniser/trainingfiles --profile acg_media_insights
 
# Copy Files
aws s3 sync trainingfiles s3://acg-media-insights-modelfiles/comprehend/aws_services_entity_recogniser/trainingfiles --profile acg_media_insights

# Create a data access role which can access the training files
aws iam create-role --role-name acg_comprehend_s3_access_role --assume-role-policy-document file://trust_relationship.json --profile acg_media_insights
aws iam put-role-policy --role-name acg_comprehend_s3_access_role --policy-name S3Access --policy-document file://data_access_policy.json --profile acg_media_insights

# Create a training job to create a new entity recogniser
aws comprehend create-entity-recognizer \
     --language-code en \
     --recognizer-name AWS-Service-Recognizer  \
     --data-access-role-arn "arn:aws:iam::188417097137:role/acg_comprehend_s3_access_role" \
     --input-data-config "EntityTypes=[{Type=AWS_SERVICE}],Documents={S3Uri=s3://acg-media-insights-modelfiles/comprehend/aws_services_entity_recogniser/trainingfiles/},EntityList={S3Uri=s3://acg-media-insights-modelfiles/comprehend/aws_services_entity_recogniser/trainingfiles/awsservices.csv}" \
     --region us-east-1 --profile acg_media_insights


#Output: 
#arn:aws:comprehend:us-east-1:188417097137:entity-recognizer/AWS-Service-Recognizer

#How to include that in the stack as a stage of workflow?