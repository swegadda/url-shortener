from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Duration,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct
import os


class UrlShortenerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # --- DynamoDB Table ---
        url_table = dynamodb.Table(
            self,
            "UrlTable",
            table_name="url-shortener-urls",
            partition_key=dynamodb.Attribute(
                name="short_code", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # --- Lambda Functions ---
        lambda_dir = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")

        create_fn = _lambda.Function(
            self,
            "CreateFunction",
            function_name="url-shortener-create",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(os.path.join(lambda_dir, "create")),
            environment={"TABLE_NAME": url_table.table_name},
            timeout=Duration.seconds(10),
            memory_size=256,
        )

        redirect_fn = _lambda.Function(
            self,
            "RedirectFunction",
            function_name="url-shortener-redirect",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(os.path.join(lambda_dir, "redirect")),
            environment={"TABLE_NAME": url_table.table_name},
            timeout=Duration.seconds(10),
            memory_size=256,
        )

        analytics_fn = _lambda.Function(
            self,
            "AnalyticsFunction",
            function_name="url-shortener-analytics",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(os.path.join(lambda_dir, "analytics")),
            environment={"TABLE_NAME": url_table.table_name},
            timeout=Duration.seconds(10),
            memory_size=256,
        )

        # Grant DynamoDB permissions
        url_table.grant_read_write_data(create_fn)
        url_table.grant_read_write_data(redirect_fn)
        url_table.grant_read_data(analytics_fn)

        # --- API Gateway ---
        api = apigw.RestApi(
            self,
            "UrlShortenerApi",
            rest_api_name="url-shortener-api",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type"],
            ),
        )

        # Set BASE_URL so create Lambda returns full short URLs
        create_fn.add_environment(
            "BASE_URL",
            f"https://{api.rest_api_id}.execute-api.{self.region}.amazonaws.com/prod",
        )

        # POST /create
        create_resource = api.root.add_resource("create")
        create_resource.add_method(
            "POST", apigw.LambdaIntegration(create_fn)
        )

        # GET /{short_code} - redirect
        redirect_resource = api.root.add_resource("{short_code}")
        redirect_resource.add_method(
            "GET", apigw.LambdaIntegration(redirect_fn)
        )

        # GET /analytics and GET /analytics/{short_code}
        analytics_resource = api.root.add_resource("analytics")
        analytics_resource.add_method(
            "GET", apigw.LambdaIntegration(analytics_fn)
        )
        analytics_detail = analytics_resource.add_resource("{short_code}")
        analytics_detail.add_method(
            "GET", apigw.LambdaIntegration(analytics_fn)
        )

        # --- S3 Bucket for Frontend ---
        frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # --- CloudFront Distribution ---
        distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    frontend_bucket
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
        )

        # --- Deploy Frontend to S3 ---
        frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

        s3deploy.BucketDeployment(
            self,
            "DeployFrontend",
            sources=[s3deploy.Source.asset(frontend_dir)],
            destination_bucket=frontend_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        # --- Outputs ---
        CfnOutput(self, "ApiUrl", value=api.url, description="API Gateway URL")
        CfnOutput(
            self,
            "CloudFrontUrl",
            value=f"https://{distribution.distribution_domain_name}",
            description="CloudFront Distribution URL",
        )
        CfnOutput(
            self,
            "DynamoDBTable",
            value=url_table.table_name,
            description="DynamoDB Table Name",
        )
