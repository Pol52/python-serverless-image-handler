// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Construct, CfnParameter } from "@aws-cdk/core";
import * as cdkLambda from '@aws-cdk/aws-lambda';
import * as cdkS3 from '@aws-cdk/aws-s3';
import * as cdkIam from '@aws-cdk/aws-iam';
import * as cdk from '@aws-cdk/core';
import * as cdkCloudFront from '@aws-cdk/aws-cloudfront';
import * as cdkApiGateway from '@aws-cdk/aws-apigateway';
import * as cdkLogs from '@aws-cdk/aws-logs';
import { CloudFrontToApiGatewayToLambda } from '@aws-solutions-constructs/aws-cloudfront-apigateway-lambda';
import { CloudFrontToS3 } from '@aws-solutions-constructs/aws-cloudfront-s3';
import apiBody from './api.json';

const { BUCKET_NAME, SOLUTION_NAME, VERSION } = process.env;

/**
 * Serverless Image Handler props interface
 * These props are AWS CloudFormation parameters.
 */
export interface ServerlessImageHandlerProps {
  readonly corsEnabledParameter: CfnParameter;
  readonly corsOriginParameter: CfnParameter;
  readonly sourceBucketsParameter: CfnParameter;
  readonly logRetentionPeriodParameter: CfnParameter;
  readonly autoWebPParameter: CfnParameter;
  readonly enableSignatureParameter: CfnParameter;
  readonly secretsManagerParameter: CfnParameter;
  readonly secretsManagerKeyParameter: CfnParameter;
  readonly enableDefaultFallbackImageParameter: CfnParameter;
  readonly fallbackImageS3BucketParameter: CfnParameter;
  readonly fallbackImageS3KeyParameter: CfnParameter;
}

/**
 * Serverless Image Handler custom resource config interface
 */
interface CustomResourceConfig {
  readonly properties?: { path: string, value: any }[];
  readonly condition?: cdk.CfnCondition;
  readonly dependencies?: cdk.CfnResource[];
}

/**
 * cfn-nag suppression rule interface
 */
interface CfnNagSuppressRule {
  readonly id: string;
  readonly reason: string;
}

/**
 * Serverless Image Handler Construct using AWS Solutions Constructs patterns and AWS CDK
 * @version 5.1.0
 */
