from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_logs as logs,
)
from constructs import Construct
import json

class TvSeriesRecommenderStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for series data
        data_bucket = s3.Bucket(
            self, "SeriesRecommenderData",
            bucket_name=f"tv-series-recommender-data-{self.account}-{self.region}",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # S3 bucket for the web UI
        web_ui_bucket = s3.Bucket(
            self, "TVSeriesWebUIBucket",
            bucket_name=f"tv-series-web-ui-{self.account}-{self.region}",
            website_index_document="index.html",
            public_read_access=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
        )

        # Lambda function
        lambda_function = _lambda.Function(
            self, "FetchSeriesRecommendationLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("src"),
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={
                "BUCKET_NAME": data_bucket.bucket_name,
            },
        )

        # Grant Lambda read access to the data bucket
        data_bucket.grant_read(lambda_function)

        # Define the HTTP API
        api = apigwv2.HttpApi(
            self, "TvSeriesRecommenderAPI",
            api_name="TvSeriesRecommenderAPI",
            description="API for searching TV series recommendations.",
            cors_preflight={
                "allow_origins": ["*"],
                "allow_headers": ["content-type", "authorization"],
                "allow_methods": [apigwv2.CorsHttpMethod.GET],
                "allow_credentials": False,
                "expose_headers": [],
                "max_age": Duration.seconds(3600),
            },
        )

        # Add /search route
        integration = apigwv2_integrations.HttpLambdaIntegration("SearchIntegration", lambda_function)
        api_route = api.add_routes(
            path="/search",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration,
        )

        # Ensure the deployment explicitly depends on the route
        deployment = apigwv2.CfnDeployment(
            self, "ApiDeployment",
            api_id=api.api_id,
        )
        deployment.node.add_dependency(api_route[0])

        # Add the stage with an explicit deployment
        stage = apigwv2.CfnStage(
            self, "APIDevStage",
            api_id=api.api_id,
            stage_name="dev",
            deployment_id=deployment.ref,
        )

        # Deploy JSON files to the data bucket
        s3_deployment.BucketDeployment(
            self, "DeploySeriesData",
            sources=[s3_deployment.Source.asset("series-data")],
            destination_bucket=data_bucket,
        )

        # Generate and deploy all web UI files including config.json
        s3_deployment.BucketDeployment(
            self, "DeployWebUIWithConfig",
            sources=[
                s3_deployment.Source.asset("web-ui"),  # Deploy all static files
                s3_deployment.Source.data(
                    "config.json",
                    json.dumps({"apiUrl": f"{api.api_endpoint}/dev/search"})  # Dynamically set /dev stage
                ),
            ],
            destination_bucket=web_ui_bucket,
        )

        # Output the default API Gateway URL
        CfnOutput(
            self, "ApiDefaultUrl",
            value=f"{api.api_endpoint}/dev",
        )
