import aws_cdk as core
import aws_cdk.assertions as assertions

from tv_series_recommender.tv_series_recommender_stack import TvSeriesRecommenderStack

# example tests. To run these tests, uncomment this file along with the example
# resource in tv_series_recommender/tv_series_recommender_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = TvSeriesRecommenderStack(app, "tv-series-recommender")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