export class ServerlessImageHandler extends Construct {
  constructor(scope: Construct, id: string, props: ServerlessImageHandlerProps) {
    super(scope, id);

    try {
      // CFN Conditions
      const enableCorsCondition = new cdk.CfnCondition(this, 'EnableCorsCondition', {
        expression: cdk.Fn.conditionEquals(props.corsEnabledParameter.valueAsString, 'Yes')
      });
      enableCorsCondition.overrideLogicalId('EnableCorsCondition');

      const enableSignatureCondition = new cdk.CfnCondition(this, 'EnableSignatureCondition', {
        expression: cdk.Fn.conditionEquals(props.enableSignatureParameter.valueAsString, 'Yes')
      });
      enableSignatureCondition.overrideLogicalId('EnableSignatureCondition');

      const enableDefaultFallbackImageCondition = new cdk.CfnCondition(this, 'EnableDefaultFallbackImageCondition', {
        expression: cdk.Fn.conditionEquals(props.enableDefaultFallbackImageParameter.valueAsString, 'Yes')
      });
      enableDefaultFallbackImageCondition.overrideLogicalId('EnableDefaultFallbackImageCondition');

      const isOptInRegion = new cdk.CfnCondition(this, 'IsOptInRegion', {
        expression: cdk.Fn.conditionOr(
          cdk.Fn.conditionEquals("af-south-1", cdk.Aws.REGION),
          cdk.Fn.conditionEquals("ap-east-1", cdk.Aws.REGION),
          cdk.Fn.conditionEquals("eu-south-1" , cdk.Aws.REGION),
          cdk.Fn.conditionEquals("me-south-1" , cdk.Aws.REGION)
        )
      });
      isOptInRegion.overrideLogicalId('IsOptInRegion');
      
      const isNotOptInRegion = new cdk.CfnCondition(this, 'IsNotOptInRegion', {
        expression: cdk.Fn.conditionNot(isOptInRegion)
      });
      isNotOptInRegion.overrideLogicalId('IsNotOptInRegion')

      // ImageHandlerFunctionRole
      const imageHandlerFunctionRole = new cdkIam.Role(this, 'ImageHandlerFunctionRole', {
        assumedBy: new cdkIam.ServicePrincipal('lambda.amazonaws.com'),
        path: '/',
        roleName: `${cdk.Aws.STACK_NAME}ImageHandlerFunctionRole-${cdk.Aws.REGION}`
      });
      const cfnImageHandlerFunctionRole = imageHandlerFunctionRole.node.defaultChild as cdkIam.CfnRole;
      this.addCfnNagSuppressRules(cfnImageHandlerFunctionRole, [
        {
          id: 'W28',
          reason: 'Resource name validated and found to pose no risk to updates that require replacement of this resource.'
        }
      ]);
      cfnImageHandlerFunctionRole.overrideLogicalId('ImageHandlerFunctionRole');

      // ImageHandlerPolicy
      const imageHandlerPolicy = new cdkIam.Policy(this, 'ImageHandlerPolicy', {
        policyName: `${cdk.Aws.STACK_NAME}ImageHandlerPolicy`,
        statements: [
          new cdkIam.PolicyStatement({
            actions: [
              'logs:CreateLogStream',
              'logs:CreateLogGroup',
              'logs:PutLogEvents'
            ],
            resources: [
              `arn:${cdk.Aws.PARTITION}:logs:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:log-group:/aws/lambda/*`
            ]
          }),
          new cdkIam.PolicyStatement({
            actions: [
              's3:GetObject',
              's3:PutObject',
              's3:ListBucket'
            ],
            resources: [
              `arn:${cdk.Aws.PARTITION}:s3:::*`
            ]
          }),
          new cdkIam.PolicyStatement({
            actions: [
              'rekognition:DetectFaces',
              'rekognition:DetectModerationLabels'
            ],
            resources: [
              '*'
            ]
          })
        ]
      });
      imageHandlerPolicy.attachToRole(imageHandlerFunctionRole);
      const cfnImageHandlerPolicy = imageHandlerPolicy.node.defaultChild as cdkIam.CfnPolicy;
      this.addCfnNagSuppressRules(cfnImageHandlerPolicy, [
        {
          id: 'W12',
          reason: 'rekognition:DetectFaces requires \'*\' resources.'
        }
      ]);
      cfnImageHandlerPolicy.overrideLogicalId('ImageHandlerPolicy');

      // ImageHandlerFunction
      const imageHandlerFunction = new cdkLambda.Function(this, 'ImageHandlerFunction', {
        description: 'Serverless Image Handler - Function for performing image edits and manipulations.',
        code: new cdkLambda.S3Code(
          cdkS3.Bucket.fromBucketArn(this, 'ImageHandlerLambdaSource', `arn:${cdk.Aws.PARTITION}:s3:::${BUCKET_NAME}-${cdk.Aws.REGION}`),
          `${SOLUTION_NAME}/${VERSION}/image-handler.zip`
        ),
        handler: 'index.handler',
        runtime: cdkLambda.Runtime.NODEJS_12_X,
        timeout: cdk.Duration.seconds(30),
        memorySize: 1024,
        role: imageHandlerFunctionRole,
        environment: {
          AUTO_WEBP: props.autoWebPParameter.valueAsString,
          CORS_ENABLED: props.corsEnabledParameter.valueAsString,
          CORS_ORIGIN: props.corsOriginParameter.valueAsString,
          SOURCE_BUCKETS: props.sourceBucketsParameter.valueAsString,
          REWRITE_MATCH_PATTERN: '',
          REWRITE_SUBSTITUTION: '',
          ENABLE_SIGNATURE: props.enableSignatureParameter.valueAsString,
          SECRETS_MANAGER: props.secretsManagerParameter.valueAsString,
          SECRET_KEY: props.secretsManagerKeyParameter.valueAsString,
          ENABLE_DEFAULT_FALLBACK_IMAGE: props.enableDefaultFallbackImageParameter.valueAsString,
          DEFAULT_FALLBACK_IMAGE_BUCKET: props.fallbackImageS3BucketParameter.valueAsString,
          DEFAULT_FALLBACK_IMAGE_KEY: props.fallbackImageS3KeyParameter.valueAsString
        }
      });
      const cfnImageHandlerFunction = imageHandlerFunction.node.defaultChild as cdkLambda.CfnFunction;
      this.addCfnNagSuppressRules(cfnImageHandlerFunction, [
        {
          id: 'W58',
          reason: 'False alarm: The Lambda function does have the permission to write CloudWatch Logs.'
        }
      ]);
      cfnImageHandlerFunction.overrideLogicalId('ImageHandlerFunction');

      // ImageHandlerLogGroup
      const lambdaFunctionLogs = new cdkLogs.LogGroup(this, 'ImageHandlerLogGroup', {
        logGroupName: `/aws/lambda/${imageHandlerFunction.functionName}`
      });
      const cfnLambdaFunctionLogs = lambdaFunctionLogs.node.defaultChild as cdkLogs.CfnLogGroup;
      cfnLambdaFunctionLogs.retentionInDays = props.logRetentionPeriodParameter.valueAsNumber;
      this.addCfnNagSuppressRules(cfnLambdaFunctionLogs, [
        {
          "id": "W84",
          "reason": "Used to store store function info"
        }
      ]);
      cfnLambdaFunctionLogs.overrideLogicalId('ImageHandlerLogGroup');

      // CloudFrontToApiGatewayToLambda pattern
      const cloudFrontApiGatewayLambda = new CloudFrontToApiGatewayToLambda(this, 'CloudFrontApiGatewayLambda', {
        existingLambdaObj: imageHandlerFunction,
        insertHttpSecurityHeaders: false
      });
      const { apiGatewayLogGroup, apiGateway, cloudFrontWebDistribution } = cloudFrontApiGatewayLambda;

      // ApiLogs
      const cfnApiGatewayLogGroup = apiGatewayLogGroup.node.defaultChild as cdkLogs.CfnLogGroup;
      this.addCfnNagSuppressRules(cfnApiGatewayLogGroup, [
        {
          "id": "W84",
          "reason": "Used to store store api log info, not using kms"
        },
        {
          "id": "W86",
          "reason": "Log retention specified in CloudFromation parameters."
        }
      ]);
      cfnApiGatewayLogGroup.overrideLogicalId('ApiLogs');

      // ImageHandlerApi
      this.removeChildren(apiGateway, [ 'Endpoint', 'UsagePlan', 'Deployment', 'Default', 'DeploymentStage.prod' ]);
      const cfnApiGateway = apiGateway.node.defaultChild as cdkApiGateway.CfnRestApi;
      cfnApiGateway.name = 'ServerlessImageHandler';
      cfnApiGateway.body = apiBody;
      cfnApiGateway.overrideLogicalId('ImageHandlerApi');

      // ImageHandlerPermission
      imageHandlerFunction.addPermission('ImageHandlerPermission', {
        action: 'lambda:InvokeFunction',
        sourceArn: `arn:${cdk.Aws.PARTITION}:execute-api:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:${apiGateway.restApiId}/*/*/*`,
        principal: new cdkIam.ServicePrincipal('apigateway.amazonaws.com')
      });
      (imageHandlerFunction.node.findChild('ImageHandlerPermission') as cdkLambda.CfnPermission).overrideLogicalId('ImageHandlerPermission');

      // ApiLoggingRole
      const cfnApiGatewayLogRole = cloudFrontApiGatewayLambda.apiGatewayCloudWatchRole.node.defaultChild as cdkIam.CfnRole;
      cfnApiGatewayLogRole.overrideLogicalId('ApiLoggingRole');

      // ApiAccountConfig
      const cfnApiGatewayAccount = cloudFrontApiGatewayLambda.node.findChild('LambdaRestApiAccount') as cdkApiGateway.CfnAccount;
      cfnApiGatewayAccount.overrideLogicalId('ApiAccountConfig');

      // ImageHandlerApiDeployment
      const cfnApiGatewayDeployment = new cdkApiGateway.CfnDeployment(this, 'ImageHandlerApiDeployment', {
        restApiId: apiGateway.restApiId,
        stageName: 'image',
        stageDescription: {
          accessLogSetting: {
            destinationArn: cfnApiGatewayLogGroup.attrArn,
            format: '$context.identity.sourceIp $context.identity.caller $context.identity.user [$context.requestTime] "$context.httpMethod $context.resourcePath $context.protocol" $context.status $context.responseLength $context.requestId'
          }
        }
      });
      this.addCfnNagSuppressRules(cfnApiGatewayDeployment, [
        {
          id: 'W68',
          reason: 'The solution does not require the usage plan.'
        }
      ]);
      this.addDependencies(cfnApiGatewayDeployment, [ cfnApiGatewayAccount ]);
      cfnApiGatewayDeployment.overrideLogicalId('ImageHandlerApiDeployment');

      // Logs
      const cloudFrontToApiGateway = cloudFrontApiGatewayLambda.node.findChild('CloudFrontToApiGateway');
      const accessLogBucket = cloudFrontToApiGateway.node.findChild('CloudfrontLoggingBucket') as cdkS3.Bucket;
      const cfnAccessLogBucket = accessLogBucket.node.defaultChild as cdkS3.CfnBucket;
      cfnAccessLogBucket.cfnOptions.condition = isNotOptInRegion;
      this.addCfnNagSuppressRules(cfnAccessLogBucket, [
        {
          "id": "W35",
          "reason": "Used to store access logs for other buckets"
        }
      ]);
      cfnAccessLogBucket.overrideLogicalId('Logs');

      // LogsBucketPolicy
      const accessLogBucketPolicy = accessLogBucket.node.findChild('Policy') as cdkS3.BucketPolicy;
      const cfnAccessLogBucketPolicy = accessLogBucketPolicy.node.defaultChild as cdkS3.CfnBucketPolicy;
      (accessLogBucketPolicy.node.defaultChild as cdkS3.CfnBucketPolicy).cfnOptions.condition = isNotOptInRegion;
      (accessLogBucketPolicy.node.defaultChild as cdkS3.CfnBucketPolicy).overrideLogicalId('LogsBucketPolicy');
      
      //OptInRegionLogBucketPolicy
      const optInRegionPolicyStatement = cfnAccessLogBucketPolicy.policyDocument.toJSON().Statement[0];
      optInRegionPolicyStatement.Resource = "";

      //Choose Log Bucket
      const cloudFrontLogsBucket = accessLogBucket.bucketRegionalDomainName.toString();
      
      
      //ImageHandlerCachePolicy
      const cfnCachePolicy = new cdkCloudFront.CfnCachePolicy(
        this, 
        'CachePolicy', 
        {
          cachePolicyConfig: {
            name: `${cdk.Aws.STACK_NAME}-${cdk.Aws.REGION}-ImageHandlerCachePolicy`,
            defaultTtl: 86400,
            minTtl: 1,
            maxTtl: 31536000,
            parametersInCacheKeyAndForwardedToOrigin: {
              cookiesConfig: {cookieBehavior: "none"},
              enableAcceptEncodingGzip: true,
              headersConfig: {
                headerBehavior: "whitelist", 
                headers:['origin', 'accept']
              },
              queryStringsConfig: {
                queryStringBehavior: "whitelist",
                queryStrings: ["signature"]
              },
            }       
        }
      });
      cfnCachePolicy.overrideLogicalId("ImageHandlerCachePolicy");

      //ImageHandlerOriginRequestPolicy
      const cfnOriginRequestPolicy = new cdkCloudFront.CfnOriginRequestPolicy(
        this, 
        "OriginRequestPolicy",
        {
          originRequestPolicyConfig: { 
            cookiesConfig: {cookieBehavior: "none"},
            headersConfig: {
              headerBehavior: "whitelist",
              headers: ['origin', 'accept']
            },
            name: `${cdk.Aws.STACK_NAME}-${cdk.Aws.REGION}-ImageHandlerOriginRequestPolicy`,
            queryStringsConfig: {
              queryStringBehavior: "whitelist",
              queryStrings: ["signature"]
            },
          }
        });
        cfnOriginRequestPolicy.overrideLogicalId("ImageHandlerOriginRequestPolicy");
 
      // ImageHandlerDistribution
      const cfnCloudFrontDistribution = cloudFrontWebDistribution.node.defaultChild as cdkCloudFront.CfnDistribution;
      cfnCloudFrontDistribution.distributionConfig = {
        origins: [{
          domainName: `${apiGateway.restApiId}.execute-api.${cdk.Aws.REGION}.amazonaws.com`,
          id: apiGateway.restApiId,
          originPath: '/image',
          customOriginConfig: {
            httpsPort: 443,
            originProtocolPolicy: 'https-only',
            originSslProtocols: [ 'TLSv1.1', 'TLSv1.2' ]
          }
        }],
        enabled: true,
        httpVersion: 'http2',
        comment: 'Image handler distribution',
        defaultCacheBehavior: {
          allowedMethods: [ 'GET', 'HEAD' ],
          targetOriginId: apiGateway.restApiId,
          viewerProtocolPolicy: 'https-only',
          cachePolicyId: cfnCachePolicy.ref,
          originRequestPolicyId: cfnOriginRequestPolicy.ref

        },
        customErrorResponses: [
          { errorCode: 500, errorCachingMinTtl: 10 },
          { errorCode: 501, errorCachingMinTtl: 10 },
          { errorCode: 502, errorCachingMinTtl: 10 },
          { errorCode: 503, errorCachingMinTtl: 10 },
          { errorCode: 504, errorCachingMinTtl: 10 }
        ],
        priceClass: 'PriceClass_All',
        logging: {
          includeCookies: false,
          bucket: cloudFrontLogsBucket,
          prefix: 'image-handler-cf-logs/'
        }
      };
      cfnCloudFrontDistribution.overrideLogicalId('ImageHandlerDistribution');

      // CloudFrontToS3 pattern
      const cloudFrontToS3 = new CloudFrontToS3(this, 'CloudFrontToS3', {
        bucketProps: {
          versioned: false,
          websiteIndexDocument: 'index.html',
          websiteErrorDocument: 'index.html',
          serverAccessLogsBucket: undefined,
          accessControl: cdkS3.BucketAccessControl.PRIVATE
        },
        insertHttpSecurityHeaders: false
      });
      this.removeChildren(cloudFrontToS3, [ 'S3LoggingBucket', 'CloudfrontLoggingBucket' ]);

      // SecretsManagerPolicy
      const secretsManagerPolicy = new cdkIam.Policy(this, 'secretsManagerPolicy', {
        statements: [
          new cdkIam.PolicyStatement({
            actions: [
              'secretsmanager:GetSecretValue'
            ],
            resources: [
              `arn:${cdk.Aws.PARTITION}:secretsmanager:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:secret:${props.secretsManagerParameter.valueAsString}*`
            ]
          })
        ]
      });
      secretsManagerPolicy.attachToRole(imageHandlerFunctionRole);
      const cfnSecretsManagerPolicy = secretsManagerPolicy.node.defaultChild as cdkIam.CfnPolicy;
      cfnSecretsManagerPolicy.cfnOptions.condition = enableSignatureCondition;
      cfnSecretsManagerPolicy.overrideLogicalId('SecretsManagerPolicy');
    } catch (error) {
      console.error(error);
    }
  }

