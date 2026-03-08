import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import { Construct } from 'constructs';

export class MedAssistStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ========================================
    // S3 Buckets with AES-256 Encryption
    // ========================================
    
    const documentsBucket = new s3.Bucket(this, 'DocumentsBucket', {
      bucketName: `medassist-documents-${this.account}`,
      encryption: s3.BucketEncryption.S3_MANAGED, // AES-256
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: false,
      lifecycleRules: [
        {
          id: 'DeleteOldSessions',
          expiration: cdk.Duration.days(1), // 24-hour cleanup
          prefix: 'sessions/',
        },
      ],
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
      autoDeleteObjects: true, // For dev/test
    });

    const knowledgeBaseBucket = new s3.Bucket(this, 'KnowledgeBaseBucket', {
      bucketName: `medassist-knowledge-base-${this.account}`,
      encryption: s3.BucketEncryption.S3_MANAGED, // AES-256
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
      autoDeleteObjects: true, // For dev/test
    });

    // ========================================
    // DynamoDB Tables with Encryption
    // ========================================
    
    const sessionTable = new dynamodb.Table(this, 'SessionTable', {
      tableName: 'MedAssist-Sessions',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
    });

    const documentTable = new dynamodb.Table(this, 'DocumentTable', {
      tableName: 'MedAssist-Documents',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
    });

    const embeddingTable = new dynamodb.Table(this, 'EmbeddingTable', {
      tableName: 'MedAssist-Embeddings',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
    });

    const chatHistoryTable = new dynamodb.Table(this, 'ChatHistoryTable', {
      tableName: 'MedAssist-ChatHistory',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      timeToLiveAttribute: 'ttl', // 24-hour TTL
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
    });

    // ========================================
    // IAM Role for Lambda Functions (Least Privilege)
    // ========================================
    
    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Execution role for MedAssist Lambda functions with least privilege',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // S3 permissions
    documentsBucket.grantReadWrite(lambdaRole);
    knowledgeBaseBucket.grantReadWrite(lambdaRole);

    // DynamoDB permissions
    sessionTable.grantReadWriteData(lambdaRole);
    documentTable.grantReadWriteData(lambdaRole);
    embeddingTable.grantReadWriteData(lambdaRole);
    chatHistoryTable.grantReadWriteData(lambdaRole);

    // AWS AI/ML service permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'textract:DetectDocumentText',
        'textract:AnalyzeDocument',
      ],
      resources: ['*'],
    }));

    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'rekognition:DetectText',
        'rekognition:DetectLabels',
      ],
      resources: ['*'],
    }));

    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'comprehendmedical:DetectEntitiesV2',
        'comprehendmedical:InferICD10CM',
        'comprehendmedical:InferRxNorm',
      ],
      resources: ['*'],
    }));

    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
      ],
      resources: [
        `arn:aws:bedrock:${this.region}::foundation-model/*`,
      ],
    }));

    // Lambda invoke permission for UploadLambda to invoke ExtractionLambda
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['lambda:InvokeFunction'],
      resources: [`arn:aws:lambda:${this.region}:${this.account}:function:MedAssist-Extraction`],
    }));

    // ========================================
    // Lambda Functions
    // ========================================
    
    const uploadLambda = new lambda.Function(this, 'UploadLambda', {
      functionName: 'MedAssist-Upload',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'upload.handler',
      code: lambda.Code.fromAsset('../lambda/upload'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        DOCUMENTS_BUCKET: documentsBucket.bucketName,
        SESSION_TABLE: sessionTable.tableName,
        DOCUMENT_TABLE: documentTable.tableName,
        EXTRACTION_LAMBDA: 'MedAssist-Extraction',
      },
    });

    const extractionLambda = new lambda.Function(this, 'ExtractionLambda', {
      functionName: 'MedAssist-Extraction',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'extraction.handler',
      code: lambda.Code.fromAsset('../lambda/extraction'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(300), // 5 minutes for document processing
      memorySize: 1024,
      environment: {
        DOCUMENTS_BUCKET: documentsBucket.bucketName,
        DOCUMENT_TABLE: documentTable.tableName,
      },
    });

    const embeddingLambda = new lambda.Function(this, 'EmbeddingLambda', {
      functionName: 'MedAssist-Embedding',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'embedding.handler',
      code: lambda.Code.fromAsset('../lambda/embedding'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(300),
      memorySize: 2048,
      environment: {
        EMBEDDINGS_TABLE: embeddingTable.tableName,
        DOCUMENT_TABLE: documentTable.tableName,
        KNOWLEDGE_BASE_BUCKET: knowledgeBaseBucket.bucketName,
      },
    });

    const ragLambda = new lambda.Function(this, 'RAGLambda', {
      functionName: 'MedAssist-RAG',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'rag.handler',
      code: lambda.Code.fromAsset('../lambda/rag', {
        exclude: [
          '*.zip',
          '*_backup.py',
          '*_previous.py',
          '*_simplified.py',
          '*_ultra_simple.py',
          'test_*.py',
          '__pycache__',
          'lambda_build',
          'package',
          'simplified_build',
          'ultra_simple_build',
        ],
      }),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(90),
      memorySize: 2048,
      environment: {
        DOCUMENT_TABLE: documentTable.tableName,
        EMBEDDINGS_TABLE: embeddingTable.tableName,
        KNOWLEDGE_BASE_BUCKET: knowledgeBaseBucket.bucketName,
        CHAT_HISTORY_TABLE: chatHistoryTable.tableName,
      },
    });

    const dashboardLambda = new lambda.Function(this, 'DashboardLambda', {
      functionName: 'MedAssist-Dashboard',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'dashboard.handler',
      code: lambda.Code.fromAsset('../lambda/dashboard'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
      environment: {
        EMBEDDINGS_TABLE: embeddingTable.tableName,
        DOCUMENT_TABLE: documentTable.tableName,
      },
    });

    const exportLambda = new lambda.Function(this, 'ExportLambda', {
      functionName: 'MedAssist-Export',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'export.handler',
      code: lambda.Code.fromAsset('../lambda/export'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(60),
      memorySize: 1024,
      environment: {
        DOCUMENTS_BUCKET: documentsBucket.bucketName,
        SESSION_TABLE: sessionTable.tableName,
      },
    });

    const cleanupLambda = new lambda.Function(this, 'CleanupLambda', {
      functionName: 'MedAssist-Cleanup',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'cleanup.handler',
      code: lambda.Code.fromAsset('../lambda/cleanup'),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(60),
      memorySize: 512,
      environment: {
        DOCUMENTS_BUCKET: documentsBucket.bucketName,
        SESSION_TABLE: sessionTable.tableName,
        DOCUMENT_TABLE: documentTable.tableName,
        EMBEDDING_TABLE: embeddingTable.tableName,
      },
    });

    // Update UploadLambda environment with ExtractionLambda ARN
    uploadLambda.addEnvironment('EXTRACTION_LAMBDA_ARN', extractionLambda.functionArn);

    // ========================================
    // EventBridge Rule for Session Cleanup (runs every 24 hours)
    // ========================================
    
    const cleanupRule = new events.Rule(this, 'SessionCleanupRule', {
      ruleName: 'MedAssist-SessionCleanup',
      description: 'Triggers session cleanup Lambda every 24 hours',
      schedule: events.Schedule.rate(cdk.Duration.hours(24)),
    });
    
    cleanupRule.addTarget(new targets.LambdaFunction(cleanupLambda));

    // ========================================
    // API Gateway with TLS 1.2+, CloudWatch Logging, and CORS
    // ========================================
    
    const api = new apigateway.RestApi(this, 'MedAssistAPI', {
      restApiName: 'MedAssist API',
      description: 'API for MedAssist AI System',
      deployOptions: {
        stageName: 'prod',
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: ['*'],
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['*'],
        allowCredentials: false,
        statusCode: 200,
      },
      endpointConfiguration: {
        types: [apigateway.EndpointType.REGIONAL],
      },
      policy: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            principals: [new iam.AnyPrincipal()],
            actions: ['execute-api:Invoke'],
            resources: ['execute-api:/*'],
            conditions: {
              StringEquals: {
                'aws:SecureTransport': 'true', // Enforce TLS
              },
            },
          }),
        ],
      }),
    });

    // API Endpoints with Lambda proxy integration (Lambda returns CORS headers)
    // CORS is handled by defaultCorsPreflightOptions at API level
    const uploadResource = api.root.addResource('upload');
    uploadResource.addMethod('POST', new apigateway.LambdaIntegration(uploadLambda, {
      proxy: true,
    }));

    const chatResource = api.root.addResource('chat');
    chatResource.addMethod('POST', new apigateway.LambdaIntegration(ragLambda, {
      proxy: true,
    }));

    const dashboardResource = api.root.addResource('dashboard');
    dashboardResource.addMethod('GET', new apigateway.LambdaIntegration(dashboardLambda, {
      proxy: true,
    }));

    const exportResource = api.root.addResource('export');
    exportResource.addMethod('POST', new apigateway.LambdaIntegration(exportLambda, {
      proxy: true,
    }));

    // ========================================
    // Outputs
    // ========================================
    
    new cdk.CfnOutput(this, 'APIEndpoint', {
      value: api.url,
      description: 'API Gateway endpoint URL',
      exportName: 'MedAssistAPIEndpoint',
    });

    new cdk.CfnOutput(this, 'DocumentsBucketName', {
      value: documentsBucket.bucketName,
      description: 'S3 bucket for documents',
      exportName: 'MedAssistDocumentsBucket',
    });

    new cdk.CfnOutput(this, 'SessionTableName', {
      value: sessionTable.tableName,
      description: 'DynamoDB table for sessions',
      exportName: 'MedAssistSessionTable',
    });
  }
}
