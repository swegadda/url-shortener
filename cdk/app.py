#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.url_shortener_stack import UrlShortenerStack

app = cdk.App()
stack = UrlShortenerStack(app, "UrlShortenerStack", env=cdk.Environment(region="ap-southeast-2"))
cdk.Tags.of(stack).add("auto-delete", "no")
app.synth()