  /**
   * Adds cfn-nag suppression rules to the AWS CloudFormation resource metadata.
   * @param {cdk.CfnResource} resource Resource to add cfn-nag suppression rules
   * @param {CfnNagSuppressRule[]} rules Rules to suppress
   */
  addCfnNagSuppressRules(resource: cdk.CfnResource, rules: CfnNagSuppressRule[]) {
    resource.addMetadata('cfn_nag', {
      rules_to_suppress: rules
    });
  }

  /**
   * Adds dependencies to the AWS CloudFormation resource.
   * @param {cdk.CfnResource} resource Resource to add AWS CloudFormation dependencies
   * @param {cdk.CfnResource[]} dependencies Dependencies to be added to the AWS CloudFormation resource
   */
  addDependencies(resource: cdk.CfnResource, dependencies: cdk.CfnResource[]) {
    for (let dependency of dependencies) {
      resource.addDependsOn(dependency);
    }
  }

  /**
   * Removes AWS CDK created children from the AWS CloudFormation resource.
   * @param {cdk.IConstruct} resource Resource to delete children
   * @param {string[]} children The list of children to delete from the resource
   */
  removeChildren(resource: cdk.IConstruct, children: string[]) {
    for (let child of children) {
      resource.node.tryRemoveChild(child);
    }
  }

  /**
   * Removes all dependent children of the resource.
   * @param {cdk.IConstruct} resource Resource to delete all dependent children
   */
  removeAllChildren(resource: cdk.IConstruct) {
    let children = resource.node.children;
    for (let child of children) {
      this.removeAllChildren(child);
      resource.node.tryRemoveChild(child.node.id);
    }
  }
}
